#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import AustraliaConfig
from .tax_calculator import AustraliaTaxCalculator
from .pension_calculator import AustraliaPensionCalculator

class AustraliaPlugin(BaseCountryPlugin):
    """澳大利亚插件"""

    COUNTRY_CODE = "AU"
    COUNTRY_NAME = "澳大利亚"
    CURRENCY = "AUD"

    def __init__(self):
        super().__init__()
        self.tax_calculator = AustraliaTaxCalculator()
        self.pension_calculator = AustraliaPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = AustraliaConfig()
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
        """计算超级年金缴费"""
        # 超级年金缴费率
        super_rate = 0.12  # 12% 雇主强制缴费

        monthly_employer = monthly_salary * super_rate
        monthly_employee = 0  # 员工通常不缴费

        total_employer = monthly_employer * 12 * years
        total_employee = 0

        return {
            'monthly_employee': monthly_employee,
            'monthly_employer': monthly_employer,
            'total_employee': total_employee,
            'total_employer': total_employer,
            'total_lifetime': total_employee + total_employer
        }

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        return 67

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return self.tax_calculator.get_tax_brackets()

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取超级年金缴费率"""
        return {
            "employee": 0.0,         # 员工通常不缴费
            "employer": 0.12,        # 雇主强制缴费12%
            "total": 0.12            # 总缴费比例12%
        }
