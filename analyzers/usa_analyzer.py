#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US pension analysis module
"""

from core.pension_engine import PensionEngine
from utils.common import (
    create_standard_person, create_standard_economic_factors, 
    print_analysis_header, print_section_header, print_completion_message, converter
)
from core.models import SalaryProfile

def analyze_usa_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析美国养老金"""
    print_analysis_header("🇺🇸", "美国", scenario_name, monthly_salary)

    # 创建标准对象
    person = create_standard_person()
    person.start_work_date = person.birth_date.replace(year=1995, month=7, day=1)  # US specific start date
    
    salary_profile = SalaryProfile(
        monthly_salary=monthly_salary,
        annual_growth_rate=0.02,
        contribution_start_age=30,
        base_salary=monthly_salary
    )
    
    economic_factors = create_standard_economic_factors(base_currency="CNY", display_currency="USD")

    # 获取美国计算器
    usa_calculator = engine.calculators['US']

    print(f"\n🏦 正在计算美国养老金...")

    # 1. 基础养老金计算
    print_section_header("📊 基础养老金计算结果:")

    basic_result = usa_calculator.calculate_pension(person, salary_profile, economic_factors)

    print(f"月退休金: {converter.format_amount(basic_result.monthly_pension, 'USD')}")
    print(f"总缴费: {converter.format_amount(basic_result.total_contribution, 'USD')}")
    print(f"总收益: {converter.format_amount(basic_result.total_benefit, 'USD')}")
    print(f"退休当年账户余额: {converter.format_amount(basic_result.retirement_account_balance, 'USD')}")
    print(f"投资回报率: {basic_result.roi:.1%}")
    print(f"回本年龄: {basic_result.break_even_age}岁" if basic_result.break_even_age else "回本年龄: 无法计算")

    # 2. 401K详细分析
    print_section_header("🔍 401K详细分析:")

    k401_analysis = usa_calculator.get_401k_analysis(person, salary_profile, economic_factors)

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
    print_section_header("📋 缴费上限分析:")

    print(f"2025年401K缴费上限:")
    print(f"  • 402(g) 员工递延上限：$23,500")
    print(f"  • 50+ catch-up：$7,500")
    print(f"  • 60–63 super catch-up：$11,250（替代 $7,500；计划需支持）")
    print(f"  • 415(c) 员工+雇主合计上限：$70,000（不含 catch-up）")
    print(f"  • 60–63岁可递延总额 = $23,500 + $11,250 = $34,750")

    age_limits = k401_analysis['age_limits']
    print(f"\n当前年龄: {age_limits['current_age']}岁")

    # 4. 雇主配比分析
    print_section_header("💼 雇主配比分析:")

    employer_match = k401_analysis['employer_match_sample']
    print(f"年工资: {converter.format_amount(employer_match['salary'], 'USD')}")
    print(f"员工缴费: {converter.format_amount(employer_match['employee_contribution'], 'USD')}")
    print(f"雇主配比: {converter.format_amount(employer_match['employer_match'], 'USD')}")
    print(f"401K总额: {converter.format_amount(employer_match['total_401k'], 'USD')}")

    # 5. 不同缴费比例场景
    print_section_header("📈 不同缴费比例场景分析:")

    cny_to_usd_rate = 0.14
    monthly_salary_usd = monthly_salary * cny_to_usd_rate
    scenarios = usa_calculator.get_contribution_scenarios(
        monthly_salary_usd * 12, 30, 0.07
    )

    print(f"{'缴费比例':<10} {'年缴费':<15} {'35年后余额':<20} {'月退休金':<15}")
    print("-" * 60)

    for scenario in scenarios:
        print(f"{scenario['deferral_rate']:>8.1%}  {converter.format_amount(scenario['annual_contribution'], 'USD'):<15} {converter.format_amount(scenario['future_value'], 'USD'):<20} {converter.format_amount(scenario['monthly_pension'], 'USD'):<15}")

    # 6. 缴费历史详情
    print_section_header("📅 缴费历史详情（前5年和后5年）:")

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
    print_section_header("📋 总结:")

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
    
    print_completion_message(scenario_name)