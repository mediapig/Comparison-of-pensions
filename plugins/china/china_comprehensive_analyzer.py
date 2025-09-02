#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer
from .china_tax_calculator import ChinaTaxCalculator

class ChinaComprehensiveAnalyzer:
    """中国综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['CN']
        self.tax_calculator = ChinaTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 中国退休年龄
        self.retirement_age = 63

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析中国的情况"""
        print(f"\n{'='*80}")
        print(f"🇨🇳 中国综合分析")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"年增长率: 2.0%")
        print(f"工作年限: 35年 (30岁-63岁)")
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
            display_currency="CNY"
        )

        # 计算中国养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'CNY')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'CNY')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'CNY')}")
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

        print(f"月薪 (CNY): {converter.format_amount(monthly_salary_cny, 'CNY')}")

        # 计算社保缴费详情
        social_security = self.tax_calculator.calculate_social_security_contribution(monthly_salary_cny)

        print(f"\n社保缴费详情:")
        print(f"员工缴费: {converter.format_amount(social_security['total'], 'CNY')}")
        print(f"雇主缴费: {converter.format_amount(monthly_salary_cny * 0.16, 'CNY')}")
        print(f"总社保缴费: {converter.format_amount(social_security['total'] + monthly_salary_cny * 0.16, 'CNY')}")

        # 计算个人所得税
        annual_income = monthly_salary_cny * 12

        # 设置专项附加扣除（不包含住房公积金）
        deductions = {
            'social_security': social_security['total'] * 12,  # 年社保扣除
            'education': 12000,      # 子女教育
            'housing': 12000,        # 住房租金/房贷利息
            'elderly': 24000,        # 赡养老人
        }

        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)

        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'CNY')}")
        print(f"社保扣除: {converter.format_amount(deductions['social_security'], 'CNY')}")
        print(f"专项附加扣除: {converter.format_amount(deductions['education'] + deductions['housing'] + deductions['elderly'], 'CNY')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'CNY')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'CNY')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'CNY')}")

        # 计算实际到手金额（不包含住房公积金）
        monthly_social_security = social_security['total']
        monthly_tax = tax_result['total_tax'] / 12

        monthly_net_income = monthly_salary_cny - monthly_social_security - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0

        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_cny, 'CNY')}")
        print(f"社保: -{converter.format_amount(monthly_social_security, 'CNY')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'CNY')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'CNY')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-63岁，33年)")
        print("-" * 50)

        # 计算33年的总收入
        total_income = 0
        total_social_security = 0
        total_employer_social = 0
        total_tax = 0
        total_net_income = 0

        for year in range(33):
            current_salary = monthly_salary_cny * (1.02 ** year) * 12

            # 社保缴费
            monthly_social = self.tax_calculator.calculate_social_security_contribution(
                monthly_salary_cny * (1.02 ** year)
            )['total']
            annual_social = monthly_social * 12

            # 个税（不包含住房公积金）
            deductions = {
                'social_security': annual_social,
                'education': 12000,
                'housing': 12000,
                'elderly': 24000,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']

            # 累计
            total_income += current_salary
            total_social_security += annual_social
            total_employer_social += current_salary * 0.16
            total_tax += annual_tax
            total_net_income += current_salary - annual_social - annual_tax

        print(f"33年总收入: {converter.format_amount(total_income, 'CNY')}")
        print(f"33年员工社保: {converter.format_amount(total_social_security, 'CNY')}")
        print(f"33年单位社保: {converter.format_amount(total_employer_social, 'CNY')}")
        print(f"33年总个税: {converter.format_amount(total_tax, 'CNY')}")
        print(f"33年总净收入: {converter.format_amount(total_net_income, 'CNY')}")

        print(f"\n比例分析:")
        social_ratio = (total_social_security + total_employer_social) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0

        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (33 * 12)
        avg_monthly_social = (total_social_security + total_employer_social) / (33 * 12)
        avg_monthly_tax = total_tax / (33 * 12)
        avg_monthly_net = total_net_income / (33 * 12)

        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'CNY')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'CNY')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'CNY')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'CNY')}")

        print(f"\n{'='*80}")
