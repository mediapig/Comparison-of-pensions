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
from utils.smart_currency_converter import CurrencyAmount
from .config import ChinaConfig
from .china_tax_calculator import ChinaTaxCalculator
from .pension_calculator import ChinaPensionCalculator
from .china_social_security_calculator import ChinaSocialSecurityCalculator, ChinaSocialSecurityParams
from .china_detailed_analyzer import ChinaDetailedAnalyzer

class ChinaPlugin(BaseCountryPlugin):
    """中国插件 - 合并版本"""

    COUNTRY_CODE = "CN"
    COUNTRY_NAME = "中国"
    CURRENCY = "CNY"

    def __init__(self):
        super().__init__()
        self.tax_calculator = ChinaTaxCalculator()
        self.pension_calculator = ChinaPensionCalculator()
        self.social_security_calculator = ChinaSocialSecurityCalculator()
        self.detailed_analyzer = ChinaDetailedAnalyzer()

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
        """计算退休金 - 使用新的社保计算器"""
        # 获取退休年龄
        retirement_age = self.get_retirement_age(person)
        start_age = person.age if person.age > 0 else 30
        
        # 使用新的社保计算器计算养老金
        pension_result = self.social_security_calculator.calculate_lifetime_pension(
            monthly_salary=salary_profile.monthly_salary,
            start_age=start_age,
            retirement_age=retirement_age,
            salary_growth_rate=salary_profile.annual_growth_rate
        )
        
        # 转换为PensionResult格式
        return PensionResult(
            monthly_pension=pension_result.monthly_pension,
            total_contribution=pension_result.total_contributions,
            total_benefit=pension_result.total_benefits,
            retirement_account_balance=pension_result.housing_fund_balance + pension_result.medical_account_balance,
            break_even_age=pension_result.break_even_age,
            roi=pension_result.roi * 100,  # 转换为百分比
            original_currency=self.CURRENCY,
            details={
                'work_years': pension_result.work_years,
                'retirement_age': retirement_age,
                'basic_pension': pension_result.basic_pension,
                'personal_account_pension': pension_result.personal_account_pension,
                'housing_fund_balance': pension_result.housing_fund_balance,
                'medical_account_balance': pension_result.medical_account_balance,
                'total_employee_contributions': pension_result.total_employee_contributions,
                'total_employer_contributions': pension_result.total_employer_contributions
            }
        )

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
        """计算社保缴费 - 使用新的社保计算器"""
        # 使用新的社保计算器计算年度缴费
        ss_contribution = self.social_security_calculator.calculate_social_security_contribution(monthly_salary)
        hf_contribution = self.social_security_calculator.calculate_housing_fund_contribution(monthly_salary)
        
        return {
            'monthly_employee': ss_contribution.employee_total,
            'monthly_employer': ss_contribution.employer_total,
            'total_employee': ss_contribution.employee_total * 12 * years,
            'total_employer': ss_contribution.employer_total * 12 * years,
            'total_lifetime': ss_contribution.total_contribution * 12 * years,
            'housing_fund_employee': hf_contribution.employee_contribution,
            'housing_fund_employer': hf_contribution.employer_contribution,
            'housing_fund_total': hf_contribution.total_contribution * 12 * years,
            'contribution_base': ss_contribution.contribution_base,
            'housing_fund_base': hf_contribution.contribution_base
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
    
    def print_detailed_analysis(self, 
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细分析"""
        self.detailed_analyzer.print_detailed_analysis(
            self, person, salary_profile, economic_factors, pension_result, local_amount
        )
