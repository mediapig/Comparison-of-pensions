#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国养老金分析器
分析401K和Social Security的详细情况
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from utils.currency_converter import converter

class USAPensionAnalyzer:
    """美国养老金分析器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.calculator = engine.calculators['US']

    def analyze_scenario(self, scenario_name: str, monthly_salary: float):
        """分析单个场景"""
        print(f"\n{'='*80}")
        print(f"🇺🇸 美国养老金详细分析 - {scenario_name}")
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

        # 创建工资档案 - 工资每年增长2%
        salary_profile = SalaryProfile(
            base_salary=monthly_salary,
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

        print(f"\n🏦 正在计算美国养老金...")

        # 1. 基础养老金计算
        print(f"\n📊 基础养老金计算结果:")
        print("-" * 50)

        basic_result = self.calculator.calculate_pension(person, salary_profile, economic_factors)

        print(f"月退休金: {converter.format_amount(basic_result.monthly_pension, 'USD')}")
        print(f"总缴费: {converter.format_amount(basic_result.total_contribution, 'USD')}")
        print(f"总收益: {converter.format_amount(basic_result.total_benefit, 'USD')}")
        print(f"投资回报率: {basic_result.roi:.1%}")
        print(f"回本年龄: {basic_result.break_even_age}岁" if basic_result.break_even_age else "回本年龄: 无法计算")

        # 2. 401K详细分析
        print(f"\n🔍 401K详细分析:")
        print("-" * 50)

        k401_analysis = self.calculator.get_401k_analysis(person, salary_profile, economic_factors)

        print(f"401K员工总缴费: {converter.format_amount(k401_analysis['k401_employee_total'], 'USD')}")
        print(f"401K雇主总配比: {converter.format_amount(k401_analysis['k401_employer_total'], 'USD')}")
        print(f"401K总缴费: {converter.format_amount(k401_analysis['k401_total_contributions'], 'USD')}")
        print(f"递延缴费上限: $23,500 (2025年)")
        print(f"50岁+追加: $7,500")
        print(f"60-63岁追加: $11,250")
        print(f"415(c)总上限: $70,000")
        print(f"401K账户余额: {converter.format_amount(k401_analysis['k401_balance'], 'USD')}")
        print(f"401K月退休金: {converter.format_amount(k401_analysis['k401_monthly_pension'], 'USD')}")

        # 3. 缴费上限分析
        print(f"\n📋 缴费上限分析:")
        print("-" * 50)

        # 显示2025年401K准确的上限信息
        print(f"2025年401K缴费上限:")
        print(f"  • 402(g) 员工递延上限：$23,500")
        print(f"  • 50+ catch-up：$7,500")
        print(f"  • 60–63 super catch-up：$11,250（替代 $7,500；计划需支持）")
        print(f"  • 415(c) 员工+雇主合计上限：$70,000（不含 catch-up）")
        print(f"  • 60–63岁可递延总额 = $23,500 + $11,250 = $34,750")

        # 显示当前年龄信息
        age_limits = k401_analysis['age_limits']
        print(f"\n当前年龄: {age_limits['current_age']}岁")

        # 4. 雇主配比分析
        print(f"\n💼 雇主配比分析:")
        print("-" * 50)

        employer_match = k401_analysis['employer_match_sample']
        print(f"年工资: {converter.format_amount(employer_match['salary'], 'USD')}")
        print(f"员工缴费: {converter.format_amount(employer_match['employee_contribution'], 'USD')}")
        print(f"雇主配比: {converter.format_amount(employer_match['employer_match'], 'USD')}")
        print(f"401K总额: {converter.format_amount(employer_match['total_401k'], 'USD')}")

        # 5. 不同缴费比例场景
        print(f"\n📈 不同缴费比例场景分析:")
        print("-" * 50)

        # 将人民币月薪转换为美元
        cny_to_usd_rate = 0.14
        monthly_salary_usd = monthly_salary * cny_to_usd_rate
        scenarios = self.calculator.get_contribution_scenarios(
            monthly_salary_usd * 12, 30, 0.07
        )

        print(f"{'缴费比例':<10} {'年缴费':<15} {'35年后余额':<20} {'月退休金':<15}")
        print("-" * 60)

        for scenario in scenarios:
            print(f"{scenario['deferral_rate']:>8.1%}  {converter.format_amount(scenario['annual_contribution'], 'USD'):<15} {converter.format_amount(scenario['future_value'], 'USD'):<20} {converter.format_amount(scenario['monthly_pension'], 'USD'):<15}")

        # 6. 缴费历史详情
        print(f"\n📅 缴费历史详情（前5年和后5年）:")
        print("-" * 50)

        contribution_history = k401_analysis['contribution_history']

        # 显示前5年
        print("前5年缴费情况:")
        for i in range(min(5, len(contribution_history))):
            record = contribution_history[i]
            print(f"  第{i+1}年（{record['age']}岁）: 工资${record['annual_salary']:,.0f}, 401K员工缴费${record['k401_employee_contribution']:,.0f}, 雇主配比${record['k401_employer_match']:,.0f}")

        # 显示后5年
        if len(contribution_history) > 5:
            print("\n后5年缴费情况:")
            for i in range(max(0, len(contribution_history)-5), len(contribution_history)):
                record = contribution_history[i]
                print(f"  第{i+1}年（{record['age']}岁）: 工资${record['annual_salary']:,.0f}, 401K员工缴费${record['k401_employee_contribution']:,.0f}, 雇主配比${record['k401_employer_match']:,.0f}")

        # 7. 总结
        print(f"\n📋 总结:")
        print("-" * 50)

        # 计算替代率 - 使用美元工资计算
        annual_salary_usd = monthly_salary_usd * 12
        replacement_rate = (basic_result.monthly_pension * 12) / annual_salary_usd * 100

        print(f"年工资: {converter.format_amount(annual_salary_usd, 'USD')}")
        print(f"退休后年养老金: {converter.format_amount(basic_result.monthly_pension * 12, 'USD')}")
        print(f"替代率: {replacement_rate:.1f}%")

        # 分析各部分占比
        social_security = basic_result.details.get('social_security_pension', 0)
        k401_pension = basic_result.details.get('k401_monthly_pension', 0)

        if social_security > 0 and k401_pension > 0:
            total_pension = social_security + k401_pension
            social_security_pct = social_security / total_pension * 100
            k401_pct = k401_pension / total_pension * 100

            print(f"\n养老金构成:")
            print(f"  Social Security: {converter.format_amount(social_security, 'USD')}/月 ({social_security_pct:.1f}%)")
            print(f"  401K: {converter.format_amount(k401_pension, 'USD')}/月 ({k401_pct:.1f}%)")
            print(f"  总计: {converter.format_amount(total_pension, 'USD')}/月")

    def analyze_all_scenarios(self):
        """分析所有场景"""
        print("🇺🇸 === 美国养老金详细分析系统 ===")
        print("分析401K和Social Security的详细情况\n")

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

        print(f"\n🎯 美国养老金分析完成！")
