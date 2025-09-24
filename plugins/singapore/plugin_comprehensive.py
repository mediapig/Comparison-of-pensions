#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡退休金计算插件 - 综合版
集成新的CPF综合引擎，提供完整的CPF规则实现
"""

from typing import Dict, List, Optional, Any
from datetime import date

from core.base_plugin import BaseCountryPlugin, PluginConfig
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from .cpf_comprehensive_engine import (
    CPFComprehensiveEngine, CPFParameters, CPFComprehensiveResult,
    run_cpf_simulation, compare_cpf_life_plans, create_default_parameters
)
from .cpf_life_analyzer import CPFLifeAnalyzer, AnalysisConfig
from .singapore_tax_calculator_enhanced import SingaporeTaxCalculatorEnhanced
from .singapore_detailed_analyzer import SingaporeDetailedAnalyzer


class SingaporeComprehensivePlugin(BaseCountryPlugin):
    """新加坡综合插件 - 使用新的CPF综合引擎"""

    COUNTRY_CODE = "SG"
    COUNTRY_NAME = "新加坡"
    CURRENCY = "SGD"

    def __init__(self):
        super().__init__()
        self.cpf_engine = CPFComprehensiveEngine()
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
        """计算新加坡CPF退休金 - 使用综合引擎"""
        
        # 创建CPF参数
        cpf_params = CPFParameters(
            start_age=person.age if person.age > 0 else 30,
            retirement_age=self.get_retirement_age(person),
            end_age=90,  # 默认90岁
            annual_salary=salary_profile.monthly_salary * 12,
            salary_growth_rate=economic_factors.salary_growth_rate if hasattr(economic_factors, 'salary_growth_rate') else 0.02,
            ra_target_type="FRS",
            cpf_life_plan="standard",
            use_personal_irr=True
        )
        
        # 运行综合模拟
        self.cpf_engine.params = cpf_params  # 使用正确的参数
        cpf_result = self.cpf_engine.run_comprehensive_simulation()
        
        # 计算月退休金
        monthly_pension = cpf_result.cpf_life_result.monthly_payouts[0] if cpf_result.cpf_life_result.monthly_payouts else 0
        
        # 计算总收益
        total_benefit = cpf_result.total_benefits
        
        # 计算回本年龄
        break_even_age = None
        if monthly_pension > 0:
            break_even_months = cpf_result.total_employee_contributions / monthly_pension
            break_even_age = cpf_params.retirement_age + (break_even_months / 12)
            break_even_age = int(break_even_age) if break_even_age < 90 else None
        
        # 计算ROI
        roi = cpf_result.personal_irr * 100 if cpf_result.personal_irr else 0
        
        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=cpf_result.total_contributions,
            total_benefit=total_benefit,
            retirement_account_balance=cpf_result.ra_balance_at_65,
            break_even_age=break_even_age,
            roi=roi,
            original_currency=self.CURRENCY,
            details={
                'work_years': cpf_result.work_years,
                'retirement_age': cpf_params.retirement_age,
                'cpf_accounts_at_65': {
                    'oa_balance': cpf_result.oa_balance_at_65,
                    'sa_balance': cpf_result.sa_remaining_at_55,  # SA在55岁后基本为0
                    'ra_balance': cpf_result.ra_balance_at_65,
                    'ma_balance': cpf_result.ma_balance_at_65
                },
                'cpf_accounts_at_55': {
                    'ra_established': cpf_result.ra_established_at_55,
                    'oa_remaining': cpf_result.oa_remaining_at_55,
                    'sa_remaining': cpf_result.sa_remaining_at_55,
                    'cash_withdrawn': cpf_result.cash_withdrawn_at_55
                },
                'cpf_life_analysis': {
                    'plan': cpf_result.cpf_life_result.plan,
                    'monthly_payout': monthly_pension,
                    'total_payout': cpf_result.cpf_life_result.total_payout,
                    'final_balance': cpf_result.cpf_life_result.final_balance,
                    'bequest_at_80': cpf_result.cpf_life_result.bequest_at_80,
                    'bequest_at_90': cpf_result.cpf_life_result.bequest_at_90,
                    'payout_efficiency': cpf_result.cpf_life_result.payout_efficiency
                },
                'financial_analysis': {
                    'total_employee_contributions': cpf_result.total_employee_contributions,
                    'total_employer_contributions': cpf_result.total_employer_contributions,
                    'total_contributions': cpf_result.total_contributions,
                    'total_benefits': cpf_result.total_benefits,
                    'terminal_value': cpf_result.terminal_value,
                    'personal_irr': cpf_result.personal_irr,
                    'system_irr': cpf_result.system_irr,
                    'npv_personal': cpf_result.npv_personal,
                    'npv_system': cpf_result.npv_system
                },
                'validation': {
                    'passed': cpf_result.validation_passed,
                    'errors': cpf_result.validation_errors
                },
                'yearly_breakdown': [
                    {
                        'age': yr.age,
                        'year': yr.year,
                        'salary': yr.salary,
                        'cpf_base': yr.cpf_base,
                        'employee_contrib': yr.employee_contrib,
                        'employer_contrib': yr.employer_contrib,
                        'oa_balance': yr.oa_balance,
                        'sa_balance': yr.sa_balance,
                        'ma_balance': yr.ma_balance,
                        'ra_balance': yr.ra_balance,
                        'bhs_limit': yr.bhs_limit,
                        'ma_overflow': yr.ma_overflow
                    }
                    for yr in cpf_result.yearly_results
                ]
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
        """计算CPF缴费 - 使用综合引擎"""
        # 获取年龄（默认30岁开始工作）
        age = kwargs.get('age', 30)
        
        # 创建CPF参数
        cpf_params = CPFParameters(
            start_age=age,
            retirement_age=age + years,
            end_age=90,
            annual_salary=monthly_salary * 12,
            salary_growth_rate=kwargs.get('salary_growth_rate', 0.02),
            ra_target_type="FRS",
            cpf_life_plan="standard"
        )
        
        # 运行模拟
        cpf_result = self.cpf_engine.run_comprehensive_simulation()
        
        return {
            'monthly_employee': cpf_result.total_employee_contributions / (12 * years),
            'monthly_employer': cpf_result.total_employer_contributions / (12 * years),
            'total_employee': cpf_result.total_employee_contributions,
            'total_employer': cpf_result.total_employer_contributions,
            'total_lifetime': cpf_result.total_contributions,
            'cpf_breakdown': {
                'oa_total': sum(yr.oa_allocation for yr in cpf_result.yearly_results),
                'sa_total': sum(yr.sa_allocation for yr in cpf_result.yearly_results),
                'ma_total': sum(yr.ma_allocation for yr in cpf_result.yearly_results),
                'ra_total': cpf_result.ra_balance_at_65
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
        # 创建临时参数
        temp_params = CPFParameters(
            start_age=65,
            retirement_age=65,
            end_age=90,
            annual_salary=0,  # 不需要薪资
            cpf_life_plan=plan
        )
        
        temp_engine = CPFComprehensiveEngine(temp_params)
        return temp_engine._calculate_cpf_life(ra65_balance)
    
    def compare_cpf_life_plans(self, ra65_balance: float) -> Dict:
        """
        比较所有CPF LIFE计划
        
        Args:
            ra65_balance: 65岁时RA余额
            
        Returns:
            所有计划的对比结果
        """
        temp_params = CPFParameters(
            start_age=65,
            retirement_age=65,
            end_age=90,
            annual_salary=0
        )
        
        temp_engine = CPFComprehensiveEngine(temp_params)
        return temp_engine.compare_plans(ra65_balance)
    
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
        temp_params = CPFParameters(
            start_age=65,
            retirement_age=65,
            end_age=90,
            annual_salary=0,
            cpf_life_plan=plan
        )
        
        temp_engine = CPFComprehensiveEngine(temp_params)
        return temp_engine.analyze_bequest_scenarios(ra65_balance, plan)
    
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
        temp_params = CPFParameters(
            start_age=65,
            retirement_age=65,
            end_age=90,
            annual_salary=0
        )
        
        temp_engine = CPFComprehensiveEngine(temp_params)
        return temp_engine.calculate_optimal_plan(ra65_balance, preferences)
    
    def run_comprehensive_simulation(self, **kwargs) -> CPFComprehensiveResult:
        """
        运行综合CPF模拟
        
        Args:
            **kwargs: CPF参数
            
        Returns:
            综合模拟结果
        """
        params = create_default_parameters(**kwargs)
        engine = CPFComprehensiveEngine(params)
        return engine.run_comprehensive_simulation()
    
    def run_ra_target_comparison(self, **kwargs) -> Dict[str, CPFComprehensiveResult]:
        """
        运行RA目标比较
        
        Args:
            **kwargs: CPF参数
            
        Returns:
            不同RA目标的结果
        """
        ra_targets = ["FRS", "ERS", "BRS"]
        results = {}
        
        for target in ra_targets:
            params = create_default_parameters(**kwargs, ra_target_type=target)
            engine = CPFComprehensiveEngine(params)
            results[target] = engine.run_comprehensive_simulation()
        
        return results
    
    def run_sensitivity_analysis(self, **kwargs) -> Dict[str, Any]:
        """
        运行敏感性分析
        
        Args:
            **kwargs: CPF参数
            
        Returns:
            敏感性分析结果
        """
        base_params = kwargs.copy()
        
        # 起始年龄敏感性
        start_ages = [25, 30, 35, 40]
        start_age_results = {}
        
        for start_age in start_ages:
            params_dict = base_params.copy()
            params_dict['start_age'] = start_age
            params = create_default_parameters(**params_dict)
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            start_age_results[start_age] = {
                'monthly_pension': result.cpf_life_result.monthly_payouts[0],
                'total_benefits': result.total_benefits,
                'personal_irr': result.personal_irr
            }
        
        # 薪资水平敏感性
        salaries = [120000, 180000, 240000, 300000]
        salary_results = {}
        
        for salary in salaries:
            params_dict = base_params.copy()
            params_dict['annual_salary'] = salary
            params = create_default_parameters(**params_dict)
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            salary_results[salary] = {
                'monthly_pension': result.cpf_life_result.monthly_payouts[0],
                'total_benefits': result.total_benefits,
                'personal_irr': result.personal_irr
            }
        
        return {
            'start_age_sensitivity': start_age_results,
            'salary_sensitivity': salary_results
        }