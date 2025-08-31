#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
货币转换示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator
from utils.currency_converter import converter, CurrencyConverter

def test_currency_converter():
    """测试汇率转换器"""
    print("=== 汇率转换器测试 ===\n")

    # 测试汇率获取
    print("获取汇率数据...")
    rates = converter.get_exchange_rates()
    print(f"当前汇率 (基准货币: {converter.base_currency}):")
    for currency, rate in rates.items():
        currency_name = converter.get_currency_name(currency)
        print(f"  {currency} ({currency_name}): {rate:.4f}")

    print(f"\n最后更新时间: {converter.last_update}")

    # 测试货币转换
    print("\n=== 货币转换测试 ===")

    # 人民币转美元
    cny_amount = 10000
    usd_amount = converter.convert(cny_amount, "CNY", "USD")
    print(f"{converter.format_amount(cny_amount, 'CNY')} = {converter.format_amount(usd_amount, 'USD')}")

    # 美元转欧元
    eur_amount = converter.convert(usd_amount, "USD", "EUR")
    print(f"{converter.format_amount(usd_amount, 'USD')} = {converter.format_amount(eur_amount, 'EUR')}")

    # 欧元转人民币
    cny_back = converter.convert(eur_amount, "EUR", "CNY")
    print(f"{converter.format_amount(eur_amount, 'EUR')} = {converter.format_amount(cny_back, 'CNY')}")

    # 测试不同基准货币
    print("\n=== 不同基准货币测试 ===")

    # 创建美元基准的转换器
    usd_converter = CurrencyConverter("USD")
    usd_rates = usd_converter.get_exchange_rates()

    print(f"美元基准汇率:")
    for currency, rate in list(usd_rates.items())[:5]:  # 只显示前5个
        currency_name = usd_converter.get_currency_name(currency)
        print(f"  {currency} ({currency_name}): {rate:.4f}")

def test_pension_with_currency():
    """测试带货币转换的退休金计算"""
    print("\n=== 退休金货币转换测试 ===\n")

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

    # 测试1: 人民币基准
    print("测试1: 人民币基准")
    economic_cny = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CNY"
    )

    comparison_cny = engine.compare_pensions(person, salary_profile, economic_cny)
    print("退休金对比 (人民币):")
    for _, row in comparison_cny.iterrows():
        print(f"  {row['country_name']}: {converter.format_amount(row['monthly_pension'], 'CNY')}/月")

    # 测试2: 美元显示
    print("\n测试2: 美元显示")
    economic_usd = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="USD"
    )

    comparison_usd = engine.compare_pensions(person, salary_profile, economic_usd)
    print("退休金对比 (美元):")
    for _, row in comparison_usd.iterrows():
        print(f"  {row['country_name']}: {converter.format_amount(row['monthly_pension'], 'USD')}/月")

    # 测试3: 欧元显示
    print("\n测试3: 欧元显示")
    economic_eur = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="EUR"
    )

    comparison_eur = engine.compare_pensions(person, salary_profile, economic_eur)
    print("退休金对比 (欧元):")
    for _, row in comparison_eur.iterrows():
        print(f"  {row['country_name']}: {converter.format_amount(row['monthly_pension'], 'EUR')}/月")

def test_currency_formatting():
    """测试货币格式化"""
    print("\n=== 货币格式化测试 ===")

    test_amounts = [1234.56, 1000000, 0.99, 999999.99]

    for amount in test_amounts:
        print(f"\n金额: {amount}")
        for currency in ['CNY', 'USD', 'EUR', 'GBP', 'JPY', 'HKD']:
            formatted = converter.format_amount(amount, currency)
            print(f"  {currency}: {formatted}")

def main():
    """主函数"""
    print("开始货币转换测试...\n")

    try:
        # 1. 测试汇率转换器
        test_currency_converter()

        # 2. 测试退休金货币转换
        test_pension_with_currency()

        # 3. 测试货币格式化
        test_currency_formatting()

        print("\n所有测试完成！")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
