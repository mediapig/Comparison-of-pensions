#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class SingaporePlugin(BaseCountryPlugin):
    """新加坡插件"""

    COUNTRY_CODE = "SG"
    COUNTRY_NAME = "新加坡"
    CURRENCY = "SGD"

    def __init__(self):
        super().__init__()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        return PluginConfig(
            country_code=self.COUNTRY_CODE,
            country_name=self.COUNTRY_NAME,
            currency=self.CURRENCY,
            retirement_ages={"male": 62, "female": 62},
            tax_year=2024
        )

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡CPF退休金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # CPF缴费率（2024年）
        cpf_rates = {
            "employee": 0.20,  # 员工20%
            "employer": 0.17   # 雇主17%
        }

        # CPF缴费基数上限（2024年）
        max_contribution_base = 6000  # 月薪上限6000新币

        # 计算缴费基数
        contribution_base = min(monthly_salary, max_contribution_base)

        # 计算月缴费
        monthly_employee_contribution = contribution_base * cpf_rates["employee"]
        monthly_employer_contribution = contribution_base * cpf_rates["employer"]
        monthly_total_contribution = monthly_employee_contribution + monthly_employer_contribution

        # 计算总缴费
        total_contribution = monthly_total_contribution * 12 * work_years

        # 简化的CPF退休金计算
        # 实际CPF计算更复杂，这里简化处理
        monthly_pension = contribution_base * 0.4  # 大约40%替代率

        # 计算总收益
        retirement_years = 20  # 假设领取20年
        total_benefit = monthly_pension * 12 * retirement_years

        # 计算ROI
        roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = self.get_retirement_age(person)
        if monthly_pension > 0:
            break_even_months = total_contribution / monthly_pension
            break_even_age = retirement_age + (break_even_months / 12)
            break_even_age = int(break_even_age) if break_even_age < 85 else None
        else:
            break_even_age = None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency=self.CURRENCY,
            details={
                'contribution_base': contribution_base,
                'cpf_rates': cpf_rates,
                'work_years': work_years,
                'retirement_age': retirement_age,
                'max_contribution_base': max_contribution_base
            }
        )

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算新加坡个人所得税"""
        if deductions is None:
            deductions = {}

        # 2024年新加坡税率表
        tax_brackets = [
            {'min': 0, 'max': 20000, 'rate': 0.0},
            {'min': 20000, 'max': 30000, 'rate': 0.02},
            {'min': 30000, 'max': 40000, 'rate': 0.035},
            {'min': 40000, 'max': 80000, 'rate': 0.07},
            {'min': 80000, 'max': 120000, 'rate': 0.115},
            {'min': 120000, 'max': 160000, 'rate': 0.15},
            {'min': 160000, 'max': 200000, 'rate': 0.18},
            {'min': 200000, 'max': 240000, 'rate': 0.19},
            {'min': 240000, 'max': 280000, 'rate': 0.195},
            {'min': 280000, 'max': 320000, 'rate': 0.20},
            {'min': 320000, 'max': float('inf'), 'rate': 0.22}
        ]

        # 基本免税额
        basic_allowance = 20000

        # 应纳税所得额
        taxable_income = max(0, annual_income - basic_allowance - sum(deductions.values()))

        # 计算税额
        total_tax = 0
        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                taxable_in_bracket = min(taxable_income - bracket['min'],
                                       bracket['max'] - bracket['min'])
                total_tax += taxable_in_bracket * bracket['rate']

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'effective_rate': (total_tax / annual_income * 100) if annual_income > 0 else 0,
            'net_income': annual_income - total_tax
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算CPF缴费"""
        # CPF缴费率
        employee_rate = 0.20
        employer_rate = 0.17

        # 缴费基数上限
        max_base = 6000
        contribution_base = min(monthly_salary, max_base)

        monthly_employee = contribution_base * employee_rate
        monthly_employer = contribution_base * employer_rate

        total_employee = monthly_employee * 12 * years
        total_employer = monthly_employer * 12 * years

        return {
            'monthly_employee': monthly_employee,
            'monthly_employer': monthly_employer,
            'total_employee': total_employee,
            'total_employer': total_employer,
            'total_lifetime': total_employee + total_employer
        }

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        return 62
