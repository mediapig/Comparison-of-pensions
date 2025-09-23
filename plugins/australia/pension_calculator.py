#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚退休金计算器
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class AustraliaPensionCalculator:
    """澳大利亚超级年金计算器"""

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算澳大利亚超级年金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # 超级年金缴费率（2024年）
        super_rate = 0.12  # 12% 雇主强制缴费

        # 计算月缴费
        monthly_contribution = monthly_salary * super_rate

        # 计算总缴费
        total_contribution = monthly_contribution * 12 * work_years

        # 简化的超级年金计算
        # 假设年化回报率5%
        annual_return = 0.05
        total_balance = total_contribution * ((1 + annual_return) ** work_years)

        # 计算月退休金（假设领取20年）
        retirement_years = 20
        monthly_pension = total_balance / (retirement_years * 12)

        # 计算ROI
        roi = ((total_balance / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = 67
        break_even_age = retirement_age + (total_contribution / (monthly_pension * 12)) if monthly_pension > 0 else None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_balance,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="AUD",
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'super_rate': super_rate,
                'annual_return': annual_return
            }
        )
