#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis runner for coordinating pension system analysis
"""

from datetime import date
from core.pension_engine import PensionEngine
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from utils.common import converter, get_country_currency, create_standard_person, create_standard_salary_profile, create_standard_economic_factors

def analyze_scenario(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析单个场景"""
    print(f"\n{'='*80}")
    print(f"📊 {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 35年")
    print(f"退休年龄: 按各国实际年龄")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建标准对象
    person = create_standard_person()
    salary_profile = create_standard_salary_profile(monthly_salary)
    economic_factors = create_standard_economic_factors()

    # 计算退休金对比
    print(f"\n🏦 正在计算退休金对比...")
    comparison_df = engine.compare_pensions(person, salary_profile, economic_factors)

    print(f"\n📈 退休金对比结果:")
    print(f"{'排名':<4} {'国家/地区':<12} {'退休年龄':<8} {'月退休金':<15} {'总缴费':<15} {'投资回报率':<12}")
    print("-" * 75)

    for i, (_, row) in enumerate(comparison_df.iterrows(), 1):
        # 获取该国的实际退休年龄
        country_code = row['country']
        calculator = engine.calculators[country_code]
        retirement_age = calculator.get_retirement_age(person)

        print(f"{i:>2}.  {row['country_name']:<10} {retirement_age:>6}岁  {converter.format_amount(row['monthly_pension'], 'CNY'):<15} {converter.format_amount(row['total_contribution'], 'CNY'):<15} {row['roi']:>8.1%}")

    # 计算统计信息
    avg_pension = comparison_df['monthly_pension'].mean()
    max_country = comparison_df.loc[comparison_df['monthly_pension'].idxmax()]
    min_country = comparison_df.loc[comparison_df['monthly_pension'].idxmin()]

    print(f"\n📊 统计信息:")
    print(f"  平均月退休金: {converter.format_amount(avg_pension, 'CNY')}")
    print(f"  最高退休金: {max_country['country_name']} ({converter.format_amount(max_country['monthly_pension'], 'CNY')})")
    print(f"  最低退休金: {min_country['country_name']} ({converter.format_amount(min_country['monthly_pension'], 'CNY')})")

    return comparison_df

def analyze_by_country(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """按国家分别分析场景"""
    print(f"\n{'='*80}")
    print(f"🌍 {scenario_name} - 按国家分别输出")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 35年")
    print(f"退休年龄: 按各国实际年龄")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建标准对象
    person = create_standard_person()
    salary_profile = create_standard_salary_profile(monthly_salary)
    economic_factors = create_standard_economic_factors()

    for country_code, calculator in engine.calculators.items():
        print(f"\n🏛️  {calculator.country_name} ({country_code})")
        print("-" * 50)
        
        # 设置该国的货币显示
        local_currency = get_country_currency(country_code)
        local_economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency=local_currency
        )
        
        try:
            local_result = calculator.calculate_pension(person, salary_profile, local_economic_factors)
            
            retirement_age = calculator.get_retirement_age(person)
            contribution_rates = calculator.contribution_rates
            
            print(f"退休年龄: {retirement_age}岁")
            print(f"总缴费率: {contribution_rates['total']:.1%}")
            print(f"员工缴费率: {contribution_rates['employee']:.1%}")
            print(f"雇主缴费率: {contribution_rates['employer']:.1%}")
            print(f"月退休金: {converter.format_amount(local_result.monthly_pension, local_currency)}")
            print(f"总缴费: {converter.format_amount(local_result.total_contribution, local_currency)}")
            print(f"总收益: {converter.format_amount(local_result.total_benefit, local_currency)}")
            print(f"投资回报率: {local_result.roi:.1%}")
            print(f"回本年龄: {local_result.break_even_age}岁" if local_result.break_even_age else "回本年龄: 无法计算")
            
            # 显示特定国家的详细信息
            if 'details' in local_result.details:
                details = local_result.details
                if 'social_security_pension' in details:
                    print(f"社会保障金: {converter.format_amount(details['social_security_pension'], local_currency)}")
                if 'k401_monthly_pension' in details:
                    print(f"401K月退休金: {converter.format_amount(details['k401_monthly_pension'], local_currency)}")
                if 'k401_balance' in details:
                    print(f"401K账户余额: {converter.format_amount(details['k401_balance'], local_currency)}")
                    
        except Exception as e:
            print(f"计算 {calculator.country_name} 退休金时出错: {e}")

def analyze_countries_comparison(engine: PensionEngine, country_codes: list, monthly_salary: float = 10000):
    """对比指定国家的退休金"""
    # 验证国家代码
    valid_codes = []
    country_names = []
    for code in country_codes:
        if code in engine.calculators:
            valid_codes.append(code)
            country_names.append(engine.calculators[code].country_name)
        else:
            print(f"警告: 未找到国家代码 '{code}' 对应的计算器")
    
    if len(valid_codes) < 2:
        print("错误: 需要至少2个有效的国家代码进行对比")
        return
    
    print(f"\n{'='*80}")
    print(f"🌐 多国养老金对比")
    print(f"对比国家: {', '.join(country_codes)}")
    print(f"对比国家: {', '.join(country_names)}")
    print(f"{'='*80}")

    person = create_standard_person()
    
    print(f"\n📊 月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print("-" * 50)
    
    salary_profile = create_standard_salary_profile(monthly_salary)
    
    results = []
    for code in valid_codes:
        if code in engine.calculators:
            calculator = engine.calculators[code]
            local_currency = get_country_currency(code)
            
            economic_factors = EconomicFactors(
                inflation_rate=0.03,
                investment_return_rate=0.07,
                social_security_return_rate=0.05,
                base_currency="CNY",
                display_currency=local_currency
            )
            
            try:
                result = calculator.calculate_pension(person, salary_profile, economic_factors)
                results.append({
                    'country_name': calculator.country_name,
                    'country_code': code,
                    'monthly_pension': result.monthly_pension,
                    'total_contribution': result.total_contribution,
                    'roi': result.roi,
                    'break_even_age': result.break_even_age,
                    'currency': local_currency,
                    'details': result.details
                })
            except Exception as e:
                print(f"计算 {calculator.country_name} 时出错: {e}")
    
    # 按月退休金排序
    results.sort(key=lambda x: x['monthly_pension'], reverse=True)
    
    for i, result in enumerate(results, 1):
        print(f"\n🏛️  {result['country_name']} ({result['country_code']})")
        print(f"   排名: {i}")
        print(f"   月退休金: {converter.format_amount(result['monthly_pension'], result['currency'])}")
        print(f"   总缴费: {converter.format_amount(result['total_contribution'], result['currency'])}")
        print(f"   投资回报率: {result['roi']:.1%}")
        print(f"   回本年龄: {result['break_even_age']}岁" if result['break_even_age'] else "回本年龄: 无法计算")
        
        # 显示特定国家的详细信息
        details = result['details']
        if result['country_code'] == 'US' and 'social_security_pension' in details:
            print(f"   Social Security: {converter.format_amount(details['social_security_pension'], 'USD')}/月")
            if 'k401_monthly_pension' in details:
                print(f"   401K: {converter.format_amount(details['k401_monthly_pension'], 'USD')}/月")
        elif result['country_code'] == 'CN' and 'basic_pension' in details:
            print(f"   基础养老金: {converter.format_amount(details['basic_pension'], 'CNY')}/月")
            if 'account_pension' in details:
                print(f"   个人账户养老金: {converter.format_amount(details['account_pension'], 'CNY')}/月")