#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多国家退休金对比示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine

# 导入所有国家计算器
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator
from plugins.germany.germany_calculator import GermanyPensionCalculator
from plugins.taiwan.taiwan_calculator import TaiwanPensionCalculator
from plugins.hongkong.hongkong_calculator import HongKongPensionCalculator
from plugins.singapore.singapore_calculator import SingaporePensionCalculator
from plugins.japan.japan_calculator import JapanPensionCalculator
from plugins.uk.uk_calculator import UKPensionCalculator
from plugins.australia.australia_calculator import AustraliaPensionCalculator
from plugins.canada.canada_calculator import CanadaPensionCalculator

import pandas as pd

def register_all_calculators(engine: PensionEngine):
    """注册所有国家计算器"""
    calculators = [
        ChinaPensionCalculator(),
        USAPensionCalculator(),
        GermanyPensionCalculator(),
        TaiwanPensionCalculator(),
        HongKongPensionCalculator(),
        SingaporePensionCalculator(),
        JapanPensionCalculator(),
        UKPensionCalculator(),
        AustraliaPensionCalculator(),
        CanadaPensionCalculator()
    ]

    for calculator in calculators:
        engine.register_calculator(calculator)

    return engine

def create_test_scenarios():
    """创建测试场景"""
    scenarios = []

    # 场景1: 年轻白领
    scenarios.append({
        'name': '年轻白领',
        'person': Person(
            name="张三",
            birth_date=date(1995, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2020, 7, 1)
        ),
        'salary': SalaryProfile(
            base_salary=8000,
            annual_growth_rate=0.06,
            bonus_rate=0.2
        ),
        'economic': EconomicFactors(
            inflation_rate=0.025,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            currency="CNY"
        )
    })

    # 场景2: 中年高管
    scenarios.append({
        'name': '中年高管',
        'person': Person(
            name="李四",
            birth_date=date(1980, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2005, 7, 1)
        ),
        'salary': SalaryProfile(
            base_salary=25000,
            annual_growth_rate=0.05,
            bonus_rate=0.3
        ),
        'economic': EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.08,
            social_security_return_rate=0.06,
            currency="CNY"
        )
    })

    # 场景3: 女性公务员
    scenarios.append({
        'name': '女性公务员',
        'person': Person(
            name="王五",
            birth_date=date(1985, 1, 1),
            gender=Gender.FEMALE,
            employment_type=EmploymentType.CIVIL_SERVANT,
            start_work_date=date(2010, 7, 1)
        ),
        'salary': SalaryProfile(
            base_salary=15000,
            annual_growth_rate=0.04,
            bonus_rate=0.25
        ),
        'economic': EconomicFactors(
            inflation_rate=0.025,
            investment_return_rate=0.06,
            social_security_return_rate=0.05,
            currency="CNY"
        )
    })

    return scenarios

def analyze_scenario(engine: PensionEngine, scenario: dict):
    """分析单个场景"""
    print(f"\n{'='*60}")
    print(f"场景: {scenario['name']}")
    print(f"{'='*60}")

    person = scenario['person']
    salary = scenario['salary']
    economic = scenario['economic']

    print(f"个人信息:")
    print(f"  姓名: {person.name}")
    print(f"  年龄: {person.age}岁")
    print(f"  工作年限: {person.work_years}年")
    print(f"  就业类型: {person.employment_type.value}")
    print(f"  基本工资: {salary.base_salary:,.0f}元")
    print(f"  年增长率: {salary.annual_growth_rate:.1%}")

    print(f"\n经济因素:")
    print(f"  通胀率: {economic.inflation_rate:.1%}")
    print(f"  投资回报率: {economic.investment_return_rate:.1%}")
    print(f"  社保基金投资回报率: {economic.social_security_return_rate:.1%}")

    # 计算退休金对比
    print(f"\n正在计算退休金对比...")
    comparison_df = engine.compare_pensions(person, salary, economic)

    print(f"\n退休金对比结果:")
    print(comparison_df.to_string(index=False))

    # 计算排名
    print(f"\n排名分析:")
    for i, (_, row) in enumerate(comparison_df.iterrows(), 1):
        print(f"  {i}. {row['country_name']}: {row['monthly_pension']:,.0f}元/月")

    # 计算平均值
    avg_pension = comparison_df['monthly_pension'].mean()
    print(f"\n平均月退休金: {avg_pension:,.0f}元")

    # 找出最高和最低
    max_country = comparison_df.loc[comparison_df['monthly_pension'].idxmax()]
    min_country = comparison_df.loc[comparison_df['monthly_pension'].idxmin()]

    print(f"最高退休金: {max_country['country_name']} ({max_country['monthly_pension']:,.0f}元)")
    print(f"最低退休金: {min_country['country_name']} ({min_country['monthly_pension']:,.0f}元)")

    return comparison_df

def generate_summary_report(engine: PensionEngine, scenarios: list):
    """生成总结报告"""
    print(f"\n{'='*80}")
    print(f"总结报告")
    print(f"{'='*80}")

    all_results = []

    for scenario in scenarios:
        person = scenario['person']
        salary = scenario['salary']
        economic = scenario['economic']

        comparison_df = engine.compare_pensions(person, salary, economic)

        for _, row in comparison_df.iterrows():
            all_results.append({
                'scenario': scenario['name'],
                'age': person.age,
                'base_salary': salary.base_salary,
                'country': row['country_name'],
                'monthly_pension': row['monthly_pension'],
                'roi': row['roi'],
                'break_even_age': row['break_even_age']
            })

    # 转换为DataFrame进行分析
    results_df = pd.DataFrame(all_results)

    print(f"\n按国家分组的平均退休金:")
    country_avg = results_df.groupby('country')['monthly_pension'].agg(['mean', 'min', 'max']).round(0)
    country_avg.columns = ['平均', '最低', '最高']
    print(country_avg.to_string())

    print(f"\n按场景分组的平均退休金:")
    scenario_avg = results_df.groupby('scenario')['monthly_pension'].agg(['mean', 'min', 'max']).round(0)
    scenario_avg.columns = ['平均', '最低', '最高']
    print(scenario_avg.to_string())

    print(f"\nROI分析:")
    roi_analysis = results_df.groupby('country')['roi'].agg(['mean', 'min', 'max']).round(3)
    roi_analysis.columns = ['平均ROI', '最低ROI', '最高ROI']
    print(roi_analysis.to_string())

    return results_df

def main():
    """主函数"""
    print("=== 多国家退休金对比系统 ===\n")

    # 创建计算引擎
    engine = PensionEngine()

    # 注册所有国家计算器
    print("正在注册国家计算器...")
    engine = register_all_calculators(engine)

    print(f"\n可用国家: {engine.get_available_countries()}")
    print(f"总计: {len(engine.get_available_countries())} 个国家/地区")

    # 创建测试场景
    scenarios = create_test_scenarios()

    # 分析每个场景
    all_results = []
    for scenario in scenarios:
        result_df = analyze_scenario(engine, scenario)
        all_results.append(result_df)

    # 生成总结报告
    summary_df = generate_summary_report(engine, scenarios)

    print(f"\n分析完成！")
    print(f"共分析了 {len(scenarios)} 个场景，{len(engine.get_available_countries())} 个国家/地区")

if __name__ == "__main__":
    main()
