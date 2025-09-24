#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF插件 - 性能优化版
使用优化后的计算器提升性能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core.plugin_base import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, CurrencyAmount
from plugins.singapore.cpf_calculator_optimized import SingaporeCPFCalculatorOptimized
from plugins.singapore.cpf_payout_calculator import SingaporeCPFPayoutCalculator
from plugins.singapore.singapore_tax_calculator_enhanced import SingaporeTaxCalculatorEnhanced
from utils.performance_monitor import monitor_performance


class SingaporePluginOptimized(BaseCountryPlugin):
    """新加坡CPF插件 - 性能优化版"""

    def __init__(self):
        super().__init__()
        self.cpf_calculator = SingaporeCPFCalculatorOptimized()
        self.cpf_payout_calculator = SingaporeCPFPayoutCalculator()
        self.tax_calculator = SingaporeTaxCalculatorEnhanced()

    def _load_config(self) -> PluginConfig:
        """加载插件配置"""
        return PluginConfig(
            country_code='SG',
            country_name='新加坡',
            currency='SGD',
            retirement_age=65,
            contribution_rate=0.37,
            description='新加坡中央公积金(CPF)系统 - 性能优化版'
        )

    @monitor_performance
    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡CPF退休金 - 优化版"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35
        start_age = person.age if person.age > 0 else 30
        retirement_age = self.get_retirement_age(person)

        # 使用优化的CPF计算器计算终身缴费
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
            annual_nominal_rate=0.035,  # 3.5%年利率（与CPF Life一致）
            annual_inflation_rate=0.02,  # 2%通胀率
            payout_years=25,  # 25年领取期（65-90岁）
            scheme="level"  # 固定金额领取
        )
        
        monthly_pension = payout_result.monthly_payment
        total_benefit = payout_result.total_payments

        # 计算优化的IRR - 基于个人现金流
        irr_analysis = self.cpf_calculator.calculate_irr_analysis(
            monthly_salary, start_age, retirement_age
        )
        
        # 使用优化的IRR值
        irr_value = irr_analysis['irr_value']
        irr_percentage = irr_analysis['irr_percentage']
        
        # 获取传统模型结果用于兼容性
        simplified_result = irr_analysis['traditional_model']
        employee_total = simplified_result['employee_contrib_total']
        monthly_payout = simplified_result['monthly_payout']

        # 计算替代率
        final_salary = monthly_salary * (1 + salary_profile.annual_growth_rate) ** work_years
        replacement_rate = monthly_pension / final_salary if final_salary > 0 else 0

        # 计算税收影响
        annual_income = monthly_salary * 12
        taxable_income = annual_income - (annual_income * 0.20)  # 扣除员工CPF缴费
        tax_result = self.tax_calculator.calc_tax(taxable_income)
        net_income = taxable_income - tax_result.get('total_tax', 0)

        # 计算ROI
        roi_percentage = (total_benefit - employee_total) / employee_total * 100 if employee_total > 0 else 0

        # 计算回本年龄
        if monthly_pension > 0:
            break_even_months = employee_total / monthly_pension
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
            roi=roi_percentage / 100,  # 转换为小数
            original_currency=self.CURRENCY,
            details={
                'work_years': work_years,
                'retirement_age': retirement_age,
                'cpf_accounts': lifetime_result['final_balances'],
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
                },
                'irr_analysis': {
                    'irr_value': irr_value,
                    'irr_percentage': irr_percentage,
                    'employee_contrib_total': employee_total,
                    'monthly_payout': monthly_payout
                },
                'replacement_rate': replacement_rate,
                'net_income': net_income,
                'tax_amount': tax_result.get('total_tax', 0),
                'optimization_info': {
                    'version': 'optimized',
                    'performance_improvements': [
                        '向量化计算替代循环',
                        '缓存机制避免重复计算',
                        '简化的年金公式',
                        '优化的IRR计算'
                    ]
                }
            }
        )

    @monitor_performance
    def calculate_tax(self, annual_income: float) -> dict:
        """计算税收 - 优化版"""
        return self.tax_calculator.calc_tax(annual_income)

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        return 65  # 新加坡CPF标准退休年龄

    def get_contribution_rates(self, age: int) -> dict:
        """获取缴费比例"""
        return self.cpf_calculator.get_contribution_rates(age)

    def get_account_allocation_rates(self, age: int) -> dict:
        """获取账户分配比例"""
        return self.cpf_calculator.get_account_allocation_rates(age)

    def calculate_annual_contribution(self, monthly_salary: float, age: int) -> dict:
        """计算年度缴费"""
        contribution = self.cpf_calculator.calculate_annual_contribution(monthly_salary, age)
        return {
            'oa_contribution': contribution.oa_contribution,
            'sa_contribution': contribution.sa_contribution,
            'ra_contribution': contribution.ra_contribution,
            'ma_contribution': contribution.ma_contribution,
            'total_contribution': contribution.total_contribution,
            'employee_contribution': contribution.employee_contribution,
            'employer_contribution': contribution.employer_contribution
        }

    def get_performance_benchmark(self) -> dict:
        """获取性能基准测试结果"""
        return self.cpf_calculator.benchmark_performance()

    def get_performance_summary(self) -> dict:
        """获取性能摘要"""
        from utils.performance_monitor import performance_monitor
        return performance_monitor.get_performance_summary()


# 创建插件实例
plugin = SingaporePluginOptimized()