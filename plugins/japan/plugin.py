#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import JapanConfig
from .tax_calculator import JapanTaxCalculator
from .pension_calculator import JapanPensionCalculator

class JapanPlugin(BaseCountryPlugin):
    """日本插件"""

    COUNTRY_CODE = "JP"
    COUNTRY_NAME = "日本"
    CURRENCY = "JPY"

    def __init__(self):
        super().__init__()
        self.tax_calculator = JapanTaxCalculator()
        self.pension_calculator = JapanPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = JapanConfig()
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
        """计算个人所得税"""
        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)
        return {
            'total_tax': tax_result.get('total_tax', 0),
            'taxable_income': tax_result.get('taxable_income', 0),
            'effective_rate': self.tax_calculator.calculate_effective_tax_rate(annual_income, deductions),
            'net_income': self.tax_calculator.calculate_net_income(annual_income, deductions)
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算厚生年金缴费"""
        # 厚生年金缴费率
        pension_rate = 0.1835  # 18.35%
        employee_rate = pension_rate / 2  # 9.175%
        employer_rate = pension_rate / 2  # 9.175%

        monthly_employee = monthly_salary * employee_rate
        monthly_employer = monthly_salary * employer_rate

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
        return 65

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return self.tax_calculator.get_tax_brackets()

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取厚生年金缴费率"""
        return {
            "employee": 0.09175,    # 员工缴费9.175%
            "employer": 0.09175,    # 雇主缴费9.175%
            "total": 0.1835         # 总缴费比例18.35%
        }
