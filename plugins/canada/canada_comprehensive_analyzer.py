#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from typing import Dict, Any
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class CanadaTaxCalculator:
    """加拿大个人所得税计算器"""

    def __init__(self):
        self.country_code = 'CA'
        self.country_name = '加拿大'
        self.currency = 'CAD'

        # 加拿大个税税率表 (2024年)
        self.tax_brackets = [
            {'min': 0, 'max': 55867, 'rate': 0.15, 'quick_deduction': 0},
            {'min': 55867, 'max': 111733, 'rate': 0.205, 'quick_deduction': 3074},
            {'min': 111733, 'max': 173205, 'rate': 0.26, 'quick_deduction': 9871},
            {'min': 173205, 'max': 246752, 'rate': 0.29, 'quick_deduction': 17420},
            {'min': 246752, 'max': float('inf'), 'rate': 0.33, 'quick_deduction': 31220}
        ]

        # 加拿大CPP缴费率 (2024年)
        self.cpp_rates = {
            'employee': 0.0595,      # 员工CPP缴费率 5.95%
            'employer': 0.0595,      # 雇主CPP缴费率 5.95%
            'total': 0.119           # 总CPP缴费率 11.9%
        }

        # 加拿大EI缴费率 (2024年)
        self.ei_rates = {
            'employee': 0.0163,      # 员工EI缴费率 1.63%
            'employer': 0.0228,      # 雇主EI缴费率 2.28%
            'total': 0.0391          # 总EI缴费率 3.91%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算加拿大个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本个人免税额 (2024年)
        basic_personal_amount = 15000

        # CPP和EI扣除
        cpp_deduction = deductions.get('cpp_contribution', 0)
        ei_deduction = deductions.get('ei_contribution', 0)

        # 计算应纳税所得额
        taxable_income = annual_income - basic_personal_amount - cpp_deduction - ei_deduction

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': basic_personal_amount + cpp_deduction + ei_deduction,
                'breakdown': {
                    'basic_personal_amount': basic_personal_amount,
                    'cpp_deduction': cpp_deduction,
                    'ei_deduction': ei_deduction,
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
                        'bracket': f"C${bracket['min']:,.0f}-C${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': basic_personal_amount + cpp_deduction + ei_deduction,
            'breakdown': {
                'basic_personal_amount': basic_personal_amount,
                'cpp_deduction': cpp_deduction,
                'ei_deduction': ei_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_cpp_contribution(self, monthly_salary: float) -> Dict:
        """计算CPP缴费金额"""
        # CPP缴费上限 (2024年)
        cpp_ceiling = 66800 / 12  # 月薪上限

        # 计算缴费基数
        contribution_base = min(monthly_salary, cpp_ceiling)

        # 员工和雇主缴费
        employee_cpp = contribution_base * self.cpp_rates['employee']
        employer_cpp = contribution_base * self.cpp_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_cpp,
            'employer': employer_cpp,
            'total': employee_cpp + employer_cpp
        }

    def calculate_ei_contribution(self, monthly_salary: float) -> Dict:
        """计算EI缴费金额"""
        # EI缴费上限 (2024年)
        ei_ceiling = 63200 / 12  # 月薪上限

        # 计算缴费基数
        contribution_base = min(monthly_salary, ei_ceiling)

        # 员工和雇主缴费
        employee_ei = contribution_base * self.ei_rates['employee']
        employer_ei = contribution_base * self.ei_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_ei,
            'employer': employer_ei,
            'total': employee_ei + employer_ei
        }

class CanadaComprehensiveAnalyzer:
    """加拿大综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['CA']
        self.tax_calculator = CanadaTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 加拿大退休年龄
        self.retirement_age = 65

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析加拿大的情况"""
        print(f"\n{'='*80}")
        print(f"🇨🇦 加拿大综合分析")
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
            display_currency="CAD"
        )

        # 计算加拿大养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'CAD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'CAD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'CAD')}")
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

        # 转换月薪到加元（假设1 CNY = 0.19 CAD）
        monthly_salary_cad = monthly_salary_cny * 0.19
        print(f"月薪 (CAD): {converter.format_amount(monthly_salary_cad, 'CAD')}")

        # 计算CPP和EI缴费详情
        cpp_contribution = self.tax_calculator.calculate_cpp_contribution(monthly_salary_cad)
        ei_contribution = self.tax_calculator.calculate_ei_contribution(monthly_salary_cad)

        print(f"\nCPP缴费详情:")
        print(f"员工缴费: {converter.format_amount(cpp_contribution['employee'], 'CAD')}")
        print(f"雇主缴费: {converter.format_amount(cpp_contribution['employer'], 'CAD')}")
        print(f"总CPP缴费: {converter.format_amount(cpp_contribution['total'], 'CAD')}")

        print(f"\nEI缴费详情:")
        print(f"员工缴费: {converter.format_amount(ei_contribution['employee'], 'CAD')}")
        print(f"雇主缴费: {converter.format_amount(ei_contribution['employer'], 'CAD')}")
        print(f"总EI缴费: {converter.format_amount(ei_contribution['total'], 'CAD')}")

        # 计算个人所得税
        annual_income = monthly_salary_cad * 12

        # 设置扣除项
        deductions = {
            'cpp_contribution': cpp_contribution['employee'] * 12,
            'ei_contribution': ei_contribution['employee'] * 12,
        }

        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)

        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'CAD')}")
        print(f"CPP扣除: {converter.format_amount(deductions['cpp_contribution'], 'CAD')}")
        print(f"EI扣除: {converter.format_amount(deductions['ei_contribution'], 'CAD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'CAD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'CAD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'CAD')}")

        # 计算实际到手金额
        monthly_cpp = cpp_contribution['employee']
        monthly_ei = ei_contribution['employee']
        monthly_tax = tax_result['total_tax'] / 12

        monthly_net_income = monthly_salary_cad - monthly_cpp - monthly_ei - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0

        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_cad, 'CAD')}")
        print(f"CPP: -{converter.format_amount(monthly_cpp, 'CAD')}")
        print(f"EI: -{converter.format_amount(monthly_ei, 'CAD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'CAD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'CAD')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-65岁，35年)")
        print("-" * 50)

        # 计算35年的总收入
        total_income = 0
        total_cpp = 0
        total_ei = 0
        total_tax = 0
        total_net_income = 0

        for year in range(35):
            current_salary = monthly_salary_cny * (1.02 ** year) * 0.19 * 12  # 转换为加元

            # CPP和EI缴费
            monthly_cpp = self.tax_calculator.calculate_cpp_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.19
            )['employee']
            monthly_ei = self.tax_calculator.calculate_ei_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.19
            )['employee']

            annual_cpp = monthly_cpp * 12
            annual_ei = monthly_ei * 12

            # 个税
            deductions = {
                'cpp_contribution': annual_cpp,
                'ei_contribution': annual_ei,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']

            # 累计
            total_income += current_salary
            total_cpp += annual_cpp
            total_ei += annual_ei
            total_tax += annual_tax
            total_net_income += current_salary - annual_cpp - annual_ei - annual_tax

        print(f"35年总收入: {converter.format_amount(total_income, 'CAD')}")
        print(f"35年CPP缴费: {converter.format_amount(total_cpp, 'CAD')}")
        print(f"35年EI缴费: {converter.format_amount(total_ei, 'CAD')}")
        print(f"35年总个税: {converter.format_amount(total_tax, 'CAD')}")
        print(f"35年总净收入: {converter.format_amount(total_net_income, 'CAD')}")

        print(f"\n比例分析:")
        social_ratio = (total_cpp + total_ei) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0

        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (35 * 12)
        avg_monthly_social = (total_cpp + total_ei) / (35 * 12)
        avg_monthly_tax = total_tax / (35 * 12)
        avg_monthly_net = total_net_income / (35 * 12)

        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'CAD')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'CAD')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'CAD')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'CAD')}")

        print(f"\n{'='*80}")
