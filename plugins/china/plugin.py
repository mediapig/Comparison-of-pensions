#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国退休金计算插件 - 合并版本
整合了cn插件的功能到china插件中
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import ChinaConfig
from .china_tax_calculator import ChinaTaxCalculator
from .pension_calculator import ChinaPensionCalculator

class ChinaPlugin(BaseCountryPlugin):
    """中国插件 - 合并版本"""

    COUNTRY_CODE = "CN"
    COUNTRY_NAME = "中国"
    CURRENCY = "CNY"

    def __init__(self):
        super().__init__()
        self.tax_calculator = ChinaTaxCalculator()
        self.pension_calculator = ChinaPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = ChinaConfig()
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
        # 使用china_tax_calculator的社保计算功能
        ss_result = self.tax_calculator.calculate_social_security_contribution(monthly_salary)

        # 计算终身总缴费
        monthly_employee = ss_result['total']
        monthly_employer = monthly_salary * 0.16  # 雇主缴费16%
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
        return self.config.retirement_ages.get(gender.lower(), 60)

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return self.tax_calculator.get_tax_brackets()

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {
            "employee": 0.08,        # 个人缴费比例 8%
            "employer": 0.16,        # 单位缴费比例 16%
            "total": 0.24            # 总缴费比例 24%
        }
