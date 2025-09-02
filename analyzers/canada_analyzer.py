#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canada pension analysis module
"""

from core.pension_engine import PensionEngine
from utils.common import (
    create_standard_person, create_standard_salary_profile, create_standard_economic_factors,
    print_analysis_header, print_section_header, print_completion_message, converter
)

def analyze_canada_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析加拿大养老金"""
    print_analysis_header("🇨🇦", "加拿大", scenario_name, monthly_salary, "分析CPP和OAS的详细情况")

    # 创建标准对象
    person = create_standard_person()
    person.start_work_date = person.birth_date.replace(year=1995, month=7, day=1)  # Canada specific
    
    salary_profile = create_standard_salary_profile(monthly_salary, growth_rate=0.00)
    economic_factors = create_standard_economic_factors(base_currency="CNY", display_currency="CAD")

    # 获取加拿大计算器
    ca_calculator = engine.calculators['CA']

    print(f"\n🏦 正在计算加拿大养老金...")

    # 计算加拿大养老金
    result = ca_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示给付信息（公共年金制）
    cpp_annual = result.details.get('cpp_monthly', 0) * 12
    oas_annual = result.details.get('oas_monthly', 0) * 12
    annual_pension = result.monthly_pension * 12
    
    print_section_header("📊 养老金给付（公共年金制：CPP + OAS）")
    print(f"  CPP: {converter.format_amount(cpp_annual, 'CAD')}/年 | OAS: {converter.format_amount(oas_annual, 'CAD')}/年")
    print(f"  合计: {converter.format_amount(annual_pension, 'CAD')}/年 ≈ {converter.format_amount(result.monthly_pension, 'CAD')}/月")

    # 显示缴费统计信息
    print_section_header("💰 CPP 累计缴费（仅统计口径）")
    print("  合计费率: 11.9% = 员工 5.95% + 雇主 5.95%")
    print(f"  累计缴费（合计）: {converter.format_amount(result.total_contribution * 2, 'CAD')}")
    
    print(f"\nℹ️ 说明：CPP 与 OAS 为公共年金（DB/准DB），不计算总收益、投资回报率与回本年龄。")
    print("    OAS = 734.95(2025Q3, 65–74) × 12 × (居住年限/40) = 734.95×12×(35/40) ≈ 7,716.98/年")
    print("    CPP 满额口径采用：17,196/年（2025），并按年资与平均可计缴工资比例折算")

    # 计算替代率
    annual_salary_cad = monthly_salary * 0.19 * 12  # 转换为加币年工资
    replacement_rate = (result.monthly_pension * 12) / annual_salary_cad * 100

    print_section_header("📋 总结:")
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_cad, 'CAD')} (C$)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'CAD')}")
    print(f"替代率: {replacement_rate:.1f}%")

    print_completion_message(scenario_name)