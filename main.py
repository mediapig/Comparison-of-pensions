#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休金对比系统 - 主程序
计算两个固定场景：月薪5万和5千人民币，工作30年，按各国实际退休年龄，领取20年
支持按国家分别输出，使用当地货币单位
支持只输出美国分析（使用 --usa-only 参数）
"""

import sys
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator
from plugins.taiwan.taiwan_calculator import TaiwanPensionCalculator
from plugins.hongkong.hongkong_calculator import HongKongPensionCalculator
from plugins.singapore.singapore_calculator import SingaporePensionCalculator
from plugins.japan.japan_calculator import JapanPensionCalculator
from plugins.uk.uk_calculator import UKPensionCalculator
from plugins.australia.australia_calculator import AustraliaPensionCalculator
from plugins.canada.canada_calculator import CanadaPensionCalculator
from utils.currency_converter import converter

def create_pension_engine():
    """创建并注册所有国家计算器"""
    engine = PensionEngine()

    calculators = [
        ChinaPensionCalculator(),
        USAPensionCalculator(),
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

def get_country_currency(country_code: str) -> str:
    """获取各国货币代码"""
    currency_map = {
        'CN': 'CNY',  # 中国 - 人民币
        'US': 'USD',  # 美国 - 美元
        'TW': 'TWD',  # 台湾 - 新台币
        'HK': 'HKD',  # 香港 - 港币
        'SG': 'SGD',  # 新加坡 - 新币
        'JP': 'JPY',  # 日本 - 日元
        'UK': 'GBP',  # 英国 - 英镑
        'AU': 'AUD',  # 澳大利亚 - 澳币
        'CA': 'CAD'   # 加拿大 - 加币
    }
    return currency_map.get(country_code, 'CNY')

def analyze_usa_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析美国养老金"""
    print(f"\n{'='*80}")
    print(f"🇺🇸 美国养老金详细分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 30年")
    print(f"退休年龄: 65岁")
    print(f"领取年限: 20年")
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
        base_salary=monthly_salary,
        annual_growth_rate=0.02
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="USD"
    )

    # 获取美国计算器
    usa_calculator = engine.calculators['US']

    print(f"\n🏦 正在计算美国养老金...")

    # 1. 基础养老金计算
    print(f"\n📊 基础养老金计算结果:")
    print("-" * 50)

    basic_result = usa_calculator.calculate_pension(person, salary_profile, economic_factors)

    print(f"月退休金: {converter.format_amount(basic_result.monthly_pension, 'USD')}")
    print(f"总缴费: {converter.format_amount(basic_result.total_contribution, 'USD')}")
    print(f"总收益: {converter.format_amount(basic_result.total_benefit, 'USD')}")
    print(f"投资回报率: {basic_result.roi:.1%}")
    print(f"回本年龄: {basic_result.break_even_age}岁" if basic_result.break_even_age else "回本年龄: 无法计算")

    # 2. 401K详细分析
    print(f"\n🔍 401K详细分析:")
    print("-" * 50)

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
    print(f"\n📋 缴费上限分析:")
    print("-" * 50)

    # 显示2025年401K准确的上限信息
    print(f"2025年401K缴费上限:")
    print(f"  • 402(g) 员工递延上限：$23,500")
    print(f"  • 50+ catch-up：$7,500")
    print(f"  • 60–63 super catch-up：$11,250（替代 $7,500；计划需支持）")
    print(f"  • 415(c) 员工+雇主合计上限：$70,000（不含 catch-up）")
    print(f"  • 60–63岁可递延总额 = $23,500 + $11,250 = $34,750")

    # 显示当前年龄信息
    age_limits = k401_analysis['age_limits']
    print(f"\n当前年龄: {age_limits['current_age']}岁")

    # 4. 雇主配比分析
    print(f"\n💼 雇主配比分析:")
    print("-" * 50)

    employer_match = k401_analysis['employer_match_sample']
    print(f"年工资: {converter.format_amount(employer_match['salary'], 'USD')}")
    print(f"员工缴费: {converter.format_amount(employer_match['employee_contribution'], 'USD')}")
    print(f"雇主配比: {converter.format_amount(employer_match['employer_match'], 'USD')}")
    print(f"401K总额: {converter.format_amount(employer_match['total_401k'], 'USD')}")

    # 5. 不同缴费比例场景
    print(f"\n📈 不同缴费比例场景分析:")
    print("-" * 50)

    # 将人民币月薪转换为美元
    cny_to_usd_rate = 0.14
    monthly_salary_usd = monthly_salary * cny_to_usd_rate
    scenarios = usa_calculator.get_contribution_scenarios(
        monthly_salary_usd * 12, 30, 0.07
    )

    print(f"{'缴费比例':<10} {'年缴费':<15} {'30年后余额':<20} {'月退休金':<15}")
    print("-" * 60)

    for scenario in scenarios:
        print(f"{scenario['deferral_rate']:>8.1%}  {converter.format_amount(scenario['annual_contribution'], 'USD'):<15} {converter.format_amount(scenario['future_value'], 'USD'):<20} {converter.format_amount(scenario['monthly_pension'], 'USD'):<15}")

    # 6. 缴费历史详情
    print(f"\n📅 缴费历史详情（前5年和后5年）:")
    print("-" * 50)

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
    print(f"\n📋 总结:")
    print("-" * 50)

            # 计算替代率 - 使用美元工资计算
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

def analyze_scenario(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """分析单个场景"""
    print(f"\n{'='*80}")
    print(f"📊 {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 30年")
    print(f"退休年龄: 按各国实际年龄")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息 - 固定工作30年
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),  # 1990年出生
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)  # 1995年开始工作，工作到2025年，正好30年
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CNY"
    )

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

def analyze_hk_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析香港MPF"""
    print(f"\n{'='*80}")
    print(f"🇭🇰 香港MPF分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 35年")
    print(f"退休年龄: 65岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="HKD"
    )

    # 获取香港计算器
    hk_calculator = engine.calculators['HK']

    print(f"\n🏦 正在计算香港MPF...")

    # 计算香港MPF
    result = hk_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 MPF计算结果:")
    print("-" * 50)
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'HKD')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'HKD')}")
    print(f"总收益: {converter.format_amount(result.details['total_return'], 'HKD')}")
    print(f"投资回报率: {result.details['roi_pct']:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示账户详情
    details = result.details
    print(f"\n🔍 MPF账户详情:")
    print("-" * 50)
    print(f"MPF账户余额: {converter.format_amount(details['mpf_balance'], 'HKD')}")
    print(f"员工供款: {converter.format_amount(details['employee_contrib'], 'HKD')}")
    print(f"雇主供款: {converter.format_amount(details['employer_contrib'], 'HKD')}")
    print(f"总供款: {converter.format_amount(details['total_contrib'], 'HKD')}")

    # 显示缴费率信息
    contribution_rates = hk_calculator.contribution_rates
    print(f"\n💰 缴费率信息:")
    print("-" * 50)
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: 5.0% (固定)")
    print(f"总缴费率: 10.0% (员工5% + 雇主5%)")

    # 计算替代率
    annual_salary_hkd = monthly_salary * 1.08 * 12  # 转换为港币年工资（假设汇率1.08）
    replacement_rate = (result.monthly_pension * 12) / annual_salary_hkd * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_hkd, 'HKD')} (HK$)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'HKD')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_singapore_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析新加坡CPF"""
    # 获取实际参数
    sg_calculator = engine.calculators['SG']
    retirement_age = sg_calculator.get_retirement_age(Person(name="test", birth_date=date(1990, 1, 1), gender=Gender.MALE, employment_type=EmploymentType.EMPLOYEE, start_work_date=date(1995, 7, 1)))
    start_age = 30  # 固定30岁开始工作
    work_years = retirement_age - start_age  # 35年
    life_expectancy = 85
    collection_years = life_expectancy - retirement_age  # 20年
    
    print(f"\n{'='*80}")
    print(f"🇸🇬 新加坡CPF分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: {work_years}年")
    print(f"退休年龄: {retirement_age}岁")
    print(f"预期寿命: {life_expectancy}岁 (预计领取{collection_years}年)")
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
        base_salary=monthly_salary,
        annual_growth_rate=0.02
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="SGD"
    )

    # 获取新加坡计算器
    sg_calculator = engine.calculators['SG']

    print(f"\n🏦 正在计算新加坡CPF...")

    # 计算新加坡CPF
    result = sg_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 CPF计算结果:")
    print("-" * 50)
    # 显示月退休金和CPF LIFE区间
    details = result.details
    monthly_payout = details.get('monthly_payout', result.monthly_pension)
    cpf_life_low = details.get('cpf_life_low', 0)
    cpf_life_high = details.get('cpf_life_high', 0)
    
    print(f"月退休金: {converter.format_amount(monthly_payout, 'SGD')} (CPF LIFE参考区间：S${cpf_life_low:,}–S${cpf_life_high:,}/月)")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'SGD')}")
    print(f"总收益: {converter.format_amount(result.total_benefit, 'SGD')}")
    print(f"投资回报率: {result.roi:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示账户详情
    details = result.details
    print(f"\n🔍 CPF账户详情:")
    print("-" * 50)
    print(f"OA账户余额: {converter.format_amount(details['oa_balance'], 'SGD')}")
    print(f"SA账户余额: {converter.format_amount(details['sa_balance'], 'SGD')}")
    print(f"MA账户余额: {converter.format_amount(details['ma_balance'], 'SGD')}")
    print(f"RA退休账户: {converter.format_amount(details['ra_balance'], 'SGD')}")
    print(f"退休等级: {details.get('tier', 'Unknown')}")

    # 显示缴费率信息
    contribution_rates = sg_calculator.contribution_rates
    print(f"\n💰 缴费率信息:")
    print("-" * 50)
    print(f"总缴费率: {contribution_rates['total']:.1%}")
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

        # 计算替代率 - 用新币计算，因为CPF退休金是新币
    annual_salary_sgd = monthly_salary * 0.19 * 12  # 转换为新币年工资
    replacement_rate = (result.monthly_pension * 12) / annual_salary_sgd * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_sgd, 'SGD')} (S$)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'SGD')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_china_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析中国养老金"""
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
        base_salary=monthly_salary,
        annual_growth_rate=0.02
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CNY"
    )

    print(f"\n🏦 正在计算中国养老金...")

    # 计算中国养老金
    result = cn_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 养老金计算结果:")
    print("-" * 50)
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'CNY')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'CNY')}")
    print(f"总收益: {converter.format_amount(result.total_benefit, 'CNY')}")
    print(f"投资回报率: {result.roi:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示账户详情
    details = result.details
    print(f"\n🔍 养老金账户详情:")
    print("-" * 50)
    if 'basic_pension' in details:
        print(f"基础养老金: {converter.format_amount(details['basic_pension'], 'CNY')}")
    if 'personal_account_pension' in details:
        print(f"个人账户养老金: {converter.format_amount(details['personal_account_pension'], 'CNY')}")

    # 显示缴费率信息
    contribution_rates = cn_calculator.contribution_rates
    print(f"\n💰 缴费率信息:")
    print("-" * 50)
    print(f"总缴费率: {contribution_rates['total']:.1%}")
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    # 计算替代率
    annual_salary = monthly_salary * 12
    replacement_rate = (result.monthly_pension * 12) / annual_salary * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(annual_salary, 'CNY')}")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'CNY')}")
    print(f"替代率: {replacement_rate:.1f}%")


def analyze_taiwan_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析台湾养老金"""
    # 获取实际参数
    tw_calculator = engine.calculators['TW']
    retirement_age = 65  # Taiwan retirement age
    start_age = 30
    work_years = retirement_age - start_age  # 65-30 = 35
    
    print(f"\n{'='*80}")
    print(f"🇹🇼 台湾养老金分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: {work_years}年")
    print(f"退休年龄: {retirement_age}岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="TWD"
    )

    # 获取台湾计算器
    tw_calculator = engine.calculators['TW']

    print(f"\n🏦 正在计算台湾养老金...")

    # 计算台湾养老金
    result = tw_calculator.calculate_pension(person, salary_profile, economic_factors)

    # —— 隐藏/移除 DB 不适用的块 —— #
    # 检查是否为DB制系统
    if not result.details.get('hide_summary', False):
        # 显示基本信息 (非DB系统)
        print(f"\n📊 养老金计算结果:")
        print("-" * 50)
        print(f"月退休金: {converter.format_amount(result.monthly_pension, 'TWD')}")
        print(f"总缴费: {converter.format_amount(result.total_contribution, 'TWD')}")
        print(f"总收益: {converter.format_amount(result.total_benefit, 'TWD')}")
        print(f"投资回报率: {result.roi:.1%}")
        print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

        # 显示缴费率信息
        contribution_rates = tw_calculator.contribution_rates
        print(f"\n💰 缴费率信息:")
        print("-" * 50)
        print(f"总缴费率: {contribution_rates['total']:.1%}")
        print(f"员工缴费率: {contribution_rates['employee']:.1%}")
        print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

        # 计算替代率
        annual_salary_twd = monthly_salary * 4.4 * 12  # 转换为新台币年工资
        replacement_rate = (result.monthly_pension * 12) / annual_salary_twd * 100

        print(f"\n📋 总结:")
        print("-" * 50)
        print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
        print(f"年工资: {converter.format_amount(annual_salary_twd, 'TWD')} (NT$)")
        print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'TWD')}")
        print(f"替代率: {replacement_rate:.1f}%")

def analyze_japan_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析日本养老金"""
    # 获取实际参数
    jp_calculator = engine.calculators['JP']
    retirement_age = 65  # Japan retirement age
    start_age = 30
    work_years = retirement_age - start_age  # 65-30 = 35
    
    print(f"\n{'='*80}")
    print(f"🇯🇵 日本养老金分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: {work_years}年")
    print(f"退休年龄: {retirement_age}岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="JPY"
    )

    print(f"\n🏦 正在计算日本养老金...")

    # 计算日本养老金
    result = jp_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 养老金计算结果:")
    print("-" * 50)
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'JPY')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'JPY')}")
    print("总收益: N/A（DB制）")
    print("投资回报率: N/A（DB制）")
    print("回本年龄: N/A（DB制）")

    # 显示缴费率信息
    print(f"\n💰 缴费率信息（厚生年金，统计口径）:")
    print("-" * 50)
    print("合计费率: 18.3% ＝ 员工 9.15% + 雇主 9.15%")
    
    # 显示累计缴费金额
    EPI_RATE_TOTAL = 0.183
    EPI_RATE_EMP   = 0.0915
    EPI_RATE_ER    = 0.0915
    epi_contrib_total = result.total_contribution
    epi_contrib_emp   = epi_contrib_total * (EPI_RATE_EMP / EPI_RATE_TOTAL)
    epi_contrib_er    = epi_contrib_total * (EPI_RATE_ER  / EPI_RATE_TOTAL)
    print(f"累计缴费（合计）: {converter.format_amount(epi_contrib_total, 'JPY')} ＝ 员工 {converter.format_amount(epi_contrib_emp, 'JPY')} + 雇主 {converter.format_amount(epi_contrib_er, 'JPY')}")

    # 计算替代率
    annual_salary_jpy = monthly_salary * 20 * 12  # 转换为日元年工资
    replacement_rate = (result.monthly_pension * 12) / annual_salary_jpy * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_jpy, 'JPY')} (¥)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'JPY')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_uk_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析英国养老金"""
    # 获取实际参数
    uk_calculator = engine.calculators['UK']
    retirement_age = 68  # UK retirement age
    start_age = 30
    work_years = retirement_age - start_age  # 68-30 = 38
    
    print(f"\n{'='*80}")
    print(f"🇬🇧 英国养老金分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: {work_years}年")
    print(f"退休年龄: {retirement_age}岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="GBP"
    )

    # 获取英国计算器
    uk_calculator = engine.calculators['UK']

    print(f"\n🏦 正在计算英国养老金...")

    # 计算英国养老金
    result = uk_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 养老金计算结果:")
    print("-" * 50)
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'GBP')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'GBP')}")
    print(f"总收益: {converter.format_amount(result.total_benefit, 'GBP')}")
    print(f"投资回报率: {result.roi:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示缴费率信息
    contribution_rates = uk_calculator.contribution_rates
    print(f"\n💰 缴费率信息:")
    print("-" * 50)
    print(f"总缴费率: {contribution_rates['total']:.1%}")
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    # 计算替代率
    annual_salary_gbp = monthly_salary * 0.11 * 12  # 转换为英镑年工资
    replacement_rate = (result.monthly_pension * 12) / annual_salary_gbp * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_gbp, 'GBP')} (£)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'GBP')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_australia_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析澳大利亚养老金"""
    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 获取澳大利亚计算器
    au_calculator = engine.calculators['AU']
    
    # 获取实际退休年龄和工作年限
    retirement_age = au_calculator.get_retirement_age(person)
    start_work_age = 30  # 固定30岁开始工作
    work_years = retirement_age - start_work_age
    
    print(f"\n{'='*80}")
    print(f"🇦🇺 澳大利亚养老金分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: {work_years}年")
    print(f"退休年龄: {retirement_age}岁")
    print(f"预期寿命: 85岁 (预计领取{85-retirement_age}年)")
    print(f"{'='*80}")

    # 创建工资档案 - 工资每年增长2%
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.02
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="AUD"
    )

    print(f"\n🏦 正在计算澳大利亚养老金...")

    # 计算澳大利亚养老金
    result = au_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示基本信息
    print(f"\n📊 养老金计算结果:")
    print("-" * 50)
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'AUD')}")
    print(f"总缴费: {converter.format_amount(result.total_contribution, 'AUD')}")
    print(f"总收益: {converter.format_amount(result.total_benefit, 'AUD')}")
    print(f"投资回报率: {result.roi:.1%}")
    print(f"回本年龄: {result.break_even_age}岁" if result.break_even_age else "回本年龄: 无法计算")

    # 显示缴费率信息
    contribution_rates = au_calculator.contribution_rates
    print(f"\n💰 缴费率信息:")
    print("-" * 50)
    print(f"总缴费率: {contribution_rates['total']:.1%}")
    print(f"员工缴费率: {contribution_rates['employee']:.1%}")
    print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

    # 使用计算器内部计算的替代率
    replacement_rate = result.details.get('replacement_rate', 0) * 100
    last_year_salary = result.details.get('last_year_salary', 0)

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"初始年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"初始年工资: {converter.format_amount(monthly_salary * 0.21 * 12, 'AUD')} (A$)")
    print(f"最后一年工资: {converter.format_amount(last_year_salary, 'AUD')} (A$)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'AUD')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_canada_only(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """只分析加拿大养老金"""
    print(f"\n{'='*80}")
    print(f"🇨🇦 加拿大养老金分析 - {scenario_name}")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 35年")
    print(f"退休年龄: 65岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CAD"
    )

    # 获取加拿大计算器
    ca_calculator = engine.calculators['CA']

    print(f"\n🏦 正在计算加拿大养老金...")

    # 计算加拿大养老金
    result = ca_calculator.calculate_pension(person, salary_profile, economic_factors)

    # 显示给付信息（公共年金制）
    cpp_annual = result.details.get('cpp_monthly', 0) * 12
    oas_annual = result.details.get('oas_monthly', 0) * 12
    annual_pension = result.monthly_pension * 12
    
    print(f"\n📊 养老金给付（公共年金制：CPP + OAS）")
    print("-" * 50)
    print(f"  CPP: {converter.format_amount(cpp_annual, 'CAD')}/年 | OAS: {converter.format_amount(oas_annual, 'CAD')}/年")
    print(f"  合计: {converter.format_amount(annual_pension, 'CAD')}/年 ≈ {converter.format_amount(result.monthly_pension, 'CAD')}/月")

    # 显示缴费统计信息
    print(f"\n💰 CPP 累计缴费（仅统计口径）")
    print("-" * 50)
    print("  合计费率: 11.9% = 员工 5.95% + 雇主 5.95%")
    print(f"  累计缴费（合计）: {converter.format_amount(result.total_contribution * 2, 'CAD')}")
    
    print(f"\nℹ️ 说明：CPP 与 OAS 为公共年金（DB/准DB），不计算总收益、投资回报率与回本年龄。")
    print("    OAS = 734.95(2025Q3, 65–74) × 12 × (居住年限/40) = 734.95×12×(35/40) ≈ 7,716.98/年")
    print("    CPP 满额口径采用：17,196/年（2025），并按年资与平均可计缴工资比例折算")

    # 计算替代率
    annual_salary_cad = monthly_salary * 0.19 * 12  # 转换为加币年工资
    replacement_rate = (result.monthly_pension * 12) / annual_salary_cad * 100

    print(f"\n📋 总结:")
    print("-" * 50)
    print(f"年工资: {converter.format_amount(monthly_salary * 12, 'CNY')} (¥)")
    print(f"年工资: {converter.format_amount(annual_salary_cad, 'CAD')} (C$)")
    print(f"退休后年养老金: {converter.format_amount(result.monthly_pension * 12, 'CAD')}")
    print(f"替代率: {replacement_rate:.1f}%")

def analyze_by_country(engine: PensionEngine, scenario_name: str, monthly_salary: float):
    """按国家分别分析场景"""
    print(f"\n{'='*80}")
    print(f"🌍 {scenario_name} - 按国家分别输出")
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 30年")
    print(f"退休年龄: 按各国实际年龄")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

    # 创建个人信息
    person = Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1995, 7, 1)
    )

    # 创建工资档案 - 工资不增长
    salary_profile = SalaryProfile(
        base_salary=monthly_salary,
        annual_growth_rate=0.00
    )

    # 创建经济因素
    economic_factors = EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency="CNY",
        display_currency="CNY"
    )

    # 按国家分别计算
    for country_code, calculator in engine.calculators.items():
        print(f"\n🏛️  {calculator.country_name} ({country_code})")
        print("-" * 50)

        # 获取该国货币
        local_currency = get_country_currency(country_code)

        # 计算该国退休金
        try:
            result = calculator.calculate_pension(person, salary_profile, economic_factors)

            # 转换为当地货币显示
            if result.original_currency != local_currency:
                local_result = result.convert_to_currency(local_currency, converter)
            else:
                local_result = result

            # 获取退休年龄
            retirement_age = calculator.get_retirement_age(person)

            print(f"退休年龄: {retirement_age}岁")

            # 显示缴费率信息
            contribution_rates = calculator.contribution_rates
            if 'total' in contribution_rates:
                print(f"总缴费率: {contribution_rates['total']:.1%}")
            if 'employee' in contribution_rates and 'employer' in contribution_rates:
                print(f"员工缴费率: {contribution_rates['employee']:.1%}")
                print(f"雇主缴费率: {contribution_rates['employer']:.1%}")

            print(f"月退休金: {converter.format_amount(local_result.monthly_pension, local_currency)}")
            print(f"总缴费: {converter.format_amount(local_result.total_contribution, local_currency)}")
            print(f"总收益: {converter.format_amount(local_result.total_benefit, local_currency)}")
            print(f"投资回报率: {local_result.roi:.1%}")
            print(f"回本年龄: {local_result.break_even_age}岁" if local_result.break_even_age else "回本年龄: 无法计算")

            # 显示详细信息
            if 'details' in local_result.details:
                details = local_result.details
                if 'social_security_pension' in details:
                    print(f"社会保障金: {converter.format_amount(details['social_security_pension'], local_currency)}")
                if 'k401_monthly_pension' in details:
                    print(f"401K月退休金: {converter.format_amount(details['k401_monthly_pension'], local_currency)}")
                if 'k401_balance' in details:
                    print(f"401K账户余额: {converter.format_amount(details['k401_balance'], local_currency)}")

        except Exception as e:
            print(f"计算出错: {str(e)}")

def analyze_countries_comparison(engine: PensionEngine, country_codes: list):
    """分析指定国家的养老金对比"""
    country_names = []
    for code in country_codes:
        if code in engine.calculators:
            country_names.append(engine.calculators[code].country_name)
    
    countries_str = "、".join(country_names)
    print(f"🌍 === {countries_str}养老金对比分析系统 ===")
    print(f"对比国家: {', '.join(country_codes)}")
    print(f"分析两个收入场景的退休金情况\n")

    # 定义两个场景
    scenarios = [
        ("高收入场景", 50000),  # 月薪5万人民币
        ("低收入场景", 5000)    # 月薪5千人民币
    ]

    for scenario_name, monthly_salary in scenarios:
        print(f"\n{'='*80}")
        print(f"📊 {scenario_name} - 月薪: {converter.format_amount(monthly_salary, 'CNY')}")
        print(f"{'='*80}")

        # 创建个人信息
        person = Person(
            name="测试用户",
            birth_date=date(1990, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(1995, 7, 1)
        )

        # 创建工资档案
        salary_profile = SalaryProfile(
            base_salary=monthly_salary,
            annual_growth_rate=0.02
        )

        # 创建经济因素
        economic_factors = EconomicFactors(
            inflation_rate=0.03,
            investment_return_rate=0.07,
            social_security_return_rate=0.05,
            base_currency="CNY",
            display_currency="CNY"
        )

        # 计算各国养老金
        results = []
        for code in country_codes:
            if code in engine.calculators:
                calculator = engine.calculators[code]
                try:
                    result = calculator.calculate_pension(person, salary_profile, economic_factors)
                    retirement_age = calculator.get_retirement_age(person)
                    
                    results.append({
                        'country_code': code,
                        'country_name': calculator.country_name,
                        'retirement_age': retirement_age,
                        'monthly_pension': result.monthly_pension,
                        'total_contribution': result.total_contribution,
                        'total_benefit': result.total_benefit,
                        'roi': result.roi,
                        'break_even_age': result.break_even_age,
                        'original_currency': result.original_currency,
                        'details': result.details
                    })
                except Exception as e:
                    print(f"计算 {calculator.country_name} 时出错: {str(e)}")

        # 按月退休金排序
        results.sort(key=lambda x: x['monthly_pension'], reverse=True)

        # 显示对比结果
        print(f"\n📈 退休金对比结果:")
        print(f"{'排名':<4} {'国家/地区':<12} {'退休年龄':<8} {'月退休金(本币)':<18} {'总缴费(本币)':<15} {'投资回报率':<12}")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            local_currency = result['original_currency']
            print(f"{i:>2}.  {result['country_name']:<10} {result['retirement_age']:>6}岁  {converter.format_amount(result['monthly_pension'], local_currency):<18} {converter.format_amount(result['total_contribution'], local_currency):<15} {result['roi']:>8.1%}")

        # 显示详细信息
        print(f"\n🔍 详细对比:")
        print("-" * 80)
        for result in results:
            local_currency = result['original_currency']
            print(f"\n🏛️  {result['country_name']} ({result['country_code']})")
            print(f"   退休年龄: {result['retirement_age']}岁")
            print(f"   月退休金: {converter.format_amount(result['monthly_pension'], local_currency)} ({local_currency}) = {converter.format_amount(result['monthly_pension'], 'CNY')} (CNY)")
            print(f"   总缴费: {converter.format_amount(result['total_contribution'], local_currency)} ({local_currency})")
            print(f"   投资回报率: {result['roi']:.1%}")
            print(f"   回本年龄: {result['break_even_age']}岁" if result['break_even_age'] else "   回本年龄: 无法计算")
            
            # 显示特殊信息
            details = result['details']
            if result['country_code'] == 'US' and 'social_security_pension' in details:
                print(f"   Social Security: {converter.format_amount(details['social_security_pension'], 'USD')}/月")
                if 'k401_monthly_pension' in details:
                    print(f"   401K: {converter.format_amount(details['k401_monthly_pension'], 'USD')}/月")
            elif result['country_code'] == 'CN' and 'basic_pension' in details:
                print(f"   基础养老金: {converter.format_amount(details['basic_pension'], 'CNY')}/月")
                if 'account_pension' in details:
                    print(f"   个人账户养老金: {converter.format_amount(details['account_pension'], 'CNY')}/月")

        # 统计信息
        if results:
            avg_pension = sum(r['monthly_pension'] for r in results) / len(results)
            max_result = results[0]  # 已排序
            min_result = results[-1]
            
            print(f"\n📊 统计信息:")
            print(f"   平均月退休金: {converter.format_amount(avg_pension, 'CNY')}")
            print(f"   最高退休金: {max_result['country_name']} ({converter.format_amount(max_result['monthly_pension'], 'CNY')})")
            print(f"   最低退休金: {min_result['country_name']} ({converter.format_amount(min_result['monthly_pension'], 'CNY')})")

    print(f"\n🎯 {countries_str}对比分析完成！")

def parse_country_comparison():
    """解析多国对比参数"""
    # 国家代码映射
    country_map = {
        'cn': 'CN', 'china': 'CN',
        'us': 'US', 'usa': 'US',
 
        'tw': 'TW', 'taiwan': 'TW',
        'hk': 'HK', 'hongkong': 'HK',
        'sg': 'SG', 'singapore': 'SG',
        'jp': 'JP', 'japan': 'JP',
        'uk': 'UK', 'britain': 'UK',
        'au': 'AU', 'australia': 'AU',
        'ca': 'CA', 'canada': 'CA'
    }
    
    # 查找包含多个国家的参数
    for arg in sys.argv[1:]:
        if ',' in arg or arg.startswith('--'):
            # 处理逗号分隔的国家列表，如: cn,au,us 或 --cn,au
            countries_str = arg.replace('--', '').lower()
            if ',' in countries_str:
                country_codes = []
                for country in countries_str.split(','):
                    country = country.strip()
                    if country in country_map:
                        code = country_map[country]
                        if code not in country_codes:
                            country_codes.append(code)
                if len(country_codes) >= 2:
                    return country_codes
    
    return None

def main():
    """主函数"""
    # 检查多国对比参数
    comparison_countries = parse_country_comparison()
    
    if comparison_countries:
        # 创建计算引擎
        engine = create_pension_engine()
        
        # 执行多国对比
        analyze_countries_comparison(engine, comparison_countries)
        return
    
    # 检查单一国家参数
    usa_only = '--usa-only' in sys.argv or '--us' in sys.argv
    hk_only = '--hk-only' in sys.argv or '--hk' in sys.argv
    sg_only = '--singapore-only' in sys.argv or '--sg' in sys.argv
    cn_only = '--china-only' in sys.argv or '--cn' in sys.argv
    tw_only = '--taiwan-only' in sys.argv or '--tw' in sys.argv
    jp_only = '--japan-only' in sys.argv or '--jp' in sys.argv
    uk_only = '--uk-only' in sys.argv or '--uk' in sys.argv
    au_only = '--australia-only' in sys.argv or '--au' in sys.argv
    ca_only = '--canada-only' in sys.argv or '--ca' in sys.argv

    # 创建计算引擎
    engine = create_pension_engine()

    # 定义两个场景
    scenarios = [
        ("高收入场景", 50000),  # 月薪5万人民币
        ("低收入场景", 5000)    # 月薪5千人民币
    ]

    # 检查单一国家参数
    if usa_only:
        print("🇺🇸 === 美国养老金详细分析系统 ===")
        print("分析401K和Social Security的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_usa_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 美国养老金分析完成！")
        return

    elif hk_only:
        print("🇭🇰 === 香港MPF详细分析系统 ===")
        print("分析强积金计划的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_hk_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 香港MPF分析完成！")
        return

    elif sg_only:
        print("🇸🇬 === 新加坡CPF详细分析系统 ===")
        print("分析中央公积金计划的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_singapore_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 新加坡CPF分析完成！")
        return

    elif cn_only:
        print("🇨🇳 === 中国养老金详细分析系统 ===")
        print("分析基本养老保险的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_china_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 中国养老金分析完成！")
        return

    elif tw_only:
        print("🇹🇼 === 台湾养老金详细分析系统 ===")
        print("分析劳保年金的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_taiwan_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 台湾养老金分析完成！")
        return

    elif jp_only:
        print("🇯🇵 === 日本养老金详细分析系统 ===")
        print("分析国民年金(NPI) + 厚生年金(EPI) 的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_japan_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 日本养老金分析完成！")
        return

    elif uk_only:
        print("🇬🇧 === 英国养老金详细分析系统 ===")
        print("分析国家养老金的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_uk_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 英国养老金分析完成！")
        return

    elif au_only:
        print("🇦🇺 === 澳大利亚养老金详细分析系统 ===")
        print("分析超级年金的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_australia_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 澳大利亚养老金分析完成！")
        return

    elif ca_only:
        print("🇨🇦 === 加拿大养老金详细分析系统 ===")
        print("分析CPP和OAS的详细情况\n")

        for scenario_name, monthly_salary in scenarios:
            analyze_canada_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 加拿大养老金分析完成！")
        return

    # 原有的多国对比功能
    print("=== 退休金对比系统 ===")
    print("计算两个固定场景：")
    print("- 月薪5万人民币，工作30年，按各国实际退休年龄，领取20年")
    print("- 月薪5千人民币，工作30年，按各国实际退休年龄，领取20年")
    print("\n使用以下参数可以分析特定国家:")
    print("  单国分析:")
    print("    --us 或 --usa-only     分析美国养老金")
    print("    --hk 或 --hk-only     分析香港MPF")
    print("    --sg 或 --sg-only     分析新加坡CPF")
    print("    --cn 或 --china-only  分析中国养老金")
    print("    --tw 或 --tw-only     分析台湾养老金")
    print("    --jp 或 --jp-only     分析日本养老金")
    print("    --uk 或 --uk-only     分析英国养老金")
    print("    --au 或 --au-only     分析澳大利亚养老金")
    print("    --ca 或 --ca-only     分析加拿大养老金")
    print("  多国对比:")
    print("    cn,au              对比中国和澳大利亚")
    print("    us,cn,au           对比美国、中国和澳大利亚")
    print("    hk,sg,tw           对比香港、新加坡和台湾")
    print("    任意国家组合       支持2个或更多国家的任意组合")

    print(f"已注册 {len(engine.get_available_countries())} 个国家/地区的计算器")

    # 分析每个场景
    all_results = []
    for scenario_name, monthly_salary in scenarios:
        result_df = analyze_scenario(engine, scenario_name, monthly_salary)
        all_results.append({
            'name': scenario_name,
            'monthly_salary': monthly_salary,
            'results': result_df
        })

    # 生成总结报告
    print(f"\n{'='*80}")
    print(f"📋 总结报告")
    print(f"{'='*80}")

    for scenario in all_results:
        print(f"\n🎯 {scenario['name']}:")
        print(f"   月薪: {converter.format_amount(scenario['monthly_salary'], 'CNY')}")
        print(f"   工作年限: 30年")
        print(f"   退休年龄: 按各国实际年龄")
        print(f"   领取年限: 20年")

        results = scenario['results']
        if not results.empty:
            max_country = results.loc[results['monthly_pension'].idxmax()]
            min_country = results.loc[results['monthly_pension'].idxmin()]
            print(f"   退休金最高: {max_country['country_name']} ({converter.format_amount(max_country['monthly_pension'], 'CNY')}/月)")
            print(f"   退休金最低: {min_country['country_name']} ({converter.format_amount(min_country['monthly_pension'], 'CNY')}/月)")

    print(f"\n✅ 分析完成！")
    print(f"共分析了 {len(scenarios)} 个场景，{len(engine.get_available_countries())} 个国家/地区")

    # 默认显示所有国家的详细信息
    print(f"\n{'='*80}")
    print("🌍 开始按国家分别输出详细信息...")

    for scenario_name, monthly_salary in scenarios:
        analyze_by_country(engine, scenario_name, monthly_salary)

    print(f"\n{'='*80}")
    print("✅ 按国家分别输出完成！")
    print(f"如需单独分析，请使用参数：")
    print(f"  --us     分析美国养老金")
    print(f"  --hk     分析香港MPF")
    print(f"  --sg     分析新加坡CPF")
    print(f"  --cn     分析中国养老金")
    print(f"  --tw     分析台湾养老金")
    print(f"  --jp     分析日本养老金")
    print(f"  --uk     分析英国养老金")
    print(f"  --au     分析澳大利亚养老金")
    print(f"  --ca     分析加拿大养老金")

if __name__ == "__main__":
    main()
