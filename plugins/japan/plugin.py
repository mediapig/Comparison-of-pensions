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
from .japan_detailed_analyzer import JapanDetailedAnalyzer
from .japan_enhanced_calculator import JapanEnhancedCalculator

class JapanPlugin(BaseCountryPlugin):
    """日本插件"""

    COUNTRY_CODE = "JP"
    COUNTRY_NAME = "日本"
    CURRENCY = "JPY"

    def __init__(self):
        super().__init__()
        self.tax_calculator = JapanTaxCalculator()
        self.pension_calculator = JapanPensionCalculator()
        self.enhanced_calculator = JapanEnhancedCalculator()
        self.detailed_analyzer = JapanDetailedAnalyzer(None)  # 将在需要时设置engine

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
        # 使用增强计算器获得更准确的结果
        return self.enhanced_calculator.calculate_pension_result(person, salary_profile, economic_factors)

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算个人所得税"""
        # 使用增强计算器获得更准确的结果
        tax_result = self.enhanced_calculator.calculate_tax_detailed(annual_income)
        return {
            'total_tax': tax_result.get('total_tax', 0),
            'taxable_income': tax_result.get('taxable_income', 0),
            'effective_rate': tax_result.get('effective_rate', 0),
            'net_income': tax_result.get('net_income', 0)
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算厚生年金缴费"""
        annual_salary = monthly_salary * 12
        
        # 使用增强计算器的社保计算
        result = self.enhanced_calculator.calculate_tax_detailed(annual_salary)
        social_security = result.get('social_security', {})
        
        # 计算年度和月度缴费
        kosei_annual = social_security.get('kosei', 0)
        kenko_annual = social_security.get('kenko', 0)
        koyo_annual = social_security.get('koyo', 0)
        
        # 员工和雇主各承担一半（除了雇用保险）
        monthly_employee = (kosei_annual + kenko_annual) / 2 / 12 + koyo_annual / 12
        monthly_employer = (kosei_annual + kenko_annual) / 2 / 12
        
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
    
    def print_detailed_analysis(self, person: Person, salary_profile: SalaryProfile,
                              economic_factors: EconomicFactors, pension_result, 
                              currency_amount):
        """打印详细分析结果"""
        # 调用详细分析器
        self.detailed_analyzer.print_detailed_analysis(
            person, salary_profile, economic_factors, pension_result, currency_amount
        )
