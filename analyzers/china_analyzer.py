#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China pension analysis module
"""

from datetime import date
from core.pension_engine import PensionEngine
from core.models import Person, SalaryProfile, Gender, EmploymentType
from utils.common import (
    create_standard_economic_factors, print_section_header, 
    print_completion_message, converter
)

def analyze_china_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析中国养老金"""
    # 获取实际参数
    cn_calculator = engine.calculators['CN']
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
        monthly_salary=monthly_salary,
        annual_growth_rate=0.02,
        contribution_start_age=30,
        base_salary=monthly_salary
    )

    # 创建经济因素
    economic_factors = create_standard_economic_factors(base_currency="CNY", display_currency="CNY")

    print(f"\n🏦 正在计算中国养老金...")

    # 计算中国养老金
    result = cn_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print_section_header("📊 养老金计算结果:")
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'CNY')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'CNY')}")
    print(f"总收益: {converter.format_amount(result.total_benefit, 'CNY')}")
    print(f"退休当年账户余额: {converter.format_amount(result.retirement_account_balance, 'CNY')}")
    print(f"投资回报率: {result.roi:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示缴费率信息
    print_section_header("💰 缴费率信息:")
    print(f"总缴费率: 28.0%")
    print(f"员工缴费率: 8.0%")
    print(f"雇主缴费率: 20.0%")

    # 显示详细分解
    details = result.details
    if 'basic_pension' in details:
        print(f"基础养老金: {converter.format_amount(details['basic_pension'], 'CNY')}")
    if 'personal_account_pension' in details:
        print(f"个人账户养老金: {converter.format_amount(details['personal_account_pension'], 'CNY')}")

    print_completion_message(scenario_name)