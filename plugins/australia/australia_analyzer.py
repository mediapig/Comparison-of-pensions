#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚养老金分析器
分析超级年金的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class AustraliaPensionAnalyzer:
    """澳大利亚养老金分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['AU']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 获取澳大利亚计算器
        retirement_age = self.calculator.get_retirement_age(person)
        start_work_age = 30  # 固定30岁开始工作
        work_years = retirement_age - start_work_age

        print(f"\n{'='*80}")
        print(f"🇦🇺 澳大利亚养老金分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"工作年限: {work_years}年")
        print(f"退休年龄: {retirement_age}岁")
        print(f"预期寿命: 85岁 (预计领取{85-retirement_age}年)")
        print(f"{'='*80}")

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
            display_currency="AUD"
        )

        print(f"\n🏦 正在计算澳大利亚养老金...")

        # 计算澳大利亚养老金
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示基本信息
        print(f"\n📊 养老金计算结果:")
        print("-" * 50)
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'AUD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'AUD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'AUD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        contribution_rates = self.calculator.contribution_rates
        print(f"\n💰 缴费率信息:")
        print("-" * 50)
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

        # 使用计算器内部计算的替代率
        replacement_rate = result.details.get('replacement_rate', 0) * 100
        last_year_salary = result.details.get('last_year_salary', 0)

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"初始年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
        print(f"初始年工资: {converter.format_amount(monthly_salary * 0.21 * 12, 'AUD')} (A$)")
        print(f"最后一年工资: {converter.format_amount(last_year_salary, 'AUD')} (A$)")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'AUD')}")
        print(f"替代率: {replacement_rate:.1f}%")

    def analyze_all_scenarios(self, monthly_salary: float = 10000):
        """分析指定工资的养老金情况"""
        print("🇦🇺 === 澳大利亚养老金详细分析系统 ===")
        print("分析超级年金的详细情况\n")

        self.analyze_scenario("分析场景", monthly_salary)
        print(f"\n{'='*80}")
        print(f"✅ 分析完成")
        print(f"{'='*80}")

        print(f"\n🎯 澳大利亚养老金分析完成！")
