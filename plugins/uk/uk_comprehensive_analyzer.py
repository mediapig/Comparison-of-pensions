#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英国综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from typing import Dict, Any
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class UKTaxCalculator:
    """英国个人所得税计算器"""
    
    def __init__(self):
        self.country_code = 'UK'
        self.country_name = '英国'
        self.currency = 'GBP'
        
        # 英国个税税率表 (2024-25财年)
        self.tax_brackets = [
            {'min': 0, 'max': 12570, 'rate': 0.0, 'quick_deduction': 0},
            {'min': 12570, 'max': 50270, 'rate': 0.20, 'quick_deduction': 0},
            {'min': 50270, 'max': 125140, 'rate': 0.40, 'quick_deduction': 7540},
            {'min': 125140, 'max': float('inf'), 'rate': 0.45, 'quick_deduction': 27290}
        ]
        
        # 英国National Insurance缴费率 (2024-25财年)
        self.ni_rates = {
            'employee': 0.12,         # 员工NI缴费率 12%
            'employer': 0.138,        # 雇主NI缴费率 13.8%
            'total': 0.258            # 总NI缴费率 25.8%
        }
        
        # 英国养老金缴费率 (2024-25财年)
        self.pension_rates = {
            'employee': 0.05,         # 员工养老金缴费率 5%
            'employer': 0.03,         # 雇主养老金缴费率 3%
            'total': 0.08             # 总养老金缴费率 8%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算英国个人所得税"""
        if deductions is None:
            deductions = {}
            
        # 个人免税额 (2024-25财年)
        personal_allowance = 12570
        
        # 养老金扣除
        pension_deduction = deductions.get('pension_contribution', 0)
        
        # 计算应纳税所得额
        taxable_income = annual_income - personal_allowance - pension_deduction
        
        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': personal_allowance + pension_deduction,
                'breakdown': {
                    'personal_allowance': personal_allowance,
                    'pension_deduction': pension_deduction,
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
                        'bracket': f"£{bracket['min']:,.0f}-£{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })
        
        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': personal_allowance + pension_deduction,
            'breakdown': {
                'personal_allowance': personal_allowance,
                'pension_deduction': pension_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_ni_contribution(self, monthly_salary: float) -> Dict:
        """计算National Insurance缴费金额"""
        # NI缴费基数上下限 (2024-25财年)
        min_base = 1048   # 最低基数
        max_base = 4189   # 最高基数
        
        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))
        
        # 员工和雇主缴费
        employee_ni = contribution_base * self.ni_rates['employee']
        employer_ni = contribution_base * self.ni_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_ni,
            'employer': employer_ni,
            'total': employee_ni + employer_ni
        }

    def calculate_pension_contribution(self, monthly_salary: float) -> Dict:
        """计算养老金缴费金额"""
        # 养老金缴费基数上下限 (2024-25财年)
        min_base = 6240 / 12   # 最低基数
        max_base = 50270 / 12  # 最高基数
        
        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))
        
        # 员工和雇主缴费
        employee_pension = contribution_base * self.pension_rates['employee']
        employer_pension = contribution_base * self.pension_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_pension,
            'employer': employer_pension,
            'total': employee_pension + employer_pension
        }

class UKComprehensiveAnalyzer:
    """英国综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['UK']
        self.tax_calculator = UKTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 英国退休年龄
        self.retirement_age = 68

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析英国的情况"""
        print(f"\n{'='*80}")
        print(f"🇬🇧 英国综合分析")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: 2.0%")
        print(f"工作年限: 38年 (30岁-68岁)")
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
            display_currency="GBP"
        )

        # 计算英国养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'GBP')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'GBP')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'GBP')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        print(f"\n缴费率信息:")
        print(f"总缴费率: 33.8%")
        print(f"员工缴费率: 17.0%")
        print(f"雇主缴费率: 16.8%")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到英镑（假设1 CNY = 0.11 GBP）
        monthly_salary_gbp = monthly_salary_cny * 0.11
        print(f"月薪 (GBP): {converter.format_amount(monthly_salary_gbp, 'GBP')}")

        # 计算National Insurance和养老金缴费详情
        ni_contribution = self.tax_calculator.calculate_ni_contribution(monthly_salary_gbp)
        pension_contribution = self.tax_calculator.calculate_pension_contribution(monthly_salary_gbp)

        print(f"\nNational Insurance缴费详情:")
        print(f"员工缴费: {converter.format_amount(ni_contribution['employee'], 'GBP')}")
        print(f"雇主缴费: {converter.format_amount(ni_contribution['employer'], 'GBP')}")
        print(f"总NI缴费: {converter.format_amount(ni_contribution['total'], 'GBP')}")

        print(f"\n养老金缴费详情:")
        print(f"员工缴费: {converter.format_amount(pension_contribution['employee'], 'GBP')}")
        print(f"雇主缴费: {converter.format_amount(pension_contribution['employer'], 'GBP')}")
        print(f"总养老金缴费: {converter.format_amount(pension_contribution['total'], 'GBP')}")

        # 计算个人所得税
        annual_income = monthly_salary_gbp * 12
        
        # 设置扣除项
        deductions = {
            'pension_contribution': pension_contribution['employee'] * 12,
        }
        
        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)
        
        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'GBP')}")
        print(f"养老金扣除: {converter.format_amount(deductions['pension_contribution'], 'GBP')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'GBP')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'GBP')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'GBP')}")

        # 计算实际到手金额
        monthly_ni = ni_contribution['employee']
        monthly_pension = pension_contribution['employee']
        monthly_tax = tax_result['total_tax'] / 12
        
        monthly_net_income = monthly_salary_gbp - monthly_ni - monthly_pension - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0
        
        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_gbp, 'GBP')}")
        print(f"NI: -{converter.format_amount(monthly_ni, 'GBP')}")
        print(f"养老金: -{converter.format_amount(monthly_pension, 'GBP')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'GBP')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'GBP')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-68岁，38年)")
        print("-" * 50)

        # 计算38年的总收入
        total_income = 0
        total_ni = 0
        total_pension = 0
        total_tax = 0
        total_net_income = 0
        
        for year in range(38):
            current_salary = monthly_salary_cny * (1.02 ** year) * 0.11 * 12  # 转换为英镑
            
            # NI和养老金缴费
            monthly_ni = self.tax_calculator.calculate_ni_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.11
            )['employee']
            monthly_pension = self.tax_calculator.calculate_pension_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.11
            )['employee']
            
            annual_ni = monthly_ni * 12
            annual_pension = monthly_pension * 12
            
            # 个税
            deductions = {
                'pension_contribution': annual_pension,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']
            
            # 累计
            total_income += current_salary
            total_ni += annual_ni
            total_pension += annual_pension
            total_tax += annual_tax
            total_net_income += current_salary - annual_ni - annual_pension - annual_tax

        print(f"38年总收入: {converter.format_amount(total_income, 'GBP')}")
        print(f"38年NI缴费: {converter.format_amount(total_ni, 'GBP')}")
        print(f"38年养老金缴费: {converter.format_amount(total_pension, 'GBP')}")
        print(f"38年总个税: {converter.format_amount(total_tax, 'GBP')}")
        print(f"38年总净收入: {converter.format_amount(total_net_income, 'GBP')}")

        print(f"\n比例分析:")
        social_ratio = (total_ni + total_pension) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0
        
        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (38 * 12)
        avg_monthly_social = (total_ni + total_pension) / (38 * 12)
        avg_monthly_tax = total_tax / (38 * 12)
        avg_monthly_net = total_net_income / (38 * 12)
        
        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'GBP')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'GBP')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'GBP')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'GBP')}")

        print(f"\n{'='*80}")
