#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer

class USATaxCalculator:
    """美国个人所得税计算器"""

    def __init__(self):
        self.country_code = 'US'
        self.country_name = '美国'
        self.currency = 'USD'

        # 美国个税税率表 (2024年)
        self.tax_brackets = [
            {'min': 0, 'max': 11600, 'rate': 0.10, 'quick_deduction': 0},
            {'min': 11600, 'max': 47150, 'rate': 0.12, 'quick_deduction': 1160},
            {'min': 47150, 'max': 100525, 'rate': 0.22, 'quick_deduction': 5423},
            {'min': 100525, 'max': 191950, 'rate': 0.24, 'quick_deduction': 17169},
            {'min': 191950, 'max': 243725, 'rate': 0.32, 'quick_deduction': 39497},
            {'min': 243725, 'max': 609350, 'rate': 0.35, 'quick_deduction': 55962},
            {'min': 609350, 'max': float('inf'), 'rate': 0.37, 'quick_deduction': 183206}
        ]

        # 美国Social Security缴费率 (2024年)
        self.ss_rates = {
            'employee': 0.062,        # 员工SS缴费率 6.2%
            'employer': 0.062,        # 雇主SS缴费率 6.2%
            'total': 0.124           # 总SS缴费率 12.4%
        }

        # 美国Medicare缴费率 (2024年)
        self.medicare_rates = {
            'employee': 0.0145,       # 员工Medicare缴费率 1.45%
            'employer': 0.0145,       # 雇主Medicare缴费率 1.45%
            'total': 0.029           # 总Medicare缴费率 2.9%
        }

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算美国个人所得税"""
        if deductions is None:
            deductions = {}

        # 标准扣除额 (2024年)
        standard_deduction = 14600

        # Social Security和Medicare扣除
        ss_deduction = deductions.get('ss_contribution', 0)
        medicare_deduction = deductions.get('medicare_contribution', 0)

        # 计算应纳税所得额
        taxable_income = annual_income - standard_deduction - ss_deduction - medicare_deduction

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': standard_deduction + ss_deduction + medicare_deduction,
                'breakdown': {
                    'standard_deduction': standard_deduction,
                    'ss_deduction': ss_deduction,
                    'medicare_deduction': medicare_deduction,
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
                        'bracket': f"${bracket['min']:,.0f}-${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': standard_deduction + ss_deduction + medicare_deduction,
            'breakdown': {
                'standard_deduction': standard_deduction,
                'ss_deduction': ss_deduction,
                'medicare_deduction': medicare_deduction,
                'tax_brackets': bracket_details
            }
        }

    def calculate_ss_contribution(self, monthly_salary: float) -> Dict:
        """计算Social Security缴费金额"""
        # SS缴费上限 (2024年)
        ss_ceiling = 168600 / 12  # 月薪上限

        # 计算缴费基数
        contribution_base = min(monthly_salary, ss_ceiling)

        # 员工和雇主缴费
        employee_ss = contribution_base * self.ss_rates['employee']
        employer_ss = contribution_base * self.ss_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_ss,
            'employer': employer_ss,
            'total': employee_ss + employer_ss
        }

    def calculate_medicare_contribution(self, monthly_salary: float) -> Dict:
        """计算Medicare缴费金额"""
        # 计算缴费基数
        contribution_base = monthly_salary

        # 员工和雇主缴费
        employee_medicare = contribution_base * self.medicare_rates['employee']
        employer_medicare = contribution_base * self.medicare_rates['employer']

        return {
            'contribution_base': contribution_base,
            'employee': employee_medicare,
            'employer': employer_medicare,
            'total': employee_medicare + employer_medicare
        }

class USAComprehensiveAnalyzer:
    """美国综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['US']
        self.tax_calculator = USATaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 美国退休年龄
        self.retirement_age = 67

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析美国的情况"""
        print(f"\n{'='*80}")
        print(f"🇺🇸 美国综合分析")
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
            display_currency="USD"
        )

        # 计算美国养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'USD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'USD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'USD')}")
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

        # 转换月薪到美元（假设1 CNY = 0.14 USD）
        monthly_salary_usd = monthly_salary_cny * 0.14
        print(f"月薪 (USD): {converter.format_amount(monthly_salary_usd, 'USD')}")

        # 计算Social Security和Medicare缴费详情
        ss_contribution = self.tax_calculator.calculate_ss_contribution(monthly_salary_usd)
        medicare_contribution = self.tax_calculator.calculate_medicare_contribution(monthly_salary_usd)

        print(f"\nSocial Security缴费详情:")
        print(f"员工缴费: {converter.format_amount(ss_contribution['employee'], 'USD')}")
        print(f"雇主缴费: {converter.format_amount(ss_contribution['employer'], 'USD')}")
        print(f"总SS缴费: {converter.format_amount(ss_contribution['total'], 'USD')}")

        print(f"\nMedicare缴费详情:")
        print(f"员工缴费: {converter.format_amount(medicare_contribution['employee'], 'USD')}")
        print(f"雇主缴费: {converter.format_amount(medicare_contribution['employer'], 'USD')}")
        print(f"总Medicare缴费: {converter.format_amount(medicare_contribution['total'], 'USD')}")

        # 计算个人所得税
        annual_income = monthly_salary_usd * 12

        # 设置扣除项
        deductions = {
            'ss_contribution': ss_contribution['employee'] * 12,
            'medicare_contribution': medicare_contribution['employee'] * 12,
        }

        tax_result = self.tax_calculator.calculate_income_tax(annual_income, deductions)

        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income, 'USD')}")
        print(f"SS扣除: {converter.format_amount(deductions['ss_contribution'], 'USD')}")
        print(f"Medicare扣除: {converter.format_amount(deductions['medicare_contribution'], 'USD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'USD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'USD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'USD')}")

        # 计算实际到手金额
        monthly_ss = ss_contribution['employee']
        monthly_medicare = medicare_contribution['employee']
        monthly_tax = tax_result['total_tax'] / 12

        monthly_net_income = monthly_salary_usd - monthly_ss - monthly_medicare - monthly_tax
        effective_tax_rate = (tax_result['total_tax'] / annual_income * 100) if annual_income > 0 else 0

        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_usd, 'USD')}")
        print(f"SS: -{converter.format_amount(monthly_ss, 'USD')}")
        print(f"Medicare: -{converter.format_amount(monthly_medicare, 'USD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'USD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'USD')}")
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-67岁，37年)")
        print("-" * 50)

        # 计算37年的总收入
        total_income = 0
        total_ss = 0
        total_medicare = 0
        total_tax = 0
        total_net_income = 0

        for year in range(37):
            current_salary = monthly_salary_cny * (1.02 ** year) * 0.14 * 12  # 转换为美元

            # SS和Medicare缴费
            monthly_ss = self.tax_calculator.calculate_ss_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.14
            )['employee']
            monthly_medicare = self.tax_calculator.calculate_medicare_contribution(
                monthly_salary_cny * (1.02 ** year) * 0.14
            )['employee']

            annual_ss = monthly_ss * 12
            annual_medicare = monthly_medicare * 12

            # 个税
            deductions = {
                'ss_contribution': annual_ss,
                'medicare_contribution': annual_medicare,
            }
            annual_tax = self.tax_calculator.calculate_income_tax(current_salary, deductions)['total_tax']

            # 累计
            total_income += current_salary
            total_ss += annual_ss
            total_medicare += annual_medicare
            total_tax += annual_tax
            total_net_income += current_salary - annual_ss - annual_medicare - annual_tax

        print(f"37年总收入: {converter.format_amount(total_income, 'USD')}")
        print(f"37年SS缴费: {converter.format_amount(total_ss, 'USD')}")
        print(f"37年Medicare缴费: {converter.format_amount(total_medicare, 'USD')}")
        print(f"37年总个税: {converter.format_amount(total_tax, 'USD')}")
        print(f"37年总净收入: {converter.format_amount(total_net_income, 'USD')}")

        print(f"\n比例分析:")
        social_ratio = (total_ss + total_medicare) / total_income * 100 if total_income > 0 else 0
        tax_ratio = total_tax / total_income * 100 if total_income > 0 else 0
        net_ratio = total_net_income / total_income * 100 if total_income > 0 else 0

        print(f"社保占收入比例: {social_ratio:.1f}%")
        print(f"个税占收入比例: {tax_ratio:.1f}%")
        print(f"净收入占收入比例: {net_ratio:.1f}%")

        print(f"\n月平均值:")
        avg_monthly_income = total_income / (37 * 12)
        avg_monthly_social = (total_ss + total_medicare) / (37 * 12)
        avg_monthly_tax = total_tax / (37 * 12)
        avg_monthly_net = total_net_income / (37 * 12)

        print(f"平均月收入: {converter.format_amount(avg_monthly_income, 'USD')}")
        print(f"平均月社保: {converter.format_amount(avg_monthly_social, 'USD')}")
        print(f"平均月个税: {converter.format_amount(avg_monthly_tax, 'USD')}")
        print(f"平均月净收入: {converter.format_amount(avg_monthly_net, 'USD')}")

        print(f"\n{'='*80}")
