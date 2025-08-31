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
from plugins.germany.germany_calculator import GermanyPensionCalculator
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

def get_country_currency(country_code: str) -> str:
    """获取各国货币代码"""
    currency_map = {
        'CN': 'CNY',  # 中国 - 人民币
        'US': 'USD',  # 美国 - 美元
        'DE': 'EUR',  # 德国 - 欧元
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

    age_limits = k401_analysis['age_limits']
    print(f"当前年龄: {age_limits['current_age']}岁")
    print(f"50岁+追加缴费上限: ${age_limits['age_50_limit']:,}")
    print(f"60-63岁额外追加上限: ${age_limits['age_60_limit']:,}")

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

    scenarios = usa_calculator.get_contribution_scenarios(
        monthly_salary * 12, 30, 0.07
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

            # 计算替代率 - 工资不增长，退休时工资就是初始工资
    annual_salary = monthly_salary * 12
    replacement_rate = (basic_result.monthly_pension * 12) / annual_salary * 100

    print(f"年工资: {converter.format_amount(annual_salary, 'USD')}")
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
    print(f"总收益: {converter.format_amount(result.total_benefit, 'HKD')}")
    print(f"投资回报率: {result.roi:.1%}")
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
    print(f"\n{'='*80}")
    print(f"🇸🇬 新加坡CPF分析 - {scenario_name}")
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
    print(f"月退休金: {converter.format_amount(result.monthly_pension, 'SGD')}")
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

def main():
    """主函数"""
    # 检查命令行参数
    usa_only = '--usa-only' in sys.argv

    if usa_only:
        print("🇺🇸 === 美国养老金详细分析系统 ===")
        print("分析401K和Social Security的详细情况\n")

        # 创建计算引擎
        engine = create_pension_engine()

        # 定义两个场景
        scenarios = [
            ("高收入场景", 50000),  # 月薪5万人民币
            ("低收入场景", 5000)    # 月薪5千人民币
        ]

        # 分析每个场景
        for scenario_name, monthly_salary in scenarios:
            analyze_usa_only(engine, scenario_name, monthly_salary)

            print(f"\n{'='*80}")
            print(f"✅ {scenario_name}分析完成")
            print(f"{'='*80}")

        print(f"\n🎯 美国养老金分析完成！")
        return

    # 原有的多国对比功能
    print("=== 退休金对比系统 ===")
    print("计算两个固定场景：")
    print("- 月薪5万人民币，工作30年，按各国实际退休年龄，领取20年")
    print("- 月薪5千人民币，工作30年，按各国实际退休年龄，领取20年")
    print("\n使用以下参数可以只分析特定国家:")
    print("  --usa-only 或 --us-only     分析美国养老金")
    print("  --singapore-only 或 --sg-only 分析新加坡CPF")
    print("  --hk-only 或 --hk-only     分析香港MPF")

    # 创建计算引擎
    engine = create_pension_engine()
    print(f"已注册 {len(engine.get_available_countries())} 个国家/地区的计算器")

    # 定义两个场景
    scenarios = [
        ("高收入场景", 50000),  # 月薪5万人民币
        ("低收入场景", 5000)    # 月薪5千人民币
    ]

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

    # 检查是否有特殊参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--usa-only', '--us-only']:
            print(f"\n{'='*80}")
            print("🇺🇸 美国养老金详细分析...")
            for scenario_name, monthly_salary in scenarios:
                analyze_usa_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print("✅ 美国养老金分析完成！")
            return
        elif sys.argv[1] in ['--singapore-only', '--sg-only']:
            print(f"\n{'='*80}")
            print("🇸🇬 新加坡CPF详细分析...")
            for scenario_name, monthly_salary in scenarios:
                analyze_singapore_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print("✅ 新加坡CPF分析完成！")
            return
        elif sys.argv[1] in ['--hk-only', '--hk-only']:
            print(f"\n{'='*80}")
            print("🇭🇰 香港MPF详细分析...")
            for scenario_name, monthly_salary in scenarios:
                analyze_hk_only(engine, scenario_name, monthly_salary)
            print(f"\n{'='*80}")
            print("✅ 香港MPF分析完成！")
            return
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("可用参数:")
            print("  --usa-only 或 --us-only     分析美国养老金")
            print("  --singapore-only 或 --sg-only 分析新加坡CPF")
            print("  --hk-only 或 --hk-only     分析香港MPF")
            return
    else:
        # 默认显示所有国家的详细信息
        print(f"\n{'='*80}")
        print("🌍 开始按国家分别输出详细信息...")

        for scenario_name, monthly_salary in scenarios:
            analyze_by_country(engine, scenario_name, monthly_salary)

        print(f"\n{'='*80}")
        print("✅ 按国家分别输出完成！")
        print(f"如需单独分析，请使用参数：")
        print(f"  --usa-only     分析美国养老金")
        print(f"  --singapore-only 分析新加坡CPF")

if __name__ == "__main__":
    main()
