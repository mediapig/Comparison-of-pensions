#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾退休金计算器
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class TaiwanPensionCalculator:
    """台湾劳保计算器"""

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算台湾劳保退休金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # 劳保缴费率（2024年）
        labor_insurance_rate = 0.11  # 11% 员工+雇主+政府
        employee_rate = 0.02  # 2% 员工
        employer_rate = 0.07  # 7% 雇主
        government_rate = 0.02  # 2% 政府

        # 计算月缴费
        monthly_employee = monthly_salary * employee_rate
        monthly_employer = monthly_salary * employer_rate
        monthly_total = monthly_employee + monthly_employer

        # 计算总缴费
        total_contribution = monthly_total * 12 * work_years

        # 简化的劳保计算
        # 假设年化回报率3%
        annual_return = 0.03
        total_balance = total_contribution * ((1 + annual_return) ** work_years)

        # 计算月退休金（简化）
        monthly_pension = monthly_salary * 0.6  # 大约60%替代率

        # 计算ROI
        retirement_years = 20
        total_benefit = monthly_pension * 12 * retirement_years
        roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = 65
        break_even_age = retirement_age + (total_contribution / (monthly_pension * 12)) if monthly_pension > 0 else None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            retirement_account_balance=total_balance,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="TWD",
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'labor_insurance_rate': labor_insurance_rate
            }
        )
