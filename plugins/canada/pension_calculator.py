#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大退休金计算器
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class CanadaPensionCalculator:
    """加拿大CPP+OAS退休金计算器"""

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算加拿大CPP+OAS退休金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # CPP缴费率（2024年）
        cpp_rate = 0.0595  # 5.95% 员工+雇主各一半
        employee_rate = cpp_rate / 2  # 2.975%
        employer_rate = cpp_rate / 2  # 2.975%

        # CPP缴费基数上限（2024年）
        max_contributable_earnings = 71300 / 12  # 月度上限
        contribution_base = min(monthly_salary, max_contributable_earnings)

        # 计算月缴费
        monthly_employee = contribution_base * employee_rate
        monthly_employer = contribution_base * employer_rate
        monthly_total = monthly_employee + monthly_employer

        # 计算总缴费
        total_contribution = monthly_total * 12 * work_years

        # 简化的CPP计算
        # 假设年化回报率3%
        annual_return = 0.03
        total_balance = total_contribution * ((1 + annual_return) ** work_years)

        # CPP月退休金（简化计算）
        cpp_monthly = min(contribution_base * 0.25, 1433)  # 最大约1433加元

        # OAS（老年保障金）
        oas_monthly = 735  # 2024年标准OAS

        # 总月退休金
        monthly_pension = cpp_monthly + oas_monthly

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
            break_even_age=break_even_age,
            roi=roi,
            original_currency="CAD",
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'cpp_monthly': cpp_monthly,
                'oas_monthly': oas_monthly,
                'cpp_rate': cpp_rate
            }
        )
