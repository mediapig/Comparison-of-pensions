#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英国退休金计算器
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class UKPensionCalculator:
    """英国国家养老金计算器"""

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算英国国家养老金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # 国家保险缴费率（2024年）
        ni_rate = 0.12  # 12% 员工缴费（收入在12,570-50,270英镑之间）

        # 计算月缴费
        monthly_employee = monthly_salary * ni_rate
        monthly_employer = monthly_salary * 0.138  # 13.8% 雇主缴费
        monthly_total = monthly_employee + monthly_employer

        # 计算总缴费
        total_contribution = monthly_total * 12 * work_years

        # 简化的国家养老金计算
        # 假设年化回报率2%
        annual_return = 0.02
        total_balance = total_contribution * ((1 + annual_return) ** work_years)

        # 国家养老金（2024年）
        state_pension_monthly = 221.20  # 英镑/周，约960英镑/月

        # 计算ROI
        retirement_years = 20
        total_benefit = state_pension_monthly * 12 * retirement_years
        roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = 68
        break_even_age = retirement_age + (total_contribution / (state_pension_monthly * 12)) if state_pension_monthly > 0 else None

        return PensionResult(
            monthly_pension=state_pension_monthly,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="GBP",
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'ni_rate': ni_rate
            }
        )
