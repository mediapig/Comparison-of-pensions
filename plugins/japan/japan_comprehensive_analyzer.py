#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from typing import Dict, Any
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class JapanTaxCalculator:
    """日本个人所得税计算器"""

    def __init__(self):
        self.country_code = 'JP'
        self.country_name = '日本'
        self.currency = 'JPY'

        # 日本个税税率表 (2024年)
        self.tax_brackets = [
            {'min': 0, 'max': 1950000, 'rate': 0.05, 'quick_deduction': 0},
            {'min': 1950000, 'max': 3300000, 'rate': 0.10, 'quick_deduction': 97500},
            {'min': 3300000, 'max': 6950000, 'rate': 0.20, 'quick_deduction': 427500},
            {'min': 6950000, 'max': 9000000, 'rate': 0.23, 'quick_deduction': 636000},
            {'min': 9000000, 'max': 18000000, 'rate': 0.33, 'quick_deduction': 1536000},
            {'min': 18000000, 'max': 40000000, 'rate': 0.40, 'quick_deduction': 2796000},
            {'min': 40000000, 'max': float('inf'), 'rate': 0.45, 'quick_deduction': 4796000}
        ]

        # 日本厚生年金缴费率 (2024年)
        self.pension_rates = {
            'employee': 0.0915,        # 员工厚生年金缴费率 9.15%
            'employer': 0.0915,        # 雇主厚生年金缴费率 9.15%
            'total': 0.183             # 总厚生年金缴费率 18.3%
        }

        # 日本健康保险缴费率 (2024年)
        self.health_insurance_rates = {
            'employee': 0.0495,        # 员工健康保险缴费率 4.95%
            'employer': 0.0495,        # 雇主健康保险缴费率 4.95%
            'total': 0.099             # 总健康保险缴费率 9.9%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算日本个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本控除 (2024年)
        basic_deduction = 480000

        # 厚生年金和健康保险扣除
        pension_deduction = deductions.get('pension_contribution', 0)
        health_deduction = deductions.get('health_insurance_contribution', 0)

        # 计算应纳税所得额
        taxable_income = annual_income - basic_deduction - pension_deduction - health_deduction

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': basic_deduction + pension_deduction + health_deduction,
                'breakdown': {
                    'basic_deduction': basic_deduction,
                    'pension_deduction': pension_deduction,
                    'health_deduction': health_deduction,
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
                        'bracket': f"¥{bracket['min']:,.0f}-¥{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': basic_deduction + pension_deduction + health_deduction,
            'breakdown': {
                'basic_deduction': basic_deduction,
                'pension_deduction': pension_deduction,
                'health_deduction': health_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_pension_contribution(self, monthly_salary: float) -> Dict:
        """计算厚生年金缴费金额"""
        # 厚生年金缴费基数上下限 (2024年)
        min_base = 98000    # 最低基数
        max_base = 650000   # 最高基数

        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))

        # 员工和雇主缴费
        employee_contribution = contribution_base * self.pension_rates['employee']
        employer_contribution = contribution_base * self.pension_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_contribution,
            'employer': employer_contribution,
            'total': employee_contribution + employer_contribution
        }

    def calculate_health_insurance_contribution(self, monthly_salary: float) -> Dict:
        """计算健康保险缴费金额"""
        # 健康保险缴费基数上下限 (2024年)
        min_base = 98000    # 最低基数
        max_base = 1380000  # 最高基数

        # 计算缴费基数
        contribution_base = max(min_base, min(monthly_salary, max_base))

        # 员工和雇主缴费
        employee_contribution = contribution_base * self.health_insurance_rates['employee']
        employer_contribution = contribution_base * self.health_insurance_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_contribution,
            'employer': employer_contribution,
            'total': employee_contribution + employer_contribution
        }

class JapanComprehensiveAnalyzer:
    """日本综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['JP']
        self.tax_calculator = JapanTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 日本退休年龄
        self.retirement_age = 65

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析日本的情况"""
        print(f"\n{'='*80}")
        print(f"🇯🇵 日本综合分析")
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
            display_currency="JPY"
        )

        # 计算日本养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'JPY')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'JPY')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'JPY')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        print(f"\n缴费率信息:")
        print(f"总缴费率: 28.2%")
        print(f"员工缴费率: 14.1%")
        print(f"雇主缴费率: 14.1%")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到日元（假设1 CNY = 20.5 JPY）
        monthly_salary_jpy = monthly_salary_cny * 20.5
        print(f"月薪 (JPY): {converter.format_amount(monthly_salary_jpy, 'JPY')}")

        # 计算厚生年金和健康保险缴费详情
        pension_contribution = self.tax_calculator.calculate_pension_contribution(monthly_salary_jpy)
        health_insurance = self.tax_calculator.calculate_health_insurance_contribution(monthly_salary_jpy)

        print(f"\n厚生年金缴费详情:")
        print(f"员工缴费: {converter.format_amount(pension_contribution['employee'], 'JPY')}")
        print(f"雇主缴费: {converter.format_amount(pension_contribution['employer'], 'JPY')}")
        print(f"总厚生年金缴费: {converter.format_amount(pension_contribution['total'], 'JPY')}")

        print(f"\n健康保险缴费详情:")
        print(f"员工缴费: {converter.format_amount(health_insurance['employee'], 'JPY')}")
        print(f"雇主缴费: {converter.format_amount(health_insurance['employer'], 'JPY')}")
        print(f"总健康保险缴费: {converter.format_amount(health_insurance['total'], 'JPY')}")

        # 计算个人所得税
        annual_income = monthly_salary_jpy * 12

        # 设置扣除项
        deductions = {
            'pension_contribution': pension_contribution['employee'] * 12,
            'health_insurance_contribution': health_insurance['employee'] * 12,
        }

        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)

        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'JPY')}")
        print(f"厚生年金扣除: {converter.format_amount(deductions['pension_contribution'], 'JPY')}")
        print(f"健康保险扣除: {converter.format_amount(deductions['health_insurance_contribution'], 'JPY')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'JPY')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'JPY')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'JPY')}")

        # 计算实际到手金额
        monthly_pension = pension_contribution['employee']
        monthly_health = health_insurance['employee']
        monthly_tax = tax_result['total_tax'] / 12

        monthly_net_income = monthly_salary_jpy - monthly_pension - monthly_health - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0

        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_jpy, 'JPY')}")
        print(f"厚生年金: -{converter.format_amount(monthly_pension, 'JPY')}")
        print(f"健康保险: -{converter.format_amount(monthly_health, 'JPY')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'JPY')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'JPY')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-65岁，35年)")
        print("-" * 50)

        # 计算35年的总收入
        total_income = 0
        total_pension = 0
        total_health = 0
        total_tax = 0
        total_net_income = 0

        for year in range(35):
            current_salary = monthly_salary_cny * (1.02 ** year) * 20.5 * 12  # 转换为日元

            # 厚生年金和健康保险缴费
            monthly_pension = self.tax_calculator.calculate_pension_contribution(
                monthly_salary_cny * (1.02 ** year) * 20.5
            )['employee']
            monthly_health = self.tax_calculator.calculate_health_insurance_contribution(
                monthly_salary_cny * (1.02 ** year) * 20.5
            )['employee']

            annual_pension = monthly_pension * 12
            annual_health = monthly_health * 12

            # 个税
            deductions = {
                'pension_contribution': annual_pension,
                'health_insurance_contribution': annual_health,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']

            # 累计
            total_income += current_salary
            total_pension += annual_pension
            total_health += annual_health
            total_tax += annual_tax
            total_net_income += current_salary - annual_pension - annual_health - annual_tax

        print(f"35年总收入: {converter.format_amount(total_income, 'JPY')}")
        print(f"35年厚生年金缴费: {converter.format_amount(total_pension, 'JPY')}")
        print(f"35年健康保险缴费: {converter.format_amount(total_health, 'JPY')}")
        print(f"35年总个税: {converter.format_amount(total_tax, 'JPY')}")
        print(f"35年总净收入: {converter.format_amount(total_net_income, 'JPY')}")

        print(f"\n比例分析:")
        social_ratio = (total_pension + total_health) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0

        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (35 * 12)
        avg_monthly_social = (total_pension + total_health) / (35 * 12)
        avg_monthly_tax = total_tax / (35 * 12)
        avg_monthly_net = total_net_income / (35 * 12)

        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'JPY')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'JPY')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'JPY')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'JPY')}")

        print(f"\n{'='*80}")
