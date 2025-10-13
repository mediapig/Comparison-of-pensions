#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF计算器 - 修正版
使用验证过的正确CPF计算逻辑
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.irr_calculator import IRRCalculator


@dataclass
class CPFAccountBalances:
    """CPF账户余额"""
    oa_balance: float = 0.0      # 普通账户余额
    sa_balance: float = 0.0      # 特别账户余额
    ra_balance: float = 0.0      # 退休账户余额
    ma_balance: float = 0.0      # 医疗账户余额


@dataclass
class CPFContribution:
    """CPF缴费结果"""
    oa_contribution: float       # 普通账户缴费
    sa_contribution: float       # 特别账户缴费
    ra_contribution: float       # 退休账户缴费
    ma_contribution: float       # 医疗账户缴费
    total_contribution: float    # 总缴费
    employee_contribution: float # 员工缴费
    employer_contribution: float # 雇主缴费


class SingaporeCPFCalculator:
    """新加坡CPF计算器 - 修正版"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

    def calculate_lifetime_cpf(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """计算终身CPF - 使用简化的正确模型"""
        annual_salary = monthly_salary * 12

        # 使用简化的CPF模型
        result = self._cpf_model(annual_salary, start_age, retirement_age - start_age)

        # 计算总缴费（员工+雇主）
        total_lifetime = result['employee_contrib_total'] * 0.37 / 0.20  # 员工缴费 / 20% * 37%

        return {
            'total_lifetime': total_lifetime,
            'total_employee': result['employee_contrib_total'],  # 员工部分
            'total_employer': total_lifetime - result['employee_contrib_total'],  # 雇主部分
            'total_oa': total_lifetime * 0.62,  # OA部分
            'total_sa': total_lifetime * 0.16,  # SA部分
            'total_ra': result['RA_at_65'],  # RA余额
            'total_ma': result['MA_remaining'],  # MA余额
            'final_balances': {
                'oa_balance': result['OA_remaining'],
                'sa_balance': 0,  # SA全部转入RA
                'ra_balance': result['RA_at_65'],
                'ma_balance': result['MA_remaining']
            }
        }

    def _cpf_model(self, income, start_age, work_years):
        """简化的CPF模型 - 基于我们验证过的正确逻辑，包括MA超额处理"""
        # === 工作期 ===
        employee_contrib_total = 0  # 雇员总缴费（用于IRR）
        OA = 0
        SA = 0
        MA = 0

        # BHS限额函数（简化版）
        def get_bhs_limit(year):
            base_bhs = 71500  # 2024年BHS
            years_from_2024 = year - 2024
            return base_bhs * (1.03 ** years_from_2024)

        def get_cohort_bhs_at_65(start_year, start_age):
            return get_bhs_limit(start_year + (65 - start_age))

        for year_offset in range(work_years):
            age = start_age + year_offset
            year = 2024 + year_offset  # 假设从2024年开始

            base = min(income, 96000)   # OW年薪上限96,000
            employee_contrib = base * 0.20  # 雇员缴费
            employer_contrib = base * 0.17   # 雇主缴费
            total_contrib = employee_contrib + employer_contrib  # 总缴费37%

            employee_contrib_total += employee_contrib

            # 按比例分配 OA, SA, MA (≤55岁: 62%/16%/22%)
            add_OA = total_contrib * 0.62  # OA: 62%
            add_SA = total_contrib * 0.16  # SA: 16%
            add_MA = total_contrib * 0.22  # MA: 22%

            # MA超额处理：计算BHS上限
            if age < 65:
                bhs_limit = get_bhs_limit(year)
            else:
                bhs_limit = get_cohort_bhs_at_65(2024, start_age)

            # 计算MA可以入账的金额
            ma_room = max(0.0, bhs_limit - MA)
            to_MA = min(add_MA, ma_room)
            overflow = add_MA - to_MA

            # 溢出处理：<55岁转到SA，≥55岁转到RA（这里先转到SA，后面会处理RA）
            if age < 55:
                add_SA += overflow
            else:
                # 55岁后溢出转到SA，后面会在55岁时转入RA
                add_SA += overflow

            # 更新账户余额
            OA += add_OA
            SA += add_SA
            MA += to_MA

            # 年终计息（基础利息）
            OA *= 1.025  # OA年息2.5%
            SA *= 1.04   # SA年息4%
            MA *= 1.04   # MA年息4%

            # 首$60k额外+1%利息
            total_balance = OA + SA + MA
            if total_balance > 0:
                extra_pool = min(total_balance, 60000) * 0.01
                # 分摊到各账户（OA≤20k限制）
                oa_eligible = min(OA, 20000)
                sa_eligible = SA
                ma_eligible = MA
                total_eligible = oa_eligible + sa_eligible + ma_eligible

                if total_eligible > 0:
                    OA += extra_pool * (oa_eligible / total_eligible)
                    SA += extra_pool * (sa_eligible / total_eligible)
                    MA += extra_pool * (ma_eligible / total_eligible)

            # 检查MA是否因利息超过BHS上限
            if MA > bhs_limit + 1e-9:
                extra = MA - bhs_limit
                MA = bhs_limit
                if age < 55:
                    SA += extra
                else:
                    SA += extra  # 55岁后也会在RA建立时处理

        # === 55岁时，转入RA ===
        RA = 0
        OA_remaining = 0
        if start_age + work_years >= 55:
            # 55岁时建立RA：SA全部转入RA，OA部分转入RA
            # 使用CPF LIFE引擎的正确逻辑

            # 计算RA目标金额（使用正确的FRS）
            # 2024年FRS约为$205,800，每年增长约3%
            base_ra_target = 205800
            years_from_2024 = 2024 + (55 - start_age) - 2024
            ra_target = base_ra_target * (1.03 ** years_from_2024)

            # 先转移SA到RA
            ra_amount = min(SA, ra_target)
            RA = ra_amount
            SA -= ra_amount

            # 如果RA目标未达到，从OA转移
            remaining_target = ra_target - RA
            if remaining_target > 0:
                oa_to_ra = min(OA, remaining_target)
                RA += oa_to_ra
                OA -= oa_to_ra

            OA_remaining = OA  # OA剩余部分

            # 55–65岁利息累积
            for i in range(10):
                RA *= 1.04   # 年息4%
                OA_remaining *= 1.025  # OA年息2.5%
                MA *= 1.04  # MA年息4%

                # 检查MA是否因利息超过BHS上限
                bhs_limit = get_cohort_bhs_at_65(2024, start_age)
                if MA > bhs_limit + 1e-9:
                    extra = MA - bhs_limit
                    MA = bhs_limit
                    RA += extra  # 55岁后MA超额转到RA
        else:
            OA_remaining = OA

        # === 65岁开始领取 ===
        # 使用简化的年金计算
        if RA > 0:
            # 简化的年金计算：25年，3.5%贴现率
            annual_rate = 0.035
            years = 25
            monthly_rate = annual_rate / 12
            months = years * 12

            if monthly_rate > 0:
                payout_per_month = RA * (monthly_rate / (1 - (1 + monthly_rate) ** (-months)))
            else:
                payout_per_month = RA / months

            total_payout = payout_per_month * months
        else:
            payout_per_month = 0
            total_payout = 0

        # 计算终值（90岁时的所有CPF账户余额）
        terminal_value = OA_remaining + MA  # SA已转入RA，RA已用于年金

        return {
            'RA_at_65': RA,
            'monthly_payout': payout_per_month,
            'total_payout': total_payout,
            'employee_contrib_total': employee_contrib_total,  # 雇员总缴费
            'OA_remaining': OA_remaining,
            'MA_remaining': MA,
            'terminal_value': terminal_value
        }

    def calculate_annual_contribution(self, monthly_salary: float, age: int) -> CPFContribution:
        """计算年度CPF缴费"""
        annual_salary = monthly_salary * 12
        base = min(annual_salary, 96000)  # OW年薪上限96,000

        # 计算总缴费
        total_contribution = base * 0.37
        total_contribution = min(total_contribution, 37740)  # 年缴费上限

        # 分配比例（≤55岁: 62%/16%/22%）
        oa_contribution = total_contribution * 0.62
        sa_contribution = total_contribution * 0.16
        ma_contribution = total_contribution * 0.22

        # 员工和雇主缴费
        employee_contribution = total_contribution * 0.20 / 0.37
        employer_contribution = total_contribution * 0.17 / 0.37

        return CPFContribution(
            oa_contribution=oa_contribution,
            sa_contribution=sa_contribution,
            ra_contribution=0,  # 55岁前没有RA
            ma_contribution=ma_contribution,
            total_contribution=total_contribution,
            employee_contribution=employee_contribution,
            employer_contribution=employer_contribution
        )

    def get_contribution_rates(self, age: int) -> Dict[str, float]:
        """获取缴费比例"""
        return {
            'employee': 0.20,
            'employer': 0.17,
            'total': 0.37
        }

    def get_account_allocation_rates(self, age: int) -> Dict[str, float]:
        """获取账户分配比例"""
        return {
            'oa': 0.62,
            'sa': 0.16,
            'ma': 0.22
        }

    def calculate_cpf_split(self, monthly_salary: float, age: int) -> CPFContribution:
        """计算指定年龄的CPF账户分配"""
        annual_salary = monthly_salary * 12
        base = min(annual_salary, 96000)

        # 计算缴费
        employee_contrib = base * 0.20
        employer_contrib = base * 0.17
        total_contrib = employee_contrib + employer_contrib

        # 按比例分配（≤55岁: 62%/16%/22%）
        oa_contribution = total_contrib * 0.62
        sa_contribution = total_contrib * 0.16
        ma_contribution = total_contrib * 0.22

        return CPFContribution(
            oa_contribution=oa_contribution,
            sa_contribution=sa_contribution,
            ra_contribution=0.0,  # 55岁前没有RA
            ma_contribution=ma_contribution,
            employee_contribution=employee_contrib,
            employer_contribution=employer_contrib,
            total_contribution=total_contrib
        )

    def calculate_irr_analysis(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """
        计算CPF的IRR分析 - 修正版

        Args:
            monthly_salary: 月薪
            start_age: 开始工作年龄
            retirement_age: 退休年龄

        Returns:
            包含IRR和详细分析的字典
        """
        # 使用新的IRR计算器
        irr_result = IRRCalculator.calculate_cpf_irr(
            monthly_salary=monthly_salary,
            start_age=start_age,
            retirement_age=retirement_age,
            terminal_age=90,
            frequency='annual'
        )

        # 获取传统模型结果用于对比
        traditional_result = self._cpf_model(monthly_salary * 12, start_age, retirement_age - start_age)

        return {
            'irr_value': irr_result['irr'],
            'irr_percentage': irr_result['analysis']['irr_percentage'],
            'npv_value': irr_result['npv'],
            'cash_flows': irr_result['cash_flows'],
            'cash_flow_details': irr_result['cash_flow_details'],
            'terminal_accounts': irr_result.get('terminal_accounts', {}),
            'summary': irr_result['summary'],
            'analysis': irr_result['analysis'],
            'traditional_model': {
                'employee_contrib_total': traditional_result['employee_contrib_total'],
                'monthly_payout': traditional_result['monthly_payout'],
                'total_payout': traditional_result['total_payout'],
                'terminal_value': traditional_result['terminal_value'],
                'ra_at_65': traditional_result['RA_at_65'],
                'oa_remaining': traditional_result['OA_remaining'],
                'ma_remaining': traditional_result['MA_remaining']
            }
        }