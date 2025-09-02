#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import CanadaConfig
from .tax_calculator import CanadaTaxCalculator
from .pension_calculator import CanadaPensionCalculator

class CanadaPlugin(BaseCountryPlugin):
    """加拿大插件"""

    COUNTRY_CODE = "CA"
    COUNTRY_NAME = "加拿大"
    CURRENCY = "CAD"

    def __init__(self):
        super().__init__()
        self.tax_calculator = CanadaTaxCalculator()
        self.pension_calculator = CanadaPensionCalculator()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = CanadaConfig()
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
        """计算CPP+EI缴费"""
        # CPP缴费率
        cpp_rate = 0.0595  # 5.95%
        employee_cpp = cpp_rate / 2  # 2.975%
        employer_cpp = cpp_rate / 2  # 2.975%

        # EI缴费率
        ei_rate = 0.0166  # 1.66%
        employee_ei = ei_rate
        employer_ei = ei_rate * 1.4  # 雇主缴费是员工的1.4倍

        # 缴费基数上限
        max_cpp_base = 71300 / 12  # CPP月度上限
        max_ei_base = 65000 / 12   # EI月度上限

        cpp_base = min(monthly_salary, max_cpp_base)
        ei_base = min(monthly_salary, max_ei_base)

        monthly_employee = (cpp_base * employee_cpp) + (ei_base * employee_ei)
        monthly_employer = (cpp_base * employer_cpp) + (ei_base * employer_ei)

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
        """获取社保缴费率"""
        return {
            "employee": 0.0595,     # CPP+EI员工缴费
            "employer": 0.0595,     # CPP+EI雇主缴费
            "total": 0.119          # 总缴费比例
        }
