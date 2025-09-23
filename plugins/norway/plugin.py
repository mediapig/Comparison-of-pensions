#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威退休金计算插件
基于2024年挪威政策
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import NorwayConfig
from .tax_calculator import NorwayTaxCalculator
from .pension_calculator import NorwayPensionCalculator

class NorwayPlugin(BaseCountryPlugin):
    """挪威插件"""

    COUNTRY_CODE = "NO"
    COUNTRY_NAME = "挪威"
    CURRENCY = "NOK"

    def __init__(self):
        super().__init__()
        self.tax_calculator = NorwayTaxCalculator()
        self.pension_calculator = NorwayPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = NorwayConfig()
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
        """计算社保缴费"""
        # 使用税收计算器的社保计算功能
        ss_result = self.tax_calculator.calculate_social_security_contribution(monthly_salary)
        employer_result = self.tax_calculator.calculate_employer_contributions(monthly_salary)

        # 计算终身总缴费
        monthly_employee = ss_result['total']
        monthly_employer = employer_result['total']
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
        gender = person.gender.value if hasattr(person.gender, 'value') else person.gender
        return self.config.retirement_ages.get(gender.lower(), 67)

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return self.tax_calculator.get_tax_brackets()

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {
            "employee": 0.08,        # 个人缴费比例 8%
            "employer": 0.14,        # 雇主缴费比例 14%
            "total": 0.22            # 总缴费比例 22%
        }

    def format_currency(self, amount: float) -> str:
        """格式化货币显示"""
        return f"kr {amount:,.0f}"

    def get_country_info(self) -> Dict[str, Any]:
        """获取国家信息"""
        return {
            'country_code': self.COUNTRY_CODE,
            'country_name': self.COUNTRY_NAME,
            'currency': self.CURRENCY,
            'retirement_age': 67,
            'tax_system': 'Flat tax with basic deduction',
            'pension_system': 'Folketrygden (National Insurance)',
            'social_security_rate': 0.22,
            'tax_rate': 0.44
        }