#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF领取计算器
基于CPF Life等退休金领取方案
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import math


@dataclass
class CPFPayoutResult:
    """CPF领取结果"""
    monthly_payment: float          # 月领取金额
    total_payments: float          # 总领取金额
    total_interest: float          # 总利息收入
    payout_years: int              # 领取年限
    final_balance: float           # 最终余额
    payout_schedule: List[Dict]    # 领取计划明细


# ======= 工具/数学函数 =======
def annuity_payment_from_present_value(PV: float, annual_rate: float, years: float, payments_per_year: int = 12) -> float:
    """
    等额年金（立即年金）公式：
    monthly_rate = annual_rate / payments_per_year
    n = years * payments_per_year
    PMT = PV * monthly_rate / (1 - (1 + monthly_rate) ** -n)
    返回每期支付（同货币周期）
    """
    m = payments_per_year
    r_m = annual_rate / m
    n = int(years * m)
    if abs(r_m) < 1e-12:
        return PV / n
    return PV * (r_m / (1 - (1 + r_m) ** (-n)))


def growing_annuity_payment_from_present_value(PV: float, annual_rate: float, years: float, growth_rate: float, payments_per_year: int = 12) -> float:
    """
    递增年金（每期按growth_rate增长）近似公式（monthly compounding）
    采用连续逼近/离散公式。若 r == g，退化为 PV/n。
    """
    m = payments_per_year
    r = annual_rate / m
    g = growth_rate / m
    n = int(years * m)
    if abs(r - g) < 1e-12:
        return PV / n
    # 等比求和变形（离散）
    factor = (r - g) / (1 - ((1 + g) / (1 + r)) ** n)
    return PV * factor


def lookup_official_payout(official_table: Dict, RA65: float, plan: str) -> float:
    """
    从官方表中查找养老金金额
    如果没有精确匹配，使用线性插值
    """
    if not official_table:
        return 0.0
    
    # 找到最接近的RA金额
    closest_amounts = sorted(official_table.keys())
    
    if RA65 <= closest_amounts[0]:
        return official_table[closest_amounts[0]]
    elif RA65 >= closest_amounts[-1]:
        return official_table[closest_amounts[-1]]
    
    # 线性插值
    for i in range(len(closest_amounts) - 1):
        if closest_amounts[i] <= RA65 <= closest_amounts[i + 1]:
            x1, x2 = closest_amounts[i], closest_amounts[i + 1]
            y1, y2 = official_table[x1], official_table[x2]
            return y1 + (y2 - y1) * (RA65 - x1) / (x2 - x1)
    
    return 0.0


class SingaporeCPFPayoutCalculator:
    """新加坡CPF领取计算器"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

    def compute_cpf_life_payout(self,
                               RA65: float,
                               plan: str = "standard",
                               start_age: int = 65,
                               nominal_discount_rate: float = 0.035,
                               expected_life_years: float = 20.0,
                               escalating_rate: float = 0.02,
                               payments_per_year: int = 12,
                               official_table_lookup: Optional[Dict] = None) -> Dict:
        """
        计算CPF Life的月领（优先级：官方表 > 公式）
        
        返回：{
           "monthly_payout": float,   # 第一个月支付金额（若escalating则为第1个月）
           "monthly_schedule": [ ... ] # 可选：整个领取期每月金额（长度 = (end_age-start_age)*12）
        }

        参数说明：
        - RA65: 65岁时RA余额（货币）
        - plan: 'standard' / 'escalating' / 'basic'
        - nominal_discount_rate: 用于折现/计息的年利率（示例 3.5%）
        - expected_life_years: 若使用简化年金法，作为"精算期限"的近似（例 20~30 年）
        - escalating_rate: 对 'escalating' 计划，年增率（例 0.02 即2%）
        - official_table_lookup: 如果可用，提供一个函数或字典 (RA_amount -> monthly)，优先使用
        """
        
        # 优先：如果有官方查表函数/字典，直接返回查表值
        if official_table_lookup is not None:
            # 如果是字典可以直接近似查找或线性内插
            monthly = lookup_official_payout(official_table_lookup, RA65, plan)
            # 若escalating表为年化基础，则转换成月度序列
            if plan == "escalating":
                months = int(expected_life_years * payments_per_year)
                monthly_schedule = [monthly * ((1 + escalating_rate) ** (i / payments_per_year)) for i in range(months)]
                return {"monthly_payout": monthly_schedule[0], "monthly_schedule": monthly_schedule}
            else:
                months = int(expected_life_years * payments_per_year)
                return {"monthly_payout": monthly, "monthly_schedule": [monthly] * months}

        # 否则使用简化年金公式近似
        # 定义用于年金计算的"年数"
        # CPF LIFE 是终身年金；没有寿命表时用 expected_life_years 近似
        years = expected_life_years  # 例如 20、25、30，根据你要模拟的保守/乐观场景调整

        if plan == "standard":
            # 标准计划：等额每月，直到预计寿命（简化）
            monthly = annuity_payment_from_present_value(RA65, nominal_discount_rate, years, payments_per_year)
            schedule = [monthly] * int(years * payments_per_year)
            return {"monthly_payout": monthly, "monthly_schedule": schedule}

        elif plan == "escalating":
            # 递增计划：第一年较低，但每年按 escalating_rate 增
            # 计算等价现值下的初始月领（growing annuity）
            monthly = growing_annuity_payment_from_present_value(RA65, nominal_discount_rate, years, escalating_rate, payments_per_year)
            # 构建月序列（每年以g增长，按月插值）
            schedule = []
            for m in range(int(years * payments_per_year)):
                # 用年级增长近似（每12个月增长一次）
                year_index = m // payments_per_year
                value = monthly * ((1 + escalating_rate) ** year_index)
                schedule.append(value)
            return {"monthly_payout": schedule[0], "monthly_schedule": schedule}

        elif plan == "basic":
            # Basic：通常给较低固定月领（保守），我们可以用一个更保守的年数（更长期限导致月领更低）
            conservative_years = years + 5  # 举例更保守
            monthly = annuity_payment_from_present_value(RA65, nominal_discount_rate, conservative_years, payments_per_year)
            schedule = [monthly] * int(conservative_years * payments_per_year)
            return {"monthly_payout": monthly, "monthly_schedule": schedule}

        else:
            raise ValueError("Unknown CPF LIFE plan")

    def build_RA_at_65(self, OA: float, SA: float, MA: float, transfer_rules: Callable, rate_sa_ra: float = 0.04, years_55_to_65: int = 10) -> float:
        """
        把 55→65 的转入/计息和 65 岁RA计算放到一起
        
        transfer_rules: 函数或参数，决定 55岁时如何从 OA/SA 转入 RA（例如先把SA都转，然后OA补齐，目标=Full Retirement Sum）
        返回 RA65（float）和修改后的账户OA/SA/MA（用于后续若需保留OA/MA）
        """
        # 1) 执行55岁时的转移规则，假设传入的OA/SA为55岁时的值
        RA = transfer_rules(OA, SA)
        # 2) 55->65期间计息（RA计息通常 ~4%）
        for _ in range(years_55_to_65):
            RA *= (1 + rate_sa_ra)
        # 3) OA/SA/MA在55->65期间也会计息（若你需要保留OA/MA）
        #    这里假定 caller 已经对OA/SA/MA做了相应计息或需要额外处理
        return RA

    def compute_payout_schedule(self,
                              principal: float,
                              annual_nominal_rate: float,
                              annual_inflation_rate: float,
                              years: int = 30,
                              freq: int = 12,
                              scheme: str = "level",
                              rounding: bool = True) -> List[Dict]:
        """
        计算CPF领取计划
        
        Args:
            principal: 本金（退休时CPF余额）
            annual_nominal_rate: 年名义利率
            annual_inflation_rate: 年通胀率
            years: 领取年限
            freq: 支付频率（月=12）
            scheme: 领取方案 ("level" 或 "growing")
            rounding: 是否四舍五入到分
            
        Returns:
            领取计划明细列表
        """
        r = annual_nominal_rate / freq          # 月利率
        g = annual_inflation_rate / freq        # 月增长率（用于 growing）
        n = years * freq                        # 总期数（月份）

        # 1) 计算每月支付额（首月，如果是 growing 则为首月金额）
        if scheme == "level":
            if r == 0:
                monthly_payment = principal / n
            else:
                monthly_payment = principal * (r / (1 - (1 + r) ** (-n)))

        elif scheme == "growing":
            # 要求 r != g，若非常接近需要用极限近似
            if abs(r - g) < 1e-12:
                # 当 r ≈ g 时，PMT0 ≈ PV / n（近似）
                monthly_payment = principal / n
            else:
                monthly_payment = principal * ((r - g) / (1 - ((1 + g) / (1 + r)) ** n))
        else:
            raise ValueError("scheme must be 'level' or 'growing'")

        # 可选四舍五入到分
        def round_money(x):
            return round(x + 1e-12, 2) if rounding else x

        monthly_payment = round_money(monthly_payment)

        # 2) 模拟逐月发放（带利息复利）
        balance = principal
        schedule = []
        for m in range(1, n + 1):
            # 计算当月利息
            interest = balance * r

            # 本期支付额
            if scheme == "level":
                payment = monthly_payment
            else:  # growing
                # 如果要按月增长：payment_m = monthly_payment * (1+g)^(m-1)
                payment = monthly_payment * ((1 + g) ** (m - 1))

            # 防止最后一期超额提现：如果 payment > balance + interest，则把 payment 调整为全部余额
            if payment > balance + interest:
                payment = balance + interest

            # 更新余额：先加利息，再减去本期支付
            balance = balance + interest - payment

            # 四舍五入显示
            interest_r = round_money(interest)
            payment_r = round_money(payment)
            balance_r = round_money(balance)

            schedule.append({
                "month": m,
                "payment": payment_r,
                "interest": interest_r,
                "balance_after": balance_r
            })

            # 若余额接近 0，跳出循环
            if balance <= 1e-6:
                break

        return schedule

    def calculate_cpf_life_payout(self,
                                ra_balance: float,
                                sa_balance: float = 0,
                                annual_nominal_rate: float = 0.04,
                                annual_inflation_rate: float = 0.02,
                                payout_years: int = 30,
                                scheme: str = "level") -> CPFPayoutResult:
        """
        计算CPF Life退休金领取（使用新的计算逻辑）
        
        Args:
            ra_balance: RA账户余额
            sa_balance: SA账户余额（如果有）
            annual_nominal_rate: 年名义利率
            annual_inflation_rate: 年通胀率
            payout_years: 领取年限
            scheme: 领取方案 ("level" 对应 "standard", "growing" 对应 "escalating")
            
        Returns:
            CPF领取结果
        """
        # 合并RA和SA余额作为本金
        total_principal = ra_balance + sa_balance
        
        if total_principal <= 0:
            return CPFPayoutResult(
                monthly_payment=0,
                total_payments=0,
                total_interest=0,
                payout_years=payout_years,
                final_balance=0,
                payout_schedule=[]
            )

        # 映射scheme到plan
        plan_mapping = {
            "level": "standard",
            "growing": "escalating"
        }
        plan = plan_mapping.get(scheme, "standard")

        # 使用新的CPF Life计算逻辑
        payout_result = self.compute_cpf_life_payout(
            RA65=total_principal,
            plan=plan,
            start_age=65,
            nominal_discount_rate=annual_nominal_rate,
            expected_life_years=payout_years,
            escalating_rate=annual_inflation_rate,
            payments_per_year=12,
            official_table_lookup=None
        )

        monthly_payment = payout_result['monthly_payout']
        monthly_schedule = payout_result['monthly_schedule']
        
        # 计算总支付和利息
        total_payments = sum(monthly_schedule)
        total_interest = total_payments - total_principal
        
        # 构建详细的schedule
        detailed_schedule = []
        balance = total_principal
        monthly_rate = annual_nominal_rate / 12
        
        for i, payment in enumerate(monthly_schedule):
            interest = balance * monthly_rate
            balance = balance + interest - payment
            if balance <= 0:
                balance = 0
                payment = balance + interest  # 最后一期支付全部余额
            
            detailed_schedule.append({
                "month": i + 1,
                "payment": payment,
                "interest": interest,
                "balance_after": balance
            })
            
            if balance <= 0:
                break

        return CPFPayoutResult(
            monthly_payment=monthly_payment,
            total_payments=total_payments,
            total_interest=total_interest,
            payout_years=payout_years,
            final_balance=balance,
            payout_schedule=detailed_schedule
        )

    def calculate_enhanced_retirement_summary(self,
                                            ra_balance: float,
                                            sa_balance: float = 0,
                                            oa_balance: float = 0,
                                            ma_balance: float = 0) -> Dict:
        """
        计算增强版退休金汇总
        
        Args:
            ra_balance: RA账户余额
            sa_balance: SA账户余额
            oa_balance: OA账户余额
            ma_balance: MA账户余额
            
        Returns:
            退休金汇总信息
        """
        total_cpf_balance = ra_balance + sa_balance + oa_balance + ma_balance
        
        # 计算不同方案的月退休金
        level_payout = self.calculate_cpf_life_payout(
            ra_balance, sa_balance, scheme="level"
        )
        
        growing_payout = self.calculate_cpf_life_payout(
            ra_balance, sa_balance, scheme="growing"
        )

        return {
            'total_cpf_balance': total_cpf_balance,
            'account_breakdown': {
                'ra_balance': ra_balance,
                'sa_balance': sa_balance,
                'oa_balance': oa_balance,
                'ma_balance': ma_balance
            },
            'retirement_income': {
                'level_monthly': level_payout.monthly_payment,
                'level_total': level_payout.total_payments,
                'growing_monthly': growing_payout.monthly_payment,
                'growing_total': growing_payout.total_payments
            },
            'payout_options': {
                'level_scheme': {
                    'monthly_payment': level_payout.monthly_payment,
                    'total_payments': level_payout.total_payments,
                    'total_interest': level_payout.total_interest,
                    'payout_years': level_payout.payout_years
                },
                'growing_scheme': {
                    'monthly_payment': growing_payout.monthly_payment,
                    'total_payments': growing_payout.total_payments,
                    'total_interest': growing_payout.total_interest,
                    'payout_years': growing_payout.payout_years
                }
            }
        }

    def cpf_payout(self, RA65: float, lifespan: int = 90, start_age: int = 65) -> Dict:
        """
        简化的CPF养老金计算函数
        假设在指定年龄去世，不留余额
        
        Args:
            RA65: 65岁时的RA账户余额
            lifespan: 预期寿命（默认90岁）
            start_age: 开始领取年龄（默认65岁）
            
        Returns:
            包含养老金信息的字典
        """
        years = lifespan - start_age
        months = years * 12

        # 每月养老金，确保去世时余额=0
        monthly_payout = RA65 / months

        # 累计领取
        total_payout = monthly_payout * months

        return {
            "RA65": RA65,
            "monthly_payout": monthly_payout,
            "total_payout": total_payout,
            "end_balance": 0,
            "payout_years": years,
            "payout_months": months,
            "lifespan": lifespan,
            "start_age": start_age
        }

    def cpf_payout_with_death_scenario(self, RA65: float, lifespan: int = 90, start_age: int = 65) -> Dict:
        """
        考虑去世情况的CPF养老金计算
        包含不同寿命假设的对比分析
        
        Args:
            RA65: 65岁时的RA账户余额
            lifespan: 预期寿命（默认90岁）
            start_age: 开始领取年龄（默认65岁）
            
        Returns:
            包含不同寿命假设的养老金对比分析
        """
        # 不同寿命假设
        death_scenarios = [75, 80, 85, 90, 95, 100]
        
        results = {}
        
        for death_age in death_scenarios:
            if death_age <= start_age:
                continue
                
            years = death_age - start_age
            months = years * 12
            
            # 每月养老金
            monthly_payout = RA65 / months
            
            # 累计领取
            total_payout = monthly_payout * months
            
            results[f"death_at_{death_age}"] = {
                "death_age": death_age,
                "payout_years": years,
                "payout_months": months,
                "monthly_payout": monthly_payout,
                "total_payout": total_payout,
                "end_balance": 0,
                "payout_efficiency": total_payout / RA65 if RA65 > 0 else 0  # 领取效率
            }
        
        # 主要结果（基于输入的lifespan）
        main_result = self.cpf_payout(RA65, lifespan, start_age)
        
        return {
            "main_scenario": main_result,
            "death_scenarios": results,
            "summary": {
                "ra65_balance": RA65,
                "start_age": start_age,
                "assumed_lifespan": lifespan,
                "scenarios_analyzed": len(results),
                "monthly_range": {
                    "min": min(scenario["monthly_payout"] for scenario in results.values()),
                    "max": max(scenario["monthly_payout"] for scenario in results.values())
                },
                "total_range": {
                    "min": min(scenario["total_payout"] for scenario in results.values()),
                    "max": max(scenario["total_payout"] for scenario in results.values())
                }
            }
        }

    def cpf_payout_death_at_90(self, RA65: float, start_age: int = 65) -> Dict:
        """
        专门计算90岁去世不留余额的CPF养老金情况
        
        Args:
            RA65: 65岁时的RA账户余额
            start_age: 开始领取年龄（默认65岁）
            
        Returns:
            90岁去世场景的养老金信息
        """
        lifespan = 90
        years = lifespan - start_age
        months = years * 12

        # 每月养老金，确保90岁时余额=0
        monthly_payout = RA65 / months

        # 累计领取
        total_payout = monthly_payout * months

        return {
            "scenario": "90岁去世不留余额",
            "RA65": RA65,
            "monthly_payout": monthly_payout,
            "total_payout": total_payout,
            "end_balance": 0,
            "payout_years": years,
            "payout_months": months,
            "lifespan": lifespan,
            "start_age": start_age,
            "description": f"从{start_age}岁开始每月领取${monthly_payout:,.2f}，共领取{years}年，90岁去世时余额为0"
        }

    def calculate_comprehensive_payout_analysis(self, RA65: float, start_age: int = 65) -> Dict:
        """
        综合养老金分析，包含90岁去世场景和其他对比情况
        
        Args:
            RA65: 65岁时的RA账户余额
            start_age: 开始领取年龄（默认65岁）
            
        Returns:
            综合养老金分析结果
        """
        # 90岁去世场景（主要场景）
        death_at_90 = self.cpf_payout_death_at_90(RA65, start_age)
        
        # 其他寿命假设对比
        other_scenarios = self.cpf_payout_with_death_scenario(RA65, lifespan=90, start_age=start_age)
        
        # 计算一些关键指标
        monthly_90 = death_at_90['monthly_payout']
        total_90 = death_at_90['total_payout']
        
        return {
            "main_scenario_90_death": death_at_90,
            "comparison_scenarios": other_scenarios['death_scenarios'],
            "summary": {
                "ra65_balance": RA65,
                "start_age": start_age,
                "death_at_90": {
                    "monthly_payout": monthly_90,
                    "total_payout": total_90,
                    "payout_years": death_at_90['payout_years'],
                    "description": death_at_90['description']
                },
                "key_insights": {
                    "monthly_income_90": f"${monthly_90:,.2f}",
                    "total_received_90": f"${total_90:,.2f}",
                    "years_of_payout": f"{death_at_90['payout_years']}年",
                    "balance_at_death": "$0.00"
                }
            }
        }

    def get_cpf_life_info(self) -> Dict:
        """获取CPF Life信息"""
        return {
            'scheme_types': ['level', 'growing'],
            'default_nominal_rate': 0.04,  # 4%年利率
            'default_inflation_rate': 0.02,  # 2%通胀率
            'default_payout_years': 30,
            'description': {
                'level': '固定金额领取：每月领取相同金额',
                'growing': '递增金额领取：每月金额按通胀率递增'
            },
            'death_at_90_scenario': {
                'description': '假设90岁去世，不留余额的养老金计算',
                'method': '简单平均分配：RA余额 ÷ 领取月数',
                'advantage': '确保资金完全使用，不留遗产',
                'disadvantage': '未考虑利息增长和通胀'
            }
        }