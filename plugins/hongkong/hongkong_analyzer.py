#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港MPF分析器
分析强积金计划的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class HongKongMPFAnalyzer:
    """香港MPF分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['HK']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        print(f"\n{'='*80}")
        print(f"🇭🇰 香港MPF分析 - {scenario_name}")
        print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"工作年限: 35年")
        print(f"退休年龄: 65岁")
        print(f"领取年限: 20年")
        print(f"{'='*80}")

        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 创建工资档案 - 工资不增长
        salary_profile = SalaryProfile(
            base_salary=monthly_salary,
            annual_growth_rate=0.00
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="HKD"
        )

        print(f"\n🏦 正在计算香港MPF...")

        # 计算香港MPF
        result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        # 显示基本信息
        print(f"\n📊 MPF计算结果:")
        print("-" * 50)
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'HKD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'HKD')}")
        print(f"总收益: {converter.format_amount(result.details['total_return'], 'HKD')}")
        print(f"投资回报率: {result.details['roi_pct']:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示账户详情
        details = result.details
        print(f"\n🔍 MPF账户详情:")
        print("-" * 50)
        print(f"MPF账户余额: {converter.format_amount(details['mpf_balance'], 'HKD')}")
        print(f"员工供款: {converter.format_amount(details['employee_contrib'], 'HKD')}")
        print(f"雇主供款: {converter.format_amount(details['employer_contrib'], 'HKD')}")
        print(f"总供款: {converter.format_amount(details['total_contrib'], 'HKD')}")

        # 显示缴费率信息
        contribution_rates = self.calculator.contribution_rates
        print(f"\n💰 缴费率信息:")
        print("-" * 50)
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: 5.0% (固定)")
        print(f"总缴费率: 10.0% (员工5% + 雇主5%)")

        # 计算替代率
        annual_salary_hkd = monthly_salary * 1.08 * 12  # 转换为港币年工资（假设汇率1.08）
        replacement_rate = (result.monthly_pension * 12) / annual_salary_hkd * 100

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
        print(f"年工资: {converter.format_amount(annual_salary_hkd, 'HKD')} (HK$)")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'HKD')}")
        print(f"替代率: {replacement_rate:.1f}%")

    def analyze_all_scenarios(self):
        """分析所有场景"""
        print("🇭🇰 === 香港MPF详细分析系统 ===")
        print("分析强积金计划的详细情况\n")

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

        print(f"\n🎯 香港MPF分析完成！")
