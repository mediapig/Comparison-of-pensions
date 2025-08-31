#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休金对比系统可视化示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_comparison_charts():
    """创建对比图表"""
    # 创建计算引擎
    engine = PensionEngine()
    engine.register_calculator(ChinaPensionCalculator())
    engine.register_calculator(USAPensionCalculator())

    # 创建测试数据
    person = Person(
        name="张三",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2015, 7, 1)
    )

    salary_profile = SalaryProfile(
        base_salary=8000,
        annual_growth_rate=0.05
    )

    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05
    )

    # 计算退休金对比
    comparison_df = engine.compare_pensions(person, salary_profile, economic_factors)

    # 1. 月退休金对比柱状图
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 2, 1)
    bars = plt.bar(comparison_df['country_name'], comparison_df['monthly_pension'],
                   color=['#FF6B6B', '#4ECDC4'])
    plt.title('月退休金对比', fontsize=14, fontweight='bold')
    plt.ylabel('月退休金 (元)')

    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{height:.0f}', ha='center', va='bottom')

    # 2. ROI对比图
    plt.subplot(2, 2, 2)
    colors = ['green' if roi > 0 else 'red' for roi in comparison_df['roi']]
    bars = plt.bar(comparison_df['country_name'], comparison_df['roi'], color=colors)
    plt.title('投资回报率 (ROI) 对比', fontsize=14, fontweight='bold')
    plt.ylabel('ROI')

    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height > 0 else -0.1),
                f'{height:.1%}', ha='center', va='bottom' if height > 0 else 'top')

    # 3. 总缴费对比
    plt.subplot(2, 2, 3)
    bars = plt.bar(comparison_df['country_name'], comparison_df['total_contribution']/10000,
                   color=['#FFE66D', '#95E1D3'])
    plt.title('总缴费对比', fontsize=14, fontweight='bold')
    plt.ylabel('总缴费 (万元)')

    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{height:.1f}', ha='center', va='bottom')

    # 4. 回本年龄对比
    plt.subplot(2, 2, 4)
    bars = plt.bar(comparison_df['country_name'], comparison_df['break_even_age'],
                   color=['#A8E6CF', '#FFB3BA'])
    plt.title('回本年龄对比', fontsize=14, fontweight='bold')
    plt.ylabel('回本年龄 (岁)')

    # 在柱子上添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.0f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('pension_comparison_charts.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_sensitivity_charts():
    """创建敏感性分析图表"""
    # 创建计算引擎
    engine = PensionEngine()
    engine.register_calculator(ChinaPensionCalculator())
    engine.register_calculator(USAPensionCalculator())

    # 创建测试数据
    person = Person(
        name="李四",
        birth_date=date(1985, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2010, 7, 1)
    )

    salary_profile = SalaryProfile(
        base_salary=12000,
        annual_growth_rate=0.06
    )

    economic_factors = EconomicFactors(
        inflation_rate=0.025,
        investment_return_rate=0.08,
        social_security_return_rate=0.06
    )

    # 通胀率敏感性分析
    inflation_rates = [0.01, 0.02, 0.025, 0.03, 0.04, 0.05]
    inflation_analysis = engine.sensitivity_analysis(
        person, salary_profile, economic_factors, 'inflation_rate', inflation_rates
    )

    # 投资回报率敏感性分析
    return_rates = [0.03, 0.05, 0.07, 0.08, 0.09, 0.11]
    investment_analysis = engine.sensitivity_analysis(
        person, salary_profile, economic_factors, 'investment_return_rate', return_rates
    )

    # 创建图表
    plt.figure(figsize=(15, 6))

    # 通胀率敏感性分析
    plt.subplot(1, 2, 1)
    for country_code in ['CN', 'US']:
        country_data = inflation_analysis[inflation_analysis['country'] == country_code]
        country_name = engine.calculators[country_code].country_name
        plt.plot(country_data['value'], country_data['monthly_pension'],
                marker='o', linewidth=2, label=country_name)

    plt.title('通胀率对月退休金的影响', fontsize=14, fontweight='bold')
    plt.xlabel('通胀率')
    plt.ylabel('月退休金 (元)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 投资回报率敏感性分析
    plt.subplot(1, 2, 2)
    for country_code in ['CN', 'US']:
        country_data = investment_analysis[investment_analysis['country'] == country_code]
        country_name = engine.calculators[country_code].country_name
        plt.plot(country_data['value'], country_data['monthly_pension'],
                marker='s', linewidth=2, label=country_name)

    plt.title('投资回报率对月退休金的影响', fontsize=14, fontweight='bold')
    plt.xlabel('投资回报率')
    plt.ylabel('月退休金 (元)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('sensitivity_analysis_charts.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_salary_growth_chart():
    """创建工资增长模型图表"""
    from utils.salary_growth import SalaryGrowthModel

    # 创建不同的工资增长模型
    base_salary = 8000
    years = 30

    # 线性增长
    linear_salaries = SalaryGrowthModel.linear_growth(base_salary, 0.05, years)

    # 复合增长
    compound_salaries = SalaryGrowthModel.compound_growth(base_salary, 0.05, years)

    # 分阶段增长
    growth_stages = [
        {'years': 10, 'rate': 0.08},   # 前10年快速增长
        {'years': 10, 'rate': 0.05},   # 中间10年中等增长
        {'years': 10, 'rate': 0.03}    # 后10年缓慢增长
    ]
    stage_salaries = SalaryGrowthModel.stage_growth(base_salary, growth_stages)

    # 职业生涯峰值模型
    peak_salaries = SalaryGrowthModel.career_peak_growth(
        base_salary, peak_age=45, start_age=25, years=years
    )

    # 创建图表
    plt.figure(figsize=(12, 8))

    years_list = list(range(years + 1))
    ages = [25 + year for year in years_list]

    plt.plot(ages, linear_salaries, 'o-', label='线性增长 (5%)', linewidth=2)
    plt.plot(ages, compound_salaries, 's-', label='复合增长 (5%)', linewidth=2)
    plt.plot(ages, stage_salaries, '^-', label='分阶段增长', linewidth=2)
    plt.plot(ages, peak_salaries, 'd-', label='职业生涯峰值', linewidth=2)

    plt.title('不同工资增长模型对比', fontsize=16, fontweight='bold')
    plt.xlabel('年龄 (岁)')
    plt.ylabel('月工资 (元)')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)

    # 添加网格
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('salary_growth_models.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """主函数"""
    print("开始生成可视化图表...")

    try:
        # 1. 退休金对比图表
        print("生成退休金对比图表...")
        create_comparison_charts()

        # 2. 敏感性分析图表
        print("生成敏感性分析图表...")
        create_sensitivity_charts()

        # 3. 工资增长模型图表
        print("生成工资增长模型图表...")
        create_salary_growth_chart()

        print("所有图表生成完成！")
        print("生成的文件:")
        print("- pension_comparison_charts.png")
        print("- sensitivity_analysis_charts.png")
        print("- salary_growth_models.png")

    except Exception as e:
        print(f"生成图表时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
