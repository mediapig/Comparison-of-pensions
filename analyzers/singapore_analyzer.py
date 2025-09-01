#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡 pension analysis module
"""

from core.pension_engine import PensionEngine
from utils.common import (
    create_standard_person, create_standard_salary_profile, create_standard_economic_factors,
    print_analysis_header, print_section_header, print_completion_message, converter
)

def analyze_singapore_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析新加坡养老金"""
    desc = "分析中央公积金(CPF)系统" if "分析中央公积金(CPF)系统" else ""
    print_analysis_header("🇸🇬", "新加坡", scenario_name, monthly_salary, desc)

    # 创建标准对象
    person = create_standard_person()
    salary_profile = create_standard_salary_profile(monthly_salary, growth_rate=0.00)
    economic_factors = create_standard_economic_factors(base_currency="CNY", display_currency="SG")

    # 获取新加坡计算器
    calculator = engine.calculators["SG"]

    print(f"
🏦 正在计算新加坡养老金...")

    # 计算新加坡养老金
    result = calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print_section_header("📊 养老金计算结果:")
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'SG')}" )
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'SG')}" )
    print(f"总收益: {converter.format_amount(result.total_benefit, 'SG')}" )
    print(f"投资回报率: {result.roi:.1%}" )
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示缴费率信息
    contribution_rates = calculator.contribution_rates
    print_section_header("💰 缴费率信息:")
    print(f"总缴费率: {contribution_rates['total']:.1%}")
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    print_completion_message(scenario_name)
