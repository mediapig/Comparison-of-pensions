#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国养老金分析器
分析基本养老保险的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class ChinaPensionAnalyzer:
    """中国养老金分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['CN']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        # 获取实际参数
        retirement_age = 63  # 固定63岁退休
        start_age = 30
        work_years = retirement_age - start_age  # 33年
        life_expectancy = 85
        collection_years = life_expectancy - retirement_age  # 22年

        print(f"\n{'='*80}")
        print(f"🇨🇳 中国养老金分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"工作年限: {work_years}年")
        print(f"退休年龄: {retirement_age}岁")
        print(f"预期寿命: {life_expectancy}岁 (预计领取{collection_years}年)")
        print(f"计发月数: 170个月")
        print(f"{'='*80}")

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
            base_salary=monthly_salary,
            annual_growth_rate=0.0
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="CNY"
        )

        print(f"\n🏦 正在计算中国养老金...")

        # 计算中国养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示基本信息
        print(f"\n📊 养老金计算结果:")
        print("-" * 50)
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'CNY')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'CNY')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'CNY')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示账户详情
        details = result.details
        print(f"\n🔍 养老金账户详情:")
        print("-" * 50)
        if 'basic_pension' in details:
            print(f"基础养老金: {converter.format_amount(details['basic_pension'], 'CNY')}")
        if 'personal_account_pension' in details:
            print(f"个人账户养老金: {converter.format_amount(details['personal_account_pension'], 'CNY')}")

        # 显示缴费率信息
        contribution_rates = self.calculator.contribution_rates
        print(f"\n💰 缴费率信息:")
        print("-" * 50)
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

        # 计算替代率
        annual_salary = monthly_salary * 12
        replacement_rate = (result.monthly_pension * 12) / annual_salary * 100

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"年工资: {converter.format_amount(annual_salary, 'CNY')}")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'CNY')}")
        print(f"替代率: {replacement_rate:.1f}%")

    def analyze_all_scenarios(self):
        """分析所有场景"""
        print("🇨🇳 === 中国养老金详细分析系统 ===")
        print("分析基本养老保险的详细情况\n")

        # 定义两个场景
        scenarios = [
            ("高收入场景", 50000),  # 月薪5万人民币
            ("低收入场景", 5000)    # 月薪5千人民币
        ]

        for scenario_name, monthly_salary in scenarios:
            self.analyze_scenario(scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 中国养老金分析完成！")
