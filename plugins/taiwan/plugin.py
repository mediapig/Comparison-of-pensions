#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import TaiwanConfig
from .tax_calculator import TaiwanTaxCalculator
from .pension_calculator import TaiwanPensionCalculator
from .taiwan_detailed_analyzer import TaiwanDetailedAnalyzer

class TaiwanPlugin(BaseCountryPlugin):
    """台湾插件"""

    COUNTRY_CODE = "TW"
    COUNTRY_NAME = "台湾"
    CURRENCY = "TWD"

    def __init__(self):
        super().__init__()
        self.tax_calculator = TaiwanTaxCalculator()
        self.pension_calculator = TaiwanPensionCalculator()
        self.detailed_analyzer = TaiwanDetailedAnalyzer()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = TaiwanConfig()
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
        """计算劳保缴费"""
        # 劳保缴费率
        employee_rate = 0.02  # 2% 员工
        employer_rate = 0.07  # 7% 雇主

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
        """获取劳保缴费率"""
        return {
            "employee": 0.02,        # 员工缴费2%
            "employer": 0.07,        # 雇主缴费7%
            "total": 0.09            # 总缴费比例9%
        }

    def print_detailed_analysis(self, person: Person, salary_profile: SalaryProfile,
                              economic_factors: EconomicFactors, pension_result,
                              currency_amount):
        """打印详细分析结果"""
        # 调用详细分析器
        self.detailed_analyzer.print_detailed_analysis(
            self, person, salary_profile, economic_factors, pension_result, currency_amount
        )
