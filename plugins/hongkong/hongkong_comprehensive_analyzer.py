#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from typing import Dict, Any
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class HongKongTaxCalculator:
    """香港个人所得税计算器"""
    
    def __init__(self):
        self.country_code = 'HK'
        self.country_name = '香港'
        self.currency = 'HKD'
        
        # 香港个税税率表 (2024-25课税年度)
        self.tax_brackets = [
            {'min': 0, 'max': 50000, 'rate': 0.02, 'quick_deduction': 0},
            {'min': 50000, 'max': 100000, 'rate': 0.06, 'quick_deduction': 2000},
            {'min': 100000, 'max': 150000, 'rate': 0.10, 'quick_deduction': 6000},
            {'min': 150000, 'max': 200000, 'rate': 0.14, 'quick_deduction': 12000},
            {'min': 200000, 'max': float('inf'), 'rate': 0.17, 'quick_deduction': 20000}
        ]
        
        # 香港MPF缴费率 (2024年)
        self.mpf_rates = {
            'employee': 0.05,         # 员工MPF缴费率 5%
            'employer': 0.05,         # 雇主MPF缴费率 5%
            'total': 0.10             # 总MPF缴费率 10%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算香港个人所得税"""
        if deductions is None:
            deductions = {}
            
        # 基本免税额 (2024-25课税年度)
        basic_allowance = 132000
        
        # MPF扣除
        mpf_deduction = deductions.get('mpf_contribution', 0)
        
        # 计算应纳税所得额
        taxable_income = annual_income - basic_allowance - mpf_deduction
        
        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': basic_allowance + mpf_deduction,
                'breakdown': {
                    'basic_allowance': basic_allowance,
                    'mpf_deduction': mpf_deduction,
                    'tax_brackets': []
                }
            }
        
        # 计算个税
        total_tax = 0
        bracket_details = []
        
        for bracket in self.tax_brackets:
            if taxable_income > bracket['min']:
                bracket_taxable = min(taxable_income - bracket['min'],
                                    bracket['max'] - bracket['min'])
                
                if bracket_taxable > 0:
                    bracket_tax = bracket_taxable * bracket['rate']
                    total_tax += bracket_tax
                    
                    bracket_details.append({
                        'bracket': f"HK${bracket['min']:,.0f}-HK${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })
        
        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': basic_allowance + mpf_deduction,
            'breakdown': {
                'basic_allowance': basic_allowance,
                'mpf_deduction': mpf_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_mpf_contribution(self, monthly_salary: float) -> Dict:
        """计算MPF缴费金额"""
        # MPF缴费上限 (2024年)
        mpf_ceiling = 30000  # 月薪上限
        
        # 计算缴费基数
        contribution_base = min(monthly_salary, mpf_ceiling)
        
        # 员工和雇主缴费
        employee_mpf = contribution_base * self.mpf_rates['employee']
        employer_mpf = contribution_base * self.mpf_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_mpf,
            'employer': employer_mpf,
            'total': employee_mpf + employer_mpf
        }

class HongKongComprehensiveAnalyzer:
    """香港综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['HK']
        self.tax_calculator = HongKongTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 香港退休年龄
        self.retirement_age = 65

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析香港的情况"""
        print(f"\n{'='*80}")
        print(f"🇭🇰 香港综合分析")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: 2.0%")
        print(f"工作年限: 35年 (30岁-65岁)")
        print(f"{'='*80}")

        # 1. 养老金分析
        self._analyze_pension(monthly_salary_cny)

        # 2. 收入分析（社保+个税+实际到手）
        self._analyze_income(monthly_salary_cny)

        # 3. 全生命周期总结
        self._analyze_lifetime_summary(monthly_salary_cny)

    def _analyze_pension(self, monthly_salary_cny: float):
        """分析养老金情况"""
        print(f"\n🏦 养老金分析")
        print("-" * 50)

        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 创建工资档案 - 工资每年增长2%
        salary_profile = SalaryProfile(
            base_salary=monthly_salary_cny,
            annual_growth_rate=0.02
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="HKD"
        )

        # 计算香港养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'HKD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'HKD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'HKD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        print(f"\n缴费率信息:")
        print(f"总缴费率: 10.0%")
        print(f"员工缴费率: 5.0%")
        print(f"雇主缴费率: 5.0%")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到港币（假设1 CNY = 1.08 HKD）
        monthly_salary_hkd = monthly_salary_cny * 1.08
        print(f"月薪 (HKD): {converter.format_amount(monthly_salary_hkd, 'HKD')}")

        # 计算MPF缴费详情
        mpf_contribution = self.tax_calculator.calculate_mpf_contribution(monthly_salary_hkd)

        print(f"\nMPF缴费详情:")
        print(f"员工缴费: {converter.format_amount(mpf_contribution['employee'], 'HKD')}")
        print(f"雇主缴费: {converter.format_amount(mpf_contribution['employer'], 'HKD')}")
        print(f"总MPF缴费: {converter.format_amount(mpf_contribution['total'], 'HKD')}")

        # 计算个人所得税
        annual_income = monthly_salary_hkd * 12
        
        # 设置扣除项
        deductions = {
            'mpf_contribution': mpf_contribution['employee'] * 12,
        }
        
        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)
        
        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'HKD')}")
        print(f"MPF扣除: {converter.format_amount(deductions['mpf_contribution'], 'HKD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'HKD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'HKD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'HKD')}")

        # 计算实际到手金额
        monthly_mpf = mpf_contribution['employee']
        monthly_tax = tax_result['total_tax'] / 12
        
        monthly_net_income = monthly_salary_hkd - monthly_mpf - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0
        
        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_hkd, 'HKD')}")
        print(f"MPF: -{converter.format_amount(monthly_mpf, 'HKD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'HKD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'HKD')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-65岁，35年)")
        print("-" * 50)

        # 计算35年的总收入
        total_income = 0
        total_mpf = 0
        total_tax = 0
        total_net_income = 0
        
        for year in range(35):
            current_salary = monthly_salary_cny * (1.02 ** year) * 1.08 * 12  # 转换为港币
            
            # MPF缴费
            monthly_mpf = self.tax_calculator.calculate_mpf_contribution(
                monthly_salary_cny * (1.02 ** year) * 1.08
            )['employee']
            annual_mpf = monthly_mpf * 12
            
            # 个税
            deductions = {
                'mpf_contribution': annual_mpf,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']
            
            # 累计
            total_income += current_salary
            total_mpf += annual_mpf
            total_tax += annual_tax
            total_net_income += current_salary - annual_mpf - annual_tax

        print(f"35年总收入: {converter.format_amount(total_income, 'HKD')}")
        print(f"35年MPF缴费: {converter.format_amount(total_mpf, 'HKD')}")
        print(f"35年总个税: {converter.format_amount(total_tax, 'HKD')}")
        print(f"35年总净收入: {converter.format_amount(total_net_income, 'HKD')}")

        print(f"\n比例分析:")
        mpf_ratio = total_mpf / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0
        
        print(f"MPF占收入比例: {mpf_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (35 * 12)
        avg_monthly_mpf = total_mpf / (35 * 12)
        avg_monthly_tax = total_tax / (35 * 12)
        avg_monthly_net = total_net_income / (35 * 12)
        
        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'HKD')}")
        print(f"平均月MPF: {converter.format_amount(avg_monthly_mpf, 'HKD')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'HKD')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'HKD')}")

        print(f"\n{'='*80}")
