#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡综合分析器
包含养老金、社保、个税和实际到手金额的完整分析
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter
from utils.income_analyzer import IncomeAnalyzer
from .singapore_tax_calculator import SingaporeTaxCalculator

class SingaporeComprehensiveAnalyzer:
    """新加坡综合分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['SG']
        self.tax_calculator = SingaporeTaxCalculator()
        self.income_analyzer = IncomeAnalyzer()

        # 新加坡退休年龄
        self.retirement_age = 65

    def analyze_comprehensive(self, monthly_salary_cny: float):
        """综合分析新加坡的情况"""
        print(f"\n{'='*80}")
        print(f"🇸🇬 新加坡综合分析")
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
            display_currency="SGD"
        )

        # 计算新加坡养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示养老金结果
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'SGD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'SGD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'SGD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示CPF详情
        contribution_rates = self.calculator.contribution_rates
        print(f"\nCPF缴费率信息:")
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    def _analyze_income(self, monthly_salary_cny: float):
        """分析收入情况（社保+个税+实际到手）"""
        print(f"\n💰 收入分析")
        print("-" * 50)

        # 转换月薪到新加坡元（假设1 CNY = 0.19 SGD）
        monthly_salary_sgd = monthly_salary_cny * 0.19

        print(f"月薪 (SGD): {converter.format_amount(monthly_salary_sgd, 'SGD')}")

        # 计算CPF缴费
        cpf_result = self.tax_calculator.calculate_cpf_contribution(monthly_salary_sgd)

        print(f"\nCPF缴费详情:")
        print(f"员工缴费: {converter.format_amount(cpf_result['employee']['total'], 'SGD')}")
        print(f"雇主缴费: {converter.format_amount(cpf_result['employer']['total'], 'SGD')}")
        print(f"总CPF缴费: {converter.format_amount(cpf_result['total'], 'SGD')}")

        # 计算年收入
        annual_income_sgd = monthly_salary_sgd * 12

        # 计算个税（考虑CPF扣除）
        tax_result = self.tax_calculator.calculate_income_tax(
            annual_income_sgd,
            {'cpf_contribution': cpf_result['total'] * 12}
        )

        print(f"\n个人所得税:")
        print(f"年收入: {converter.format_amount(annual_income_sgd, 'SGD')}")
        print(f"CPF扣除: {converter.format_amount(tax_result['total_deductions'], 'SGD')}")
        print(f"应纳税所得额: {converter.format_amount(tax_result['taxable_income'], 'SGD')}")
        print(f"年个税: {converter.format_amount(tax_result['total_tax'], 'SGD')}")
        print(f"月个税: {converter.format_amount(tax_result['total_tax'] / 12, 'SGD')}")

        # 计算实际到手金额
        monthly_tax = tax_result['total_tax'] / 12
        monthly_net_income = monthly_salary_sgd - cpf_result['employee']['total'] - monthly_tax

        print(f"\n实际到手金额:")
        print(f"月薪: {converter.format_amount(monthly_salary_sgd, 'SGD')}")
        print(f"员工CPF: -{converter.format_amount(cpf_result['employee']['total'], 'SGD')}")
        print(f"月个税: -{converter.format_amount(monthly_tax, 'SGD')}")
        print(f"月到手: {converter.format_amount(monthly_net_income, 'SGD')}")

        # 计算有效税率
        effective_tax_rate = (tax_result['total_tax'] / annual_income_sgd) * 100
        print(f"有效税率: {effective_tax_rate:.1f}%")

    def _analyze_lifetime_summary(self, monthly_salary_cny: float):
        """分析全生命周期总结"""
        print(f"\n📊 全生命周期总结 (30岁-65岁，35年)")
        print("-" * 50)

        # 转换月薪到新加坡元
        monthly_salary_sgd = monthly_salary_cny * 0.19

        # 计算35年的累计数据
        total_income = 0
        total_cpf_employee = 0
        total_cpf_employer = 0
        total_tax = 0
        total_net_income = 0

        for year in range(1, 36):
            # 考虑年增长率
            adjusted_salary = monthly_salary_sgd * ((1 + 0.02) ** (year - 1))
            annual_income = adjusted_salary * 12

            # 计算CPF
            cpf_result = self.tax_calculator.calculate_cpf_contribution(adjusted_salary)
            annual_cpf_employee = cpf_result['employee']['total'] * 12
            annual_cpf_employer = cpf_result['employer']['total'] * 12

            # 计算个税
            tax_result = self.tax_calculator.calculate_income_tax(
                annual_income,
                {'cpf_contribution': cpf_result['total'] * 12}
            )
            annual_tax = tax_result['total_tax']

            # 计算年净收入
            annual_net_income = annual_income - annual_cpf_employee - annual_tax

            # 累加
            total_income += annual_income
            total_cpf_employee += annual_cpf_employee
            total_cpf_employer += annual_cpf_employer
            total_tax += annual_tax
            total_net_income += annual_net_income

        print(f"35年总收入: {converter.format_amount(total_income, 'SGD')}")
        print(f"35年员工CPF: {converter.format_amount(total_cpf_employee, 'SGD')}")
        print(f"35年雇主CPF: {converter.format_amount(total_cpf_employer, 'SGD')}")
        print(f"35年总个税: {converter.format_amount(total_tax, 'SGD')}")
        print(f"35年总净收入: {converter.format_amount(total_net_income, 'SGD')}")

        # 计算比例
        print(f"\n比例分析:")
        print(f"CPF占收入比例: {(total_cpf_employee + total_cpf_employer) / total_income * 100:.1f}%")
        print(f"个税占收入比例: {total_tax / total_income * 100:.1f}%")
        print(f"净收入占收入比例: {total_net_income / total_income * 100:.1f}%")

        # 月平均值
        print(f"\n月平均值:")
        print(f"平均月收入: {converter.format_amount(total_income / 35 / 12, 'SGD')}")
        print(f"平均月CPF: {converter.format_amount((total_cpf_employee + total_cpf_employer) / 35 / 12, 'SGD')}")
        print(f"平均月个税: {converter.format_amount(total_tax / 35 / 12, 'SGD')}")
        print(f"平均月净收入: {converter.format_amount(total_net_income / 35 / 12, 'SGD')}")
