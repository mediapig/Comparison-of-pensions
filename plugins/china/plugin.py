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
from .china_optimized_calculator import ChinaOptimizedCalculator, ChinaOptimizedParams
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
        self.optimized_calculator = ChinaOptimizedCalculator()
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
        """计算退休金 - 使用优化的7步算法计算器"""
        # 获取退休年龄
        retirement_age = self.get_retirement_age(person)
        start_age = 30  # 固定从30岁开始工作
        
        # 使用优化的7步算法计算器计算养老金
        annual_income = salary_profile.monthly_salary * 12
        pension_result = self.optimized_calculator.calculate_lifetime(
            initial_gross_income=annual_income,
            salary_growth_rate=salary_profile.annual_growth_rate,
            hf_rate=0.07  # 默认公积金比例7%
        )
        
        # 转换为PensionResult格式
        return PensionResult(
            monthly_pension=pension_result.monthly_pension,
            total_contribution=pension_result.total_contributions,
            total_benefit=pension_result.total_benefits,
            retirement_account_balance=pension_result.final_housing_fund_balance,
            break_even_age=pension_result.break_even_age,
            roi=pension_result.roi * 100,  # 转换为百分比
            original_currency=self.CURRENCY,
            details={
                'work_years': pension_result.total_work_years,
                'retirement_age': retirement_age,
                'basic_pension': pension_result.monthly_pension * 0.6,  # 估算基础养老金
                'personal_account_pension': pension_result.monthly_pension * 0.4,  # 估算个人账户养老金
                'housing_fund_balance': pension_result.final_housing_fund_balance,
                'total_employee_contributions': pension_result.total_employee_contributions,
                'total_employer_contributions': pension_result.total_employer_contributions,
                'final_pension_account_balance': pension_result.final_pension_account_balance
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
        """计算社保缴费 - 使用优化的7步算法计算器"""
        # 使用优化的7步算法计算器计算年度缴费
        annual_income = monthly_salary * 12
        avg_wage = self.optimized_calculator.params.avg_wage_2024
        
        # 计算第一年详细结果
        yearly_result = self.optimized_calculator.calculate_yearly(
            year=2024, 
            age=30, 
            gross_income=annual_income, 
            avg_wage=avg_wage, 
            hf_rate=0.07
        )
        
        return {
            'monthly_employee': yearly_result.emp_total_si / 12,
            'monthly_employer': yearly_result.er_total_si / 12,
            'total_employee': yearly_result.emp_total_si * years,
            'total_employer': yearly_result.er_total_si * years,
            'total_lifetime': (yearly_result.emp_total_si + yearly_result.er_total_si) * years,
            'housing_fund_employee': yearly_result.emp_hf / 12,
            'housing_fund_employer': yearly_result.er_hf / 12,
            'housing_fund_total': (yearly_result.emp_hf + yearly_result.er_hf) * years,
            'contribution_base': yearly_result.si_base_month,
            'housing_fund_base': yearly_result.hf_base_month
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
