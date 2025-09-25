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
from .japan_detailed_analyzer import JapanDetailedAnalyzer
from .japan_corrected_calculator import JapanCorrectedCalculator

class JapanPlugin(BaseCountryPlugin):
    """日本插件"""

    COUNTRY_CODE = "JP"
    COUNTRY_NAME = "日本"
    CURRENCY = "JPY"

    def __init__(self):
        super().__init__()
        self.tax_calculator = JapanTaxCalculator()
        self.corrected_calculator = JapanCorrectedCalculator()
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
        # 使用修正计算器获得更准确的结果
        return self.corrected_calculator.calculate_pension_result(person, salary_profile, economic_factors)

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算个人所得税"""
        # 使用修正计算器获得更准确的结果
        tax_result = self.corrected_calculator.calculate_tax_detailed(annual_income)
        return {
            'total_tax': tax_result.get('total_tax', 0),
            'taxable_income': tax_result.get('taxable_income', 0),
            'effective_rate': tax_result.get('effective_rate', 0),
            'net_income': tax_result.get('net_income', 0),
            'total_deductions': sum(tax_result.get('deductions', {}).values()),
            'breakdown': {
                'salary_deduction': tax_result.get('deductions', {}).get('salary_deduction', 0),
                'basic_deduction': tax_result.get('deductions', {}).get('basic_deduction', 0),
                'pension_deduction': tax_result.get('deductions', {}).get('ss_deduction', 0),
                'other_deductions': 0
            }
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算厚生年金缴费"""
        annual_salary = monthly_salary * 12
        
        # 使用修正计算器的社保计算
        result = self.corrected_calculator.calculate_tax_detailed(annual_salary)
        social_security = result.get('social_security', {})
        
        # 计算年度和月度缴费
        kosei_info = social_security.get('kosei', {})
        kenko_info = social_security.get('kenko', {})
        koyo_info = social_security.get('koyo', {})
        
        # 员工和雇主分别计算
        monthly_employee = (kosei_info.get('employee', 0) + 
                           kenko_info.get('employee', 0) + 
                           koyo_info.get('employee', 0))
        
        monthly_employer = (kosei_info.get('employer', 0) + 
                           kenko_info.get('employer', 0) + 
                           koyo_info.get('employer', 0))
        
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
