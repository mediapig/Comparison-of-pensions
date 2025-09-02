#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国退休金计算插件 - 合并版本
整合了us插件的功能到usa插件中
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import USAConfig
from .tax_calculator import USATaxCalculator
from .pension_calculator import USAPensionCalculator

class USAPlugin(BaseCountryPlugin):
    """美国插件 - 合并版本"""

    COUNTRY_CODE = "US"
    COUNTRY_NAME = "美国"
    CURRENCY = "USD"

    def __init__(self):
        super().__init__()
        self.tax_calculator = USATaxCalculator()
        self.pension_calculator = USAPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = USAConfig()
        return PluginConfig(
            country_code=self.COUNTRY_CODE,
            country_name=self.COUNTRY_NAME,
            currency=self.CURRENCY,
            retirement_ages=config.retirement_ages,
            tax_year=config.tax_year
        )

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算退休金"""
        return self.pension_calculator.calculate_pension(person, salary_profile, economic_factors)

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算美国联邦税"""
        if deductions is None:
            deductions = {}

        # 2024年标准扣除额
        standard_deduction = 14600  # 单身

        # 应纳税所得额
        taxable_income = max(0, annual_income - standard_deduction - sum(deductions.values()))

        # 2024年税率表
        tax_brackets = [
            {'min': 0, 'max': 11000, 'rate': 0.10},
            {'min': 11000, 'max': 44725, 'rate': 0.12},
            {'min': 44725, 'max': 95375, 'rate': 0.22},
            {'min': 95375, 'max': 182050, 'rate': 0.24},
            {'min': 182050, 'max': 231250, 'rate': 0.32},
            {'min': 231250, 'max': 578125, 'rate': 0.35},
            {'min': 578125, 'max': float('inf'), 'rate': 0.37}
        ]

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
        """计算社安金缴费"""
        max_taxable = 160200 / 12  # 月度缴费基数上限
        contribution_base = min(monthly_salary, max_taxable)

        employee_rate = 0.062
        employer_rate = 0.062

        monthly_employee = contribution_base * employee_rate
        monthly_employer = contribution_base * employer_rate

        total_employee = monthly_employee * 12 * years
        total_employer = monthly_employer * 12 * years

        return {
            'monthly_employee': monthly_employee,
            'monthly_employer': monthly_employer,
            'annual_employee': monthly_employee * 12,
            'annual_employer': monthly_employer * 12,
            'total_employee': total_employee,
            'total_employer': total_employer,
            'total_lifetime': total_employee + total_employer
        }

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        # 美国目前男女相同
        return 67

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return [
            {'min': 0, 'max': 11000, 'rate': 0.10},
            {'min': 11000, 'max': 44725, 'rate': 0.12},
            {'min': 44725, 'max': 95375, 'rate': 0.22},
            {'min': 95375, 'max': 182050, 'rate': 0.24},
            {'min': 182050, 'max': 231250, 'rate': 0.32},
            {'min': 231250, 'max': 578125, 'rate': 0.35},
            {'min': 578125, 'max': float('inf'), 'rate': 0.37}
        ]

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {
            "employee": 0.062,      # 6.2% 社会保障税
            "employer": 0.062,      # 6.2% 雇主缴费
            "total": 0.124          # 总缴费比例 12.4%
        }
