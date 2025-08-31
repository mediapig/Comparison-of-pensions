#!/usr/bin/env python3
"""
退休金对比系统使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator
import pandas as pd

def main():
    """主函数"""
    print("=== 退休金对比系统 ===\n")

    # 1. 创建退休金计算引擎
    engine = PensionEngine()

    # 2. 注册不同国家的计算器
    engine.register_calculator(ChinaPensionCalculator())
    engine.register_calculator(USAPensionCalculator())

    print(f"可用国家: {engine.get_available_countries()}\n")

    # 3. 创建个人信息
    person = Person(
        name="张三",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2015, 7, 1)
    )

    print(f"个人信息:")
    print(f"  姓名: {person.name}")
    print(f"  年龄: {person.age}岁")
    print(f"  工作年限: {person.work_years}年")
    print(f"  就业类型: {person.employment_type.value}")
    print()

    # 4. 创建工资档案
    salary_profile = SalaryProfile(
        base_salary=8000,           # 基本工资8000元
        annual_growth_rate=0.05,    # 年增长率5%
        bonus_rate=0.2              # 奖金比例20%
    )

    print(f"工资档案:")
    print(f"  基本工资: {salary_profile.base_salary}元")
    print(f"  年增长率: {salary_profile.annual_growth_rate:.1%}")
    print(f"  奖金比例: {salary_profile.bonus_rate:.1%}")
    print()

    # 5. 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,                    # 通胀率3%
        investment_return_rate=0.07,            # 投资回报率7%
        social_security_return_rate=0.05,      # 社保基金投资回报率5%
        currency="CNY"
    )

    print(f"经济因素:")
    print(f"  通胀率: {economic_factors.inflation_rate:.1%}")
    print(f"  投资回报率: {economic_factors.investment_return_rate:.1%}")
    print(f"  社保基金投资回报率: {economic_factors.social_security_return_rate:.1%}")
    print()

    # 6. 计算退休金对比
    print("正在计算退休金对比...")
    comparison_df = engine.compare_pensions(person, salary_profile, economic_factors)

    print("\n=== 退休金对比结果 ===")
    print(comparison_df.to_string(index=False))
    print()

    # 7. 敏感性分析
    print("=== 通胀率敏感性分析 ===")
    inflation_analysis = engine.sensitivity_analysis(
        person, salary_profile, economic_factors, 'inflation_rate',
        [0.01, 0.02, 0.03, 0.04, 0.05]
    )

        # 按通胀率分组显示
    for inflation_rate in [0.01, 0.02, 0.03, 0.04, 0.05]:
        data = inflation_analysis[inflation_analysis['value'] == inflation_rate]
        print(f"\n通胀率 {inflation_rate:.1%}:")
        for _, row in data.iterrows():
            country_name = engine.calculators[row['country']].country_name
            print(f"  {country_name}: 月退休金 {row['monthly_pension']:.0f}元, ROI {row['roi']:.1%}")
    
    print("\n=== 投资回报率敏感性分析 ===")
    investment_analysis = engine.sensitivity_analysis(
        person, salary_profile, economic_factors, 'investment_return_rate',
        [0.03, 0.05, 0.07, 0.09, 0.11]
    )
    
    # 按投资回报率分组显示
    for return_rate in [0.03, 0.05, 0.07, 0.09, 0.11]:
        data = investment_analysis[investment_analysis['value'] == return_rate]
        print(f"\n投资回报率 {return_rate:.1%}:")
        for _, row in data.iterrows():
            country_name = engine.calculators[row['country']].country_name
            print(f"  {country_name}: 月退休金 {row['monthly_pension']:.0f}元, ROI {row['roi']:.1%}")

    # 8. 生成详细报告
    print("\n正在生成详细报告...")
    report = engine.generate_report(person, salary_profile, economic_factors)

    print(f"\n=== 详细报告 ===")
    print(f"个人信息:")
    for key, value in report['person_info'].items():
        print(f"  {key}: {value}")

    print(f"\n缴费历史 (前5年):")
    contribution_history = report['contribution_history'][:5]
    for record in contribution_history:
        print(f"  {record['year']}年 ({record['age']}岁): 工资{record['salary']:.0f}元, 缴费{record['personal_contribution']:.0f}元")

def demo_different_scenarios():
    """演示不同场景"""
    print("\n" + "="*50)
    print("不同场景演示")
    print("="*50)

    engine = PensionEngine()
    engine.register_calculator(ChinaPensionCalculator())
    engine.register_calculator(USAPensionCalculator())

    # 场景1: 高收入人群
    print("\n场景1: 高收入人群 (月薪20000元)")
    high_income_person = Person(
        name="李四",
        birth_date=date(1985, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2010, 7, 1)
    )

    high_income_salary = SalaryProfile(
        base_salary=20000,
        annual_growth_rate=0.06,
        bonus_rate=0.3
    )

    economic_factors = EconomicFactors(
        inflation_rate=0.025,
        investment_return_rate=0.08,
        social_security_return_rate=0.06,
        currency="CNY"
    )

    comparison = engine.compare_pensions(high_income_person, high_income_salary, economic_factors)
    print(comparison.to_string(index=False))

    # 场景2: 女性公务员
    print("\n场景2: 女性公务员 (月薪15000元)")
    female_civil_servant = Person(
        name="王五",
        birth_date=date(1988, 1, 1),
        gender=Gender.FEMALE,
        employment_type=EmploymentType.CIVIL_SERVANT,
        start_work_date=date(2012, 7, 1)
    )

    civil_servant_salary = SalaryProfile(
        base_salary=15000,
        annual_growth_rate=0.04,
        bonus_rate=0.25
    )

    comparison = engine.compare_pensions(female_civil_servant, civil_servant_salary, economic_factors)
    print(comparison.to_string(index=False))

if __name__ == "__main__":
    main()
    demo_different_scenarios()
