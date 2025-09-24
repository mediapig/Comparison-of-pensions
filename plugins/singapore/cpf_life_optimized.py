#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF LIFE优化计算器
基于官方CPF LIFE机制，提供精确的退休金领取和余额计算
"""

import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
import math
from functools import lru_cache


@dataclass
class CPFLifeResult:
    """CPF LIFE计算结果"""
    monthly_schedule: List[float]      # 逐月领取金额
    bequest_curve: List[float]         # 遗赠曲线
    snapshots: Dict[str, Optional[float]]  # 关键年龄快照
    total_payout: float                # 总领取金额
    final_balance: float               # 最终余额
    plan_type: str                     # 计划类型


# ===== 参数建议 =====
# 利率：用名义年利率，月份化；可按需要校准到官方估算器
R_RA = 0.04        # RA/保底利率（含地板 4% 的近似）
R_PREM = 0.04      # CPF LIFE premium 的计息近似（官方称最高至约6%风险无关利率，保守取4%）
G_ESC = 0.02       # Escalating 年增幅，若选该计划
P_BASIC = 0.15     # Basic 计划：初始 premium 比例（10–20% 可调）


class CPFLifeOptimizedCalculator:
    """新加坡CPF LIFE优化计算器"""
    
    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'
        
        # 默认参数
        self.r_ra = R_RA
        self.r_prem = R_PREM
        self.g_esc = G_ESC
        self.p_basic = P_BASIC
    
    def set_parameters(self, r_ra: float = None, r_prem: float = None, 
                      g_esc: float = None, p_basic: float = None):
        """设置计算参数"""
        if r_ra is not None:
            self.r_ra = r_ra
        if r_prem is not None:
            self.r_prem = r_prem
        if g_esc is not None:
            self.g_esc = g_esc
        if p_basic is not None:
            self.p_basic = p_basic
    
    @lru_cache(maxsize=256)
    def annuity_pmt(self, PV: float, annual_rate: float, years: float, m: int = 12) -> float:
        """
        等额年金支付额计算（现值已知）
        
        Args:
            PV: 现值
            annual_rate: 年利率
            years: 年数
            m: 每年支付次数（默认12，即月付）
            
        Returns:
            每期支付金额
        """
        r = annual_rate / m
        n = int(years * m)
        if n <= 0:
            return 0.0
        
        if abs(r) < 1e-12:
            return PV / n
        
        return PV * (r / (1 - (1 + r) ** (-n)))
    
    @lru_cache(maxsize=256)
    def growing_annuity_pmt(self, PV: float, rate: float, years: float, 
                           growth: float, m: int = 12) -> float:
        """
        递增年金支付额计算（现值已知）
        
        Args:
            PV: 现值
            rate: 年利率
            years: 年数
            growth: 年增长率
            m: 每年支付次数（默认12，即月付）
            
        Returns:
            首期支付金额
        """
        r = rate / m
        g = growth / m
        n = int(years * m)
        if n <= 0:
            return 0.0
        
        if abs(r - g) < 1e-12:  # 近似退化
            return PV / n
        
        return PV * ((r - g) / (1 - ((1 + g) / (1 + r)) ** n))
    
    def cpf_life_simulate(self, RA65: float, plan: str = "standard", 
                        start_age: int = 65, horizon_age: int = 100) -> CPFLifeResult:
        """
        CPF LIFE模拟计算 - 按照优化算法实现
        
        返回：
          schedule: 逐月月领列表
          bequest_at_age(age): 在某年龄身故的遗赠金额（premium余额 + RA余额 + 其他未用CPF）
          snapshots: 关键年龄的余额与遗赠
        
        Args:
            RA65: 65岁时RA余额
            plan: 计划类型 ("standard", "escalating", "basic")
            start_age: 开始年龄（默认65岁）
            horizon_age: 终止年龄（默认100岁）
            
        Returns:
            CPFLifeResult: 包含月领取计划、遗赠曲线和快照的结果
        """
        months = int((horizon_age - start_age) * 12)
        
        # --- 初始分桶 ---
        if plan in ("standard", "escalating"):
            premium = RA65                # 全额进年金池
            ra = 0.0
        elif plan == "basic":
            premium = RA65 * self.p_basic      # 只扣 10–20%
            ra = RA65 - premium           # 大头留在 RA 里先发
        else:
            raise ValueError(f"Unknown plan: {plan}")
        
        # --- 计算目标月领曲线（先定"应发金额"，再逐月结转两桶）---
        if plan == "standard":
            # 等额年金：用 premium 为现值、R_PREM 为贴现、长寿期限为（horizon_age - start_age）
            m0 = self.annuity_pmt(PV=premium, annual_rate=self.r_prem, 
                                years=(horizon_age - start_age))
            desired_payout = [m0] * months
            
        elif plan == "escalating":
            # 递增年金：按 G_ESC 每年递增（第1个月为 m0），总现值= premium
            m0 = self.growing_annuity_pmt(PV=premium, rate=self.r_prem, 
                                        years=(horizon_age - start_age), 
                                        growth=self.g_esc)
            desired_payout = [m0 * ((1 + self.g_esc) ** (i // 12)) for i in range(months)]
            
        elif plan == "basic":
            # 阶段1：65→90 岁，先用 RA 发放，目标是 ~90 岁前后把 RA 用尽
            years1 = max(0, 90 - start_age)
            months1 = int(years1 * 12)
            m1 = self.annuity_pmt(PV=ra, annual_rate=self.r_ra, years=years1) if months1 > 0 else 0.0
            
            # 阶段2：90 岁后（若需要），从 premium 按等额年金继续发放至 horizon
            years2 = max(0, horizon_age - 90)
            months2 = int(years2 * 12)
            
            desired_payout = ["PHASE1"] * months1 + ["PHASE2"] * months2
        
        # --- 逐月滚存两个"资金桶"，并计算遗赠曲线 ---
        schedule, bequest_curve = [], []
        m2 = None  # 阶段2的月领金额
        
        for i in range(months):
            # 月初计息
            premium *= (1 + self.r_prem / 12)
            ra *= (1 + self.r_ra / 12)
            
            # Basic 计划的两阶段处理
            if plan == "basic":
                age = start_age + i / 12
                if desired_payout[i] == "PHASE1":
                    payout = m1
                    # 优先从 RA 扣
                    take = min(ra, payout)
                    ra -= take
                    # 若 RA 不足，差额由 premium 补（极端情形）
                    if take < payout:
                        premium -= (payout - take)
                else:
                    # 到了90岁：先确定阶段2月领（用此刻 premium 余额为现值）
                    if desired_payout[i] == "PHASE2":
                        # 首次进入PHASE2时求 m2
                        if m2 is None:
                            years2_left = horizon_age - max(90, age)
                            m2 = self.annuity_pmt(PV=premium, annual_rate=self.r_prem, 
                                                years=years2_left)
                        payout = m2
                        premium -= payout
            else:
                # standard / escalating：统一从 premium 桶扣
                payout = desired_payout[i]
                premium -= payout
            
            schedule.append(max(payout, 0.0))
            # 遗赠定义：当期死亡可留给家属的 = max(premium,0) + max(ra,0) + 其他未用CPF余额
            bequest_curve.append(max(premium, 0.0) + max(ra, 0.0))
        
        # 快照
        snapshots = {
            "age_70": bequest_curve[min(len(bequest_curve) - 1, (70 - start_age) * 12)] 
                     if start_age <= 70 < horizon_age else None,
            "age_80": bequest_curve[min(len(bequest_curve) - 1, (80 - start_age) * 12)] 
                     if start_age <= 80 < horizon_age else None,
            "age_90": bequest_curve[min(len(bequest_curve) - 1, (90 - start_age) * 12)] 
                     if start_age <= 90 < horizon_age else None,
        }
        
        return CPFLifeResult(
            monthly_schedule=schedule,
            bequest_curve=bequest_curve,
            snapshots=snapshots,
            total_payout=sum(schedule),
            final_balance=max(premium, 0.0) + max(ra, 0.0),
            plan_type=plan
        )
    
    def compare_plans(self, RA65: float, start_age: int = 65, 
                     horizon_age: int = 100) -> Dict[str, CPFLifeResult]:
        """
        比较不同CPF LIFE计划
        
        Args:
            RA65: 65岁时RA余额
            start_age: 开始年龄
            horizon_age: 终止年龄
            
        Returns:
            包含所有计划结果的字典
        """
        plans = ["standard", "escalating", "basic"]
        results = {}
        
        for plan in plans:
            results[plan] = self.cpf_life_simulate(RA65, plan, start_age, horizon_age)
        
        return results
    
    def analyze_bequest_scenarios(self, RA65: float, plan: str = "standard",
                                death_ages: List[int] = None) -> Dict:
        """
        分析不同死亡年龄的遗赠情况
        
        Args:
            RA65: 65岁时RA余额
            plan: 计划类型
            death_ages: 死亡年龄列表
            
        Returns:
            遗赠分析结果
        """
        if death_ages is None:
            death_ages = [70, 75, 80, 85, 90, 95, 100]
        
        # 计算到最大年龄的完整结果
        max_age = max(death_ages)
        result = self.cpf_life_simulate(RA65, plan, 65, max_age)
        
        bequest_analysis = {}
        for death_age in death_ages:
            if death_age >= 65:
                month_index = (death_age - 65) * 12
                if month_index < len(result.bequest_curve):
                    bequest_analysis[death_age] = {
                        'bequest_amount': result.bequest_curve[month_index],
                        'total_received': sum(result.monthly_schedule[:month_index + 1]),
                        'months_received': month_index + 1,
                        'years_received': (month_index + 1) / 12
                    }
        
        return {
            'plan': plan,
            'ra65_balance': RA65,
            'bequest_scenarios': bequest_analysis,
            'summary': {
                'max_bequest': max(scenario['bequest_amount'] for scenario in bequest_analysis.values()),
                'min_bequest': min(scenario['bequest_amount'] for scenario in bequest_analysis.values()),
                'avg_bequest': sum(scenario['bequest_amount'] for scenario in bequest_analysis.values()) / len(bequest_analysis)
            }
        }
    
    def calculate_optimal_plan(self, RA65: float, preferences: Dict = None) -> Dict:
        """
        根据用户偏好计算最优计划
        
        Args:
            RA65: 65岁时RA余额
            preferences: 用户偏好设置
            
        Returns:
            最优计划分析结果
        """
        if preferences is None:
            preferences = {
                'prioritize_monthly_income': True,  # 优先月收入
                'prioritize_bequest': False,        # 优先遗赠
                'risk_tolerance': 'moderate',       # 风险承受能力
                'expected_lifespan': 85            # 预期寿命
            }
        
        # 计算所有计划
        results = self.compare_plans(RA65, 65, preferences['expected_lifespan'])
        
        # 评分系统
        scores = {}
        for plan, result in results.items():
            score = 0
            
            # 月收入评分（前5年平均）
            avg_monthly_5yr = sum(result.monthly_schedule[:60]) / 60
            score += avg_monthly_5yr * 0.4 if preferences['prioritize_monthly_income'] else 0
            
            # 遗赠评分（80岁时）
            bequest_80 = result.snapshots.get('age_80', 0) or 0
            score += bequest_80 * 0.3 if preferences['prioritize_bequest'] else 0
            
            # 总领取评分
            score += result.total_payout * 0.3
            
            scores[plan] = score
        
        # 找出最优计划
        optimal_plan = max(scores, key=scores.get)
        
        return {
            'optimal_plan': optimal_plan,
            'scores': scores,
            'results': results,
            'recommendation': {
                'plan': optimal_plan,
                'monthly_income': results[optimal_plan].monthly_schedule[0],
                'total_payout': results[optimal_plan].total_payout,
                'bequest_at_80': results[optimal_plan].snapshots.get('age_80', 0) or 0,
                'reasoning': f"基于您的偏好，{optimal_plan}计划得分最高"
            }
        }
    
    def generate_payout_report(self, RA65: float, plan: str = "standard",
                             start_age: int = 65, horizon_age: int = 100) -> Dict:
        """
        生成详细的领取报告
        
        Args:
            RA65: 65岁时RA余额
            plan: 计划类型
            start_age: 开始年龄
            horizon_age: 终止年龄
            
        Returns:
            详细报告
        """
        result = self.cpf_life_simulate(RA65, plan, start_age, horizon_age)
        
        # 计算关键指标
        monthly_income = result.monthly_schedule[0] if result.monthly_schedule else 0
        total_payout = result.total_payout
        final_balance = result.final_balance
        
        # 计算不同年龄段的平均月收入
        age_ranges = {
            '65-70': result.monthly_schedule[:60],
            '70-80': result.monthly_schedule[60:180],
            '80-90': result.monthly_schedule[180:300],
            '90+': result.monthly_schedule[300:]
        }
        
        avg_by_age = {}
        for age_range, schedule in age_ranges.items():
            if schedule:
                avg_by_age[age_range] = sum(schedule) / len(schedule)
            else:
                avg_by_age[age_range] = 0
        
        return {
            'plan_summary': {
                'plan_type': plan,
                'ra65_balance': RA65,
                'start_age': start_age,
                'horizon_age': horizon_age,
                'total_months': len(result.monthly_schedule)
            },
            'financial_summary': {
                'initial_monthly_income': monthly_income,
                'total_payout': total_payout,
                'final_balance': final_balance,
                'payout_efficiency': total_payout / RA65 if RA65 > 0 else 0
            },
            'age_based_income': avg_by_age,
            'bequest_snapshots': result.snapshots,
            'monthly_schedule': result.monthly_schedule[:120],  # 前10年
            'bequest_curve': result.bequest_curve[:120]  # 前10年
        }
    
    def get_plan_comparison_table(self, RA65: float, start_age: int = 65,
                                horizon_age: int = 100) -> Dict:
        """
        生成计划对比表
        
        Args:
            RA65: 65岁时RA余额
            start_age: 开始年龄
            horizon_age: 终止年龄
            
        Returns:
            对比表数据
        """
        results = self.compare_plans(RA65, start_age, horizon_age)
        
        comparison_data = []
        for plan, result in results.items():
            comparison_data.append({
                'plan': plan,
                'initial_monthly': result.monthly_schedule[0] if result.monthly_schedule else 0,
                'total_payout': result.total_payout,
                'final_balance': result.final_balance,
                'bequest_at_70': result.snapshots.get('age_70', 0) or 0,
                'bequest_at_80': result.snapshots.get('age_80', 0) or 0,
                'bequest_at_90': result.snapshots.get('age_90', 0) or 0,
                'payout_efficiency': result.total_payout / RA65 if RA65 > 0 else 0
            })
        
        return {
            'ra65_balance': RA65,
            'comparison_table': comparison_data,
            'summary': {
                'highest_monthly': max(data['initial_monthly'] for data in comparison_data),
                'highest_total': max(data['total_payout'] for data in comparison_data),
                'highest_bequest': max(data['bequest_at_80'] for data in comparison_data)
            }
        }


# 便捷函数
def quick_cpf_life_calculation(RA65: float, plan: str = "standard") -> Dict:
    """
    快速CPF LIFE计算
    
    Args:
        RA65: 65岁时RA余额
        plan: 计划类型
        
    Returns:
        简化结果
    """
    calculator = CPFLifeOptimizedCalculator()
    result = calculator.cpf_life_simulate(RA65, plan)
    
    return {
        'monthly_income': result.monthly_schedule[0] if result.monthly_schedule else 0,
        'total_payout': result.total_payout,
        'final_balance': result.final_balance,
        'plan_type': result.plan_type
    }


def compare_all_plans(RA65: float) -> Dict:
    """
    比较所有CPF LIFE计划
    
    Args:
        RA65: 65岁时RA余额
        
    Returns:
        所有计划的对比结果
    """
    calculator = CPFLifeOptimizedCalculator()
    return calculator.get_plan_comparison_table(RA65)