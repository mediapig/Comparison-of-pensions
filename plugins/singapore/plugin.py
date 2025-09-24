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
from .cpf_life_optimized import CPFLifeOptimizedCalculator
from .cpf_life_analyzer import CPFLifeAnalyzer, AnalysisConfig
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
        self.cpf_life_optimized = CPFLifeOptimizedCalculator()
        self.cpf_life_analyzer = CPFLifeAnalyzer()
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
        
        # 使用优化的CPF LIFE计算器计算月退休金
        from .cpf_life_optimized import CPFLifeOptimizedCalculator
        optimized_calculator = CPFLifeOptimizedCalculator()
        
        # 合并RA和SA余额作为年金本金
        total_ra_balance = ra_balance + sa_balance
        
        if total_ra_balance > 0:
            cpf_life_result = optimized_calculator.cpf_life_simulate(
                RA65=total_ra_balance,
                plan="standard",
                start_age=65,
                horizon_age=90  # 假设90岁去世
            )
            
            monthly_pension = cpf_life_result.monthly_schedule[0] if cpf_life_result.monthly_schedule else 0
            total_benefit = cpf_life_result.total_payout
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
    
    def calculate_cpf_life_analysis(self, ra65_balance: float, 
                                  plan: str = "standard") -> Dict:
        """
        计算CPF LIFE详细分析
        
        Args:
            ra65_balance: 65岁时RA余额
            plan: CPF LIFE计划类型 ("standard", "escalating", "basic")
            
        Returns:
            CPF LIFE分析结果
        """
        return self.cpf_life_optimized.cpf_life_simulate(ra65_balance, plan)
    
    def compare_cpf_life_plans(self, ra65_balance: float) -> Dict:
        """
        比较所有CPF LIFE计划
        
        Args:
            ra65_balance: 65岁时RA余额
            
        Returns:
            所有计划的对比结果
        """
        return self.cpf_life_optimized.compare_plans(ra65_balance)
    
    def generate_cpf_life_report(self, ra65_balance: float, 
                               output_format: str = 'text') -> str:
        """
        生成CPF LIFE详细报告
        
        Args:
            ra65_balance: 65岁时RA余额
            output_format: 输出格式 ('text', 'json')
            
        Returns:
            报告内容
        """
        return self.cpf_life_analyzer.generate_detailed_report(ra65_balance, output_format)
    
    def analyze_bequest_scenarios(self, ra65_balance: float, 
                                plan: str = "standard") -> Dict:
        """
        分析遗赠情景
        
        Args:
            ra65_balance: 65岁时RA余额
            plan: CPF LIFE计划类型
            
        Returns:
            遗赠分析结果
        """
        return self.cpf_life_optimized.analyze_bequest_scenarios(ra65_balance, plan)
    
    def get_optimal_cpf_life_plan(self, ra65_balance: float, 
                                 preferences: Dict = None) -> Dict:
        """
        获取最优CPF LIFE计划推荐
        
        Args:
            ra65_balance: 65岁时RA余额
            preferences: 用户偏好设置
            
        Returns:
            最优计划分析结果
        """
        return self.cpf_life_optimized.calculate_optimal_plan(ra65_balance, preferences)
