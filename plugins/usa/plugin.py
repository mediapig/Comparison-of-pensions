#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国退休金计算插件 - 合并版本
整合了us插件的功能到usa插件中
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .config import USAConfig
from .tax_calculator import USATaxCalculator
from .pension_calculator import USAPensionCalculator

# 导入401k相关模块
try:
    from .usa_401k_calculator import USA401kCalculator, create_401k_calculator
    from .usa_401k_params import get_401k_params
    from .usa_detailed_analyzer import USADetailedAnalyzer
except ImportError:
    from usa_401k_calculator import USA401kCalculator, create_401k_calculator
    from usa_401k_params import get_401k_params
    from usa_detailed_analyzer import USADetailedAnalyzer

class USAPlugin(BaseCountryPlugin):
    """美国插件 - 合并版本"""

    COUNTRY_CODE = "US"
    COUNTRY_NAME = "美国"
    CURRENCY = "USD"

    def __init__(self):
        super().__init__()
        self.tax_calculator = USATaxCalculator()
        self.pension_calculator = USAPensionCalculator()
        self.k401_calculator = create_401k_calculator(2025)  # 使用2025年参数
        self.detailed_analyzer = USADetailedAnalyzer()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        config = USAConfig()
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
        """计算退休金（Social Security + 401k）"""
        # 计算Social Security部分
        ss_result = self.pension_calculator.calculate_pension(person, salary_profile, economic_factors)

        # 计算401k部分
        k401_result = self._calculate_401k_pension(person, salary_profile, economic_factors)

        # 合并结果
        total_monthly_pension = ss_result.monthly_pension + k401_result['monthly_pension']
        total_contribution = ss_result.total_contribution + k401_result['total_contribution']
        total_benefit = ss_result.total_benefit + k401_result['total_benefit']

        # 计算总ROI
        total_roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 更新details，包含401k信息
        details = ss_result.details.copy()
        details.update({
            'social_security_pension': ss_result.monthly_pension,
            'k401_pension': k401_result['monthly_pension'],
            'k401_balance': k401_result['final_balance'],
            'k401_total_contribution': k401_result['total_contribution'],
            'k401_employer_match': k401_result['employer_match_total'],
            'k401_investment_gains': k401_result['investment_gains']
        })

        return PensionResult(
            monthly_pension=total_monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            retirement_account_balance=k401_result['final_balance'],
            break_even_age=ss_result.break_even_age,
            roi=total_roi,
            original_currency="USD",
            details=details
        )

    def _calculate_401k_pension(self,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors) -> Dict[str, float]:
        """计算401k退休金"""
        # 将人民币月薪转换为美元（假设汇率1 CNY = 0.14 USD）
        cny_to_usd_rate = 0.14
        initial_annual_salary_usd = salary_profile.base_salary * 12 * cny_to_usd_rate

        # 计算401k
        k401_result = self.k401_calculator.calculate_401k_lifetime(
            start_age=person.age,
            retirement_age=self.get_retirement_age(person),
            initial_annual_salary=initial_annual_salary_usd,
            salary_growth_rate=salary_profile.annual_growth_rate,
            deferral_rate=0.10,  # 假设10%缴费比例
            investment_return_rate=economic_factors.investment_return_rate
        )

        # 计算退休期总收益（假设活到85岁）
        retirement_years = 85 - self.get_retirement_age(person)
        total_benefit = k401_result.withdrawal_analysis.annual_withdrawal * retirement_years

        return {
            'monthly_pension': k401_result.withdrawal_analysis.monthly_withdrawal,
            'annual_pension': k401_result.withdrawal_analysis.annual_withdrawal,
            'final_balance': k401_result.final_balance.total_balance,
            'total_contribution': k401_result.total_contributions,
            'employer_match_total': k401_result.final_balance.employer_contributions,
            'investment_gains': k401_result.total_gains,
            'total_benefit': total_benefit
        }

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算美国联邦税"""
        if deductions is None:
            deductions = {}

        # 2024年标准扣除额
        standard_deduction = 14600  # 单身

        # 应纳税所得额
        taxable_income = max(0, annual_income - standard_deduction - sum(deductions.values()))

        # 2024年税率表
        tax_brackets = [
            {'min': 0, 'max': 11000, 'rate': 0.10},
            {'min': 11000, 'max': 44725, 'rate': 0.12},
            {'min': 44725, 'max': 95375, 'rate': 0.22},
            {'min': 95375, 'max': 182050, 'rate': 0.24},
            {'min': 182050, 'max': 231250, 'rate': 0.32},
            {'min': 231250, 'max': 578125, 'rate': 0.35},
            {'min': 578125, 'max': float('inf'), 'rate': 0.37}
        ]

        total_tax = 0
        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                taxable_in_bracket = min(taxable_income - bracket['min'],
                                       bracket['max'] - bracket['min'])
                total_tax += taxable_in_bracket * bracket['rate']

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'effective_rate': (total_tax / annual_income * 100) if annual_income > 0 else 0,
            'net_income': annual_income - total_tax
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算社安金缴费"""
        max_taxable = 160200 / 12  # 月度缴费基数上限
        contribution_base = min(monthly_salary, max_taxable)

        employee_rate = 0.062
        employer_rate = 0.062

        monthly_employee = contribution_base * employee_rate
        monthly_employer = contribution_base * employer_rate

        total_employee = monthly_employee * 12 * years
        total_employer = monthly_employer * 12 * years

        return {
            'monthly_employee': monthly_employee,
            'monthly_employer': monthly_employer,
            'annual_employee': monthly_employee * 12,
            'annual_employer': monthly_employer * 12,
            'total_employee': total_employee,
            'total_employer': total_employer,
            'total_lifetime': total_employee + total_employer
        }

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        # 美国目前男女相同
        return 67

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return [
            {'min': 0, 'max': 11000, 'rate': 0.10},
            {'min': 11000, 'max': 44725, 'rate': 0.12},
            {'min': 44725, 'max': 95375, 'rate': 0.22},
            {'min': 95375, 'max': 182050, 'rate': 0.24},
            {'min': 182050, 'max': 231250, 'rate': 0.32},
            {'min': 231250, 'max': 578125, 'rate': 0.35},
            {'min': 578125, 'max': float('inf'), 'rate': 0.37}
        ]

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {
            "employee": 0.062,      # 6.2% 社会保障税
            "employer": 0.062,      # 6.2% 雇主缴费
            "total": 0.124          # 总缴费比例 12.4%
        }

    def get_401k_limits(self, age: int) -> Dict[str, float]:
        """获取401k缴费限制"""
        return self.k401_calculator.limits.get_employee_contribution_limit(age)

    def get_401k_analysis(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> Dict[str, Any]:
        """获取401k详细分析"""
        # 将人民币月薪转换为美元
        cny_to_usd_rate = 0.14
        initial_annual_salary_usd = salary_profile.base_salary * 12 * cny_to_usd_rate

        # 计算401k
        k401_result = self.k401_calculator.calculate_401k_lifetime(
            start_age=person.age,
            retirement_age=self.get_retirement_age(person),
            initial_annual_salary=initial_annual_salary_usd,
            salary_growth_rate=salary_profile.annual_growth_rate,
            deferral_rate=0.10,
            investment_return_rate=economic_factors.investment_return_rate
        )

        return {
            'k401_employee_total': k401_result.final_balance.employee_contributions,
            'k401_employer_total': k401_result.final_balance.employer_contributions,
            'k401_total_contributions': k401_result.total_contributions,
            'k401_balance': k401_result.final_balance.total_balance,
            'k401_monthly_pension': k401_result.withdrawal_analysis.monthly_withdrawal,
            'contribution_history': k401_result.contribution_history,
            'age_limits': {
                'current_age': person.age,
                'age_50_plus': person.age + 15,
                'age_60_plus': person.age + 25,
                'current_limit': self.get_401k_limits(person.age)['total_limit'],
                'age_50_limit': self.get_401k_limits(50)['total_limit'],
                'age_60_limit': self.get_401k_limits(60)['total_limit']
            },
            'employer_match_sample': {
                'salary': initial_annual_salary_usd,
                'employee_contribution': k401_result.contribution_history[0].total_employee_contribution if k401_result.contribution_history else 0,
                'employer_match': k401_result.contribution_history[0].employer_match if k401_result.contribution_history else 0,
                'total_401k': k401_result.contribution_history[0].total_contribution if k401_result.contribution_history else 0
            }
        }

    def get_contribution_scenarios(self, 
                                 annual_salary: float, 
                                 years: int = 35, 
                                 investment_rate: float = 0.07) -> List[Dict[str, Any]]:
        """获取不同缴费比例的401K场景分析"""
        return self.k401_calculator.get_contribution_scenarios(annual_salary, years, investment_rate)
    
    def print_detailed_analysis(self,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细的美国社保和401k分析"""
        self.detailed_analyzer.print_detailed_analysis(
            self, person, salary_profile, economic_factors, pension_result, local_amount
        )
