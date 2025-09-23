#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡退休金计算插件
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .cpf_calculator import SingaporeCPFCalculator, CPFAccountBalances
from .cpf_payout_calculator import SingaporeCPFPayoutCalculator
from .singapore_tax_calculator_enhanced import SingaporeTaxCalculatorEnhanced

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

    def _load_config(self) -> PluginConfig:
        """加载配置"""
        return PluginConfig(
            country_code=self.COUNTRY_CODE,
            country_name=self.COUNTRY_NAME,
            currency=self.CURRENCY,
            retirement_ages={"male": 62, "female": 62},
            tax_year=2024
        )

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡CPF退休金"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35
        start_age = person.age if person.age > 0 else 30
        retirement_age = self.get_retirement_age(person)

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
        payout_result = self.cpf_payout_calculator.calculate_cpf_life_payout(
            ra_balance=ra_balance,
            sa_balance=sa_balance,
            annual_nominal_rate=0.04,  # 4%年利率
            annual_inflation_rate=0.02,  # 2%通胀率
            payout_years=30,  # 30年领取期
            scheme="level"  # 固定金额领取
        )
        
        monthly_pension = payout_result.monthly_payment
        total_benefit = payout_result.total_payments

        # 计算ROI
        roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        if monthly_pension > 0:
            break_even_months = total_contribution / monthly_pension
            break_even_age = retirement_age + (break_even_months / 12)
            break_even_age = int(break_even_age) if break_even_age < 85 else None
        else:
            break_even_age = None

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
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
                    'monthly_payment': payout_result.monthly_payment,
                    'total_payments': payout_result.total_payments,
                    'total_interest': payout_result.total_interest,
                    'payout_years': payout_result.payout_years,
                    'scheme': 'level'
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
        return 62
