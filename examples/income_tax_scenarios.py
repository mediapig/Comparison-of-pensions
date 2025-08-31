#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考虑个人所得税的收入场景分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
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
from utils.currency_converter import converter

class TaxCalculator:
    """各国个人所得税计算器"""

    @staticmethod
    def calculate_china_tax(annual_salary: float) -> float:
        """计算中国个人所得税"""
        # 中国个税起征点：5000元/月，年化60000元
        monthly_threshold = 5000
        annual_threshold = 60000

        # 专项扣除（假设）
        special_deduction = 12000  # 年专项扣除

        taxable_income = annual_salary - annual_threshold - special_deduction

        if taxable_income <= 0:
            return 0

        # 中国个税累进税率
        if taxable_income <= 36000:
            tax_rate = 0.03
            quick_deduction = 0
        elif taxable_income <= 144000:
            tax_rate = 0.10
            quick_deduction = 2520
        elif taxable_income <= 300000:
            tax_rate = 0.20
            quick_deduction = 16920
        elif taxable_income <= 420000:
            tax_rate = 0.25
            quick_deduction = 31920
        elif taxable_income <= 660000:
            tax_rate = 0.30
            quick_deduction = 52920
        elif taxable_income <= 960000:
            tax_rate = 0.35
            quick_deduction = 85920
        else:
            tax_rate = 0.45
            quick_deduction = 181920

        annual_tax = taxable_income * tax_rate - quick_deduction
        return max(annual_tax, 0)

    @staticmethod
    def calculate_usa_tax(annual_salary: float) -> float:
        """计算美国个人所得税（联邦税，取平均值）"""
        # 美国联邦税（2024年，单身）
        # 简化计算，使用平均税率
        if annual_salary <= 11600:
            avg_rate = 0.10
        elif annual_salary <= 47150:
            avg_rate = 0.12
        elif annual_salary <= 100525:
            avg_rate = 0.22
        elif annual_salary <= 191950:
            avg_rate = 0.24
        elif annual_salary <= 243725:
            avg_rate = 0.32
        elif annual_salary <= 609350:
            avg_rate = 0.35
        else:
            avg_rate = 0.37

        # 考虑标准扣除
        standard_deduction = 14600
        taxable_income = max(annual_salary - standard_deduction, 0)

        return taxable_income * avg_rate

    @staticmethod
    def calculate_germany_tax(annual_salary: float) -> float:
        """计算德国个人所得税（简化版）"""
        # 德国个税（2024年，单身）
        # 使用平均税率简化计算
        if annual_salary <= 10908:
            avg_rate = 0.0
        elif annual_salary <= 62809:
            avg_rate = 0.42
        else:
            avg_rate = 0.45

        return annual_salary * avg_rate

    @staticmethod
    def calculate_taiwan_tax(annual_salary: float) -> float:
        """计算台湾个人所得税"""
        # 台湾个税（2024年）
        if annual_salary <= 560000:
            tax_rate = 0.05
        elif annual_salary <= 1260000:
            tax_rate = 0.12
        elif annual_salary <= 2520000:
            tax_rate = 0.20
        elif annual_salary <= 4720000:
            tax_rate = 0.30
        elif annual_salary <= 10000000:
            tax_rate = 0.40
        else:
            tax_rate = 0.45

        return annual_salary * tax_rate

    @staticmethod
    def calculate_hongkong_tax(annual_salary: float) -> float:
        """计算香港个人所得税"""
        # 香港薪俸税（2024年）
        # 基本免税额
        basic_allowance = 132000

        # 累进税率
        progressive_rates = [
            (50000, 0.02),
            (50000, 0.06),
            (50000, 0.10),
            (50000, 0.14),
            (50000, 0.17)
        ]

        # 标准税率
        standard_rate = 0.15

        # 计算累进税
        progressive_tax = 0
        remaining_income = max(annual_salary - basic_allowance, 0)

        for band, rate in progressive_rates:
            if remaining_income <= 0:
                break
            taxable_in_band = min(remaining_income, band)
            progressive_tax += taxable_in_band * rate
            remaining_income -= band

        # 计算标准税
        standard_tax = max(annual_salary - basic_allowance, 0) * standard_rate

        # 取较低者
        return min(progressive_tax, standard_tax)

    @staticmethod
    def calculate_singapore_tax(annual_salary: float) -> float:
        """计算新加坡个人所得税"""
        # 新加坡个税（2024年）
        if annual_salary <= 20000:
            tax_rate = 0.0
        elif annual_salary <= 30000:
            tax_rate = 0.02
        elif annual_salary <= 40000:
            tax_rate = 0.035
        elif annual_salary <= 80000:
            tax_rate = 0.07
        elif annual_salary <= 120000:
            tax_rate = 0.115
        elif annual_salary <= 160000:
            tax_rate = 0.15
        elif annual_salary <= 200000:
            tax_rate = 0.18
        elif annual_salary <= 320000:
            tax_rate = 0.20
        else:
            tax_rate = 0.22

        return annual_salary * tax_rate

    @staticmethod
    def calculate_japan_tax(annual_salary: float) -> float:
        """计算日本个人所得税（简化版）"""
        # 日本个税（2024年，简化）
        if annual_salary <= 1950000:
            tax_rate = 0.05
        elif annual_salary <= 3300000:
            tax_rate = 0.10
        elif annual_salary <= 6950000:
            tax_rate = 0.20
        elif annual_salary <= 9000000:
            tax_rate = 0.23
        elif annual_salary <= 18000000:
            tax_rate = 0.33
        elif annual_salary <= 40000000:
            tax_rate = 0.40
        else:
            tax_rate = 0.45

        return annual_salary * tax_rate

    @staticmethod
    def calculate_uk_tax(annual_salary: float) -> float:
        """计算英国个人所得税"""
        # 英国个税（2024年）
        personal_allowance = 12570

        if annual_salary <= personal_allowance:
            return 0

        taxable_income = annual_salary - personal_allowance

        if taxable_income <= 37700:
            tax_rate = 0.20
        elif taxable_income <= 125140:
            tax_rate = 0.40
        else:
            tax_rate = 0.45

        return taxable_income * tax_rate

    @staticmethod
    def calculate_australia_tax(annual_salary: float) -> float:
        """计算澳大利亚个人所得税"""
        # 澳大利亚个税（2024年）
        if annual_salary <= 18200:
            tax_rate = 0.0
        elif annual_salary <= 45000:
            tax_rate = 0.19
        elif annual_salary <= 120000:
            tax_rate = 0.325
        elif annual_salary <= 180000:
            tax_rate = 0.37
        else:
            tax_rate = 0.45

        return annual_salary * tax_rate

    @staticmethod
    def calculate_canada_tax(annual_salary: float) -> float:
        """计算加拿大个人所得税（联邦税，简化版）"""
        # 加拿大联邦税（2024年）
        basic_personal_amount = 15000

        if annual_salary <= basic_personal_amount:
            return 0

        taxable_income = annual_salary - basic_personal_amount

        if taxable_income <= 53359:
            tax_rate = 0.15
        elif taxable_income <= 106717:
            tax_rate = 0.205
        elif taxable_income <= 165430:
            tax_rate = 0.26
        elif taxable_income <= 235675:
            tax_rate = 0.29
        else:
            tax_rate = 0.33

        return taxable_income * tax_rate

def create_income_scenarios():
    """创建收入场景"""
    scenarios = []

    # 场景1: 最高收入 - 月薪5万人民币
    scenarios.append({
        'name': '高收入场景',
        'description': '月薪5万人民币（年收入60万）',
        'monthly_salary': 50000,
        'annual_salary': 600000,
        'income_level': 'high'
    })

    # 场景2: 最低收入 - 月薪5000人民币
    scenarios.append({
        'name': '低收入场景',
        'description': '月薪5000人民币（年收入6万）',
        'monthly_salary': 5000,
        'annual_salary': 60000,
        'income_level': 'low'
    })

    return scenarios

def calculate_after_tax_income(scenario: dict) -> dict:
    """计算税后收入"""
    annual_salary = scenario['annual_salary']

    # 计算各国个税
    tax_results = {
        'CNY': TaxCalculator.calculate_china_tax(annual_salary),
        'USD': TaxCalculator.calculate_usa_tax(annual_salary),
        'EUR': TaxCalculator.calculate_germany_tax(annual_salary),
        'TWD': TaxCalculator.calculate_taiwan_tax(annual_salary),
        'HKD': TaxCalculator.calculate_hongkong_tax(annual_salary),
        'SGD': TaxCalculator.calculate_singapore_tax(annual_salary),
        'JPY': TaxCalculator.calculate_japan_tax(annual_salary),
        'GBP': TaxCalculator.calculate_uk_tax(annual_salary),
        'AUD': TaxCalculator.calculate_australia_tax(annual_salary),
        'CAD': TaxCalculator.calculate_canada_tax(annual_salary)
    }

    # 转换为人民币进行对比
    after_tax_income = {}
    for currency, tax in tax_results.items():
        if currency == 'CNY':
            after_tax_income[currency] = annual_salary - tax
        else:
            # 转换为人民币
            converted_tax = converter.convert(tax, currency, 'CNY')
            after_tax_income[currency] = annual_salary - converted_tax

    return {
        'original_salary': annual_salary,
        'taxes': tax_results,
        'after_tax_income': after_tax_income
    }

def analyze_scenario(engine: PensionEngine, scenario: dict, tax_analysis: dict):
    """分析单个场景"""
    print(f"\n{'='*80}")
    print(f"场景: {scenario['name']}")
    print(f"描述: {scenario['description']}")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2015, 7, 1)
    )

    # 创建工资档案
    salary_profile = SalaryProfile(
        base_salary=scenario['monthly_salary'],
        annual_growth_rate=0.05
    )

    # 创建经济因素（人民币基准）
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CNY"
    )

    print(f"\n📊 收入分析:")
    print(f"  税前年收入: {converter.format_amount(scenario['annual_salary'], 'CNY')}")

    print(f"\n💰 各国个税对比:")
    for currency, tax in tax_analysis['taxes'].items():
        currency_name = converter.get_currency_name(currency)
        if currency == 'CNY':
            print(f"  {currency_name}: {converter.format_amount(tax, currency)}")
        else:
            cny_tax = converter.convert(tax, currency, 'CNY')
            print(f"  {currency_name}: {converter.format_amount(tax, currency)} (≈ {converter.format_amount(cny_tax, 'CNY')})")

    print(f"\n💵 税后收入对比:")
    for currency, income in tax_analysis['after_tax_income'].items():
        currency_name = converter.get_currency_name(currency)
        print(f"  {currency_name}: {converter.format_amount(income, 'CNY')}")

    # 计算退休金对比
    print(f"\n🏦 退休金计算中...")
    comparison_df = engine.compare_pensions(person, salary_profile, economic_factors)

    print(f"\n📈 退休金对比结果:")
    for _, row in comparison_df.iterrows():
        country_name = row['country_name']
        monthly_pension = row['monthly_pension']
        total_contribution = row['total_contribution']
        roi = row['roi']

        print(f"  {country_name}:")
        print(f"    月退休金: {converter.format_amount(monthly_pension, 'CNY')}")
        print(f"    总缴费: {converter.format_amount(total_contribution, 'CNY')}")
        print(f"    投资回报率: {roi:.1%}")

    return comparison_df

def generate_summary_report(scenarios: list, all_results: list):
    """生成总结报告"""
    print(f"\n{'='*80}")
    print(f"📋 总结报告")
    print(f"{'='*80}")

    for i, scenario in enumerate(scenarios):
        print(f"\n🎯 {scenario['name']}:")
        print(f"   税前年收入: {converter.format_amount(scenario['annual_salary'], 'CNY')}")

        # 找出退休金最高的国家
        if i < len(all_results):
            result_df = all_results[i]
            if not result_df.empty:
                max_country = result_df.loc[result_df['monthly_pension'].idxmax()]
                print(f"   退休金最高: {max_country['country_name']} ({converter.format_amount(max_country['monthly_pension'], 'CNY')}/月)")

                min_country = result_df.loc[result_df['monthly_pension'].idxmin()]
                print(f"   退休金最低: {min_country['country_name']} ({converter.format_amount(min_country['monthly_pension'], 'CNY')}/月)")

def main():
    """主函数"""
    print("=== 考虑个人所得税的收入场景分析 ===\n")

    # 创建计算引擎
    engine = PensionEngine()

    # 注册所有国家计算器
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

    print(f"已注册 {len(engine.get_available_countries())} 个国家/地区的计算器")

    # 创建收入场景
    scenarios = create_income_scenarios()

    # 分析每个场景
    all_results = []
    for scenario in scenarios:
        # 计算个税分析
        tax_analysis = calculate_after_tax_income(scenario)

        # 分析退休金
        result_df = analyze_scenario(engine, scenario, tax_analysis)
        all_results.append(result_df)

    # 生成总结报告
    generate_summary_report(scenarios, all_results)

    print(f"\n✅ 分析完成！")
    print(f"共分析了 {len(scenarios)} 个收入场景")

if __name__ == "__main__":
    main()
