#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港退休金计算器
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class HongKongPensionCalculator:
    """香港强积金计算器"""

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算香港强积金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # 强积金缴费率
        mpf_rate = 0.05  # 5% 员工+雇主各5%

        # 缴费基数上下限
        min_contribution = 7100  # 最低收入水平
        max_contribution = 30000  # 最高收入水平

        # 计算缴费基数
        if monthly_salary < min_contribution:
            contribution_base = 0  # 低于最低水平不缴费
        elif monthly_salary > max_contribution:
            contribution_base = max_contribution
        else:
            contribution_base = monthly_salary

        # 计算月缴费
        monthly_employee = contribution_base * mpf_rate
        monthly_employer = contribution_base * mpf_rate
        monthly_total = monthly_employee + monthly_employer

        # 计算总缴费
        total_contribution = monthly_total * 12 * work_years

        # 简化的强积金计算
        # 假设年化回报率4%
        annual_return = 0.04
        total_balance = total_contribution * ((1 + annual_return) ** work_years)

        # 计算月退休金（假设领取20年）
        retirement_years = 20
        monthly_pension = total_balance / (retirement_years * 12)

        # 计算ROI
        roi = ((total_balance / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = 65
        break_even_age = retirement_age + (total_contribution / (monthly_pension * 12)) if monthly_pension > 0 else None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_balance,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="HKD",
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'mpf_rate': mpf_rate,
                'annual_return': annual_return
            }
        )
