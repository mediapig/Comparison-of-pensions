#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class AustraliaTaxCalculator:
    """澳大利亚个人所得税计算器"""
    
    def __init__(self):
        self.country_code = 'AU'
        self.country_name = '澳大利亚'
        self.currency = 'AUD'
        
        # 澳大利亚个税税率表 (2024-25财年)
        self.tax_brackets = [
            {'min': 0, 'max': 18200, 'rate': 0.0, 'quick_deduction': 0},
            {'min': 18200, 'max': 45000, 'rate': 0.19, 'quick_deduction': 0},
            {'min': 45000, 'max': 135000, 'rate': 0.325, 'quick_deduction': 5092},
            {'min': 135000, 'max': 190000, 'rate': 0.37, 'quick_deduction': 29467},
            {'min': 190000, 'max': float('inf'), 'rate': 0.45, 'quick_deduction': 51667}
        ]
        
        # 澳大利亚Superannuation缴费率 (2024-25财年)
        self.super_rates = {
            'employee': 0.0,         # 员工Super缴费率 0% (雇主承担)
            'employer': 0.115,       # 雇主Super缴费率 11.5%
            'total': 0.115           # 总Super缴费率 11.5%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算澳大利亚个人所得税"""
        if deductions is None:
            deductions = {}
            
        # 基本个人免税额 (2024-25财年)
        basic_personal_amount = 18200
        
        # 计算应纳税所得额
        taxable_income = annual_income - basic_personal_amount
        
        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': basic_personal_amount,
                'breakdown': {
                    'basic_personal_amount': basic_personal_amount,
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
                        'bracket': f"A${bracket['min']:,.0f}-A${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })
        
        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': basic_personal_amount,
            'breakdown': {
                'basic_personal_amount': basic_personal_amount,
                'tax_brackets': bracket_details
            }
        }

    def calculate_super_contribution(self, monthly_salary: float) -> Dict:
        """计算Superannuation缴费金额"""
        # 计算缴费基数
        contribution_base = monthly_salary
        
        # 员工和雇主缴费
        employee_super = contribution_base * self.super_rates['employee']
        employer_super = contribution_base * self.super_rates['employer']
        
        return {
            'contribution_base': contribution_base,
            'employee': employee_super,
            'employer': employer_super,
            'total': employee_super + employer_super
        }

class AustraliaComprehensiveAnalyzer:
    """澳大利亚综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['AU']
        self.tax_calculator = AustraliaTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 澳大利亚退休年龄
        self.retirement_age = 67

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析澳大利亚的情况"""
        print(f"\n{'='*80}")
        print(f"🇦🇺 澳大利亚综合分析")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: 2.0%")
        print(f"工作年限: 37年 (30岁-67岁)")
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
            display_currency="AUD"
        )

        # 计算澳大利亚养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'AUD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'AUD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'AUD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        contribution_rates = self.calculator.contribution_rates
        print(f"\n缴费率信息:")
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到澳元（假设1 CNY = 0.21 AUD）
        monthly_salary_aud = monthly_salary_cny * 0.21
        print(f"月薪 (AUD): {converter.format_amount(monthly_salary_aud, 'AUD')}")

        # 计算Superannuation缴费详情
        super_contribution = self.tax_calculator.calculate_super_contribution(monthly_salary_aud)

        print(f"\nSuperannuation缴费详情:")
        print(f"员工缴费: {converter.format_amount(super_contribution['employee'], 'AUD')}")
        print(f"雇主缴费: {converter.format_amount(super_contribution['employer'], 'AUD')}")
        print(f"总Super缴费: {converter.format_amount(super_contribution['total'], 'AUD')}")

        # 计算个人所得税
        annual_income = monthly_salary_aud * 12
        
        tax_result = self.tax_calculator.calculate_income_tax(annual_income)
        
        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'AUD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'AUD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'AUD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'AUD')}")

        # 计算实际到手金额
        monthly_super = super_contribution['employee']
        monthly_tax = tax_result['total_tax'] / 12
        
        monthly_net_income = monthly_salary_aud - monthly_super - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0
        
        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_aud, 'AUD')}")
        print(f"Super: -{converter.format_amount(monthly_super, 'AUD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'AUD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'AUD')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-67岁，37年)")
        print("-" * 50)

        # 计算37年的总收入
        total_income = 0
        total_super = 0
        total_tax = 0
        total_net_income = 0
        
        for year in range(37):
            current_salary = monthly_salary_cny * (1.02 ** year) * 0.21 * 12  # 转换为澳元
            
            # Super缴费
            monthly_super = self.tax_calculator.calculate_super_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.21
            )['employee']
            annual_super = monthly_super * 12
            
            # 个税
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary)['total_tax']
            
            # 累计
            total_income += current_salary
            total_super += annual_super
            total_tax += annual_tax
            total_net_income += current_salary - annual_super - annual_tax

        print(f"37年总收入: {converter.format_amount(total_income, 'AUD')}")
        print(f"37年Super缴费: {converter.format_amount(total_super, 'AUD')}")
        print(f"37年总个税: {converter.format_amount(total_tax, 'AUD')}")
        print(f"37年总净收入: {converter.format_amount(total_net_income, 'AUD')}")

        print(f"\n比例分析:")
        super_ratio = total_super / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0
        
        print(f"Super占收入比例: {super_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (37 * 12)
        avg_monthly_super = total_super / (37 * 12)
        avg_monthly_tax = total_tax / (37 * 12)
        avg_monthly_net = total_net_income / (37 * 12)
        
        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'AUD')}")
        print(f"平均月Super: {converter.format_amount(avg_monthly_super, 'AUD')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'AUD')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'AUD')}")

        print(f"\n{'='*80}")
