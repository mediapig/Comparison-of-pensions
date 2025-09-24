#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, Gender, EmploymentType
from .cpf_calculator import SingaporeCPFCalculator
from .cpf_payout_calculator import SingaporeCPFPayoutCalculator
from .singapore_tax_calculator_enhanced import SingaporeTaxCalculatorEnhanced
from .singapore_detailed_analyzer import SingaporeDetailedAnalyzer

class SingaporePlugin(BaseCountryPlugin):
    """新加坡插件"""

    COUNTRY_CODE = "SG"
    COUNTRY_NAME = "新加坡"
    CURRENCY = "SGD"

    def __init__(self):
        super().__init__()
        self.cpf_calculator = SingaporeCPFCalculator()
        self.cpf_payout_calculator = SingaporeCPFPayoutCalculator()
        self.tax_calculator_enhanced = SingaporeTaxCalculatorEnhanced()
        self.detailed_analyzer = SingaporeDetailedAnalyzer()

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        return PluginConfig(
            country_code=self.COUNTRY_CODE,
            country_name=self.COUNTRY_NAME,
            currency=self.CURRENCY,
            retirement_ages={"male": 62, "female": 62},
            tax_year=2024
        )

    def create_person(self, start_age: int = 30) -> Person:
        """创建Person对象 - 新加坡：30岁工作到65岁退休"""
        current_year = date.today().year
        return Person(
            name=f"{self.COUNTRY_NAME}用户",
            birth_date=date(current_year - start_age, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(current_year, 1, 1)
        )

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡CPF退休金 - 30岁工作到65岁退休"""
        monthly_salary = salary_profile.monthly_salary
        # 新加坡：30岁工作到65岁退休
        start_age = 30
        retirement_age = 65
        work_years = retirement_age - start_age  # 35年

        # 使用新的CPF计算器计算终身缴费
        lifetime_result = self.cpf_calculator.calculate_lifetime_cpf(
            monthly_salary, start_age, retirement_age
        )

        # 计算总缴费
        total_contribution = lifetime_result['total_lifetime']

        # CPF退休金计算（基于RA账户余额）
        ra_balance = lifetime_result['final_balances']['ra_balance']
        sa_balance = lifetime_result['final_balances']['sa_balance']

        # 使用CPF领取计算器计算月退休金
        # 合并RA和SA余额作为年金本金
        total_ra_balance = ra_balance + sa_balance

        if total_ra_balance > 0:
            payout_result = self.cpf_payout_calculator.calculate_cpf_life_payout(
                ra_balance=total_ra_balance,
                sa_balance=0,
                annual_nominal_rate=0.035,  # 3.5%年利率
                annual_inflation_rate=0.02,  # 2%通胀率
                payout_years=25,  # 25年领取期（65-90岁）
                scheme="level"  # 固定金额领取
            )

            monthly_pension = payout_result.monthly_payment
            total_benefit = payout_result.total_payments
        else:
            monthly_pension = 0
            total_benefit = 0

        # 计算正确的IRR - 基于个人现金流（修正版）
        irr_analysis = self.cpf_calculator.calculate_irr_analysis(
            monthly_salary, start_age, retirement_age
        )

        # 使用修正的IRR值
        irr_value = irr_analysis['irr_value']
        irr_percentage = irr_analysis['irr_percentage']

        # 获取传统模型结果用于兼容性
        simplified_result = irr_analysis['traditional_model']
        employee_total = simplified_result['employee_contrib_total']
        monthly_payout = simplified_result['monthly_payout']
        terminal_value = simplified_result['terminal_value']

        # 计算总收益（退休领取 + 终值）
        total_benefit_corrected = simplified_result['total_payout'] + terminal_value

        # 使用IRR作为ROI（如果IRR计算失败，则使用简单回报率）
        if irr_percentage is not None:
            roi = irr_percentage
        else:
            roi = (total_benefit_corrected / employee_total - 1) * 100 if employee_total > 0 else 0

        # 计算回本年龄（基于雇员缴费）
        if monthly_payout > 0:
            break_even_months = employee_total / monthly_payout
            break_even_age = retirement_age + (break_even_months / 12)
            break_even_age = int(break_even_age) if break_even_age < 90 else None
        else:
            break_even_age = None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            retirement_account_balance=ra_balance,
            break_even_age=break_even_age,
            roi=roi,
            original_currency=self.CURRENCY,
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'cpf_accounts': {
                    'oa_balance': lifetime_result['final_balances']['oa_balance'],
                    'sa_balance': sa_balance,
                    'ra_balance': ra_balance,
                    'ma_balance': lifetime_result['final_balances']['ma_balance']
                },
                'cpf_totals': {
                    'oa_total': lifetime_result['total_oa'],
                    'sa_total': lifetime_result['total_sa'],
                    'ra_total': lifetime_result['total_ra'],
                    'ma_total': lifetime_result['total_ma']
                },
                'cpf_payout': {
                    'monthly_payment': monthly_pension,
                    'total_payments': total_benefit,
                    'total_interest': total_benefit - total_ra_balance if total_ra_balance > 0 else 0,
                    'payout_years': 25,  # 65-90岁，25年
                    'scheme': 'standard'
                },
                'irr_analysis': {
                    'irr_value': irr_value,
                    'irr_percentage': irr_percentage,
                    'npv_value': irr_analysis['npv_value'],
                    'cash_flow_summary': irr_analysis['summary'],
                    'terminal_value': terminal_value,
                    'terminal_accounts': irr_analysis.get('terminal_accounts', {}),
                    'employee_contributions_total': employee_total,
                    'total_benefits': total_benefit_corrected
                }
            }
        )

    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算新加坡个人所得税 - 使用增强版算法"""
        if deductions is None:
            deductions = {}

        # 使用增强版税务计算器
        result = self.tax_calculator_enhanced.calculate_simple_tax(
            annual_income=annual_income,
            cpf_contribution=deductions.get('cpf_contribution', 0),
            other_reliefs=deductions.get('other_reliefs', 0),
            donations=deductions.get('donations', 0)
        )

        return {
            'total_tax': result['tax_payable'],
            'taxable_income': result['chargeable_income'],
            'effective_rate': result['effective_rate'],
            'net_income': result['net_income']
        }

    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算CPF缴费"""
        # 获取年龄（默认30岁开始工作）
        age = kwargs.get('age', 30)

        # 使用新的CPF计算器
        lifetime_result = self.cpf_calculator.calculate_lifetime_cpf(
            monthly_salary, age, age + years
        )

        return {
            'monthly_employee': lifetime_result['total_employee'] / (12 * years),
            'monthly_employer': lifetime_result['total_employer'] / (12 * years),
            'total_employee': lifetime_result['total_employee'],
            'total_employer': lifetime_result['total_employer'],
            'total_lifetime': lifetime_result['total_lifetime'],
            'cpf_breakdown': {
                'oa_total': lifetime_result['total_oa'],
                'sa_total': lifetime_result['total_sa'],
                'ra_total': lifetime_result['total_ra'],
                'ma_total': lifetime_result['total_ma']
            }
        }

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        return 65  # 修正为65岁退休

    def print_detailed_analysis(self,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount):
        """打印详细分析"""
        self.detailed_analyzer.print_detailed_analysis(
            self, person, salary_profile, economic_factors, pension_result, local_amount
        )

