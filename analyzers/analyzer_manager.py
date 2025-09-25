#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析器管理器
统一管理所有国家的养老金分析器
"""

from core.pension_engine import PensionEngine
from plugins.usa.usa_analyzer import USAPensionAnalyzer
from plugins.hongkong.hongkong_analyzer import HongKongMPFAnalyzer
from plugins.singapore.singapore_analyzer import SingaporeCPFAnalyzer
# from plugins.china.china_analyzer import ChinaPensionAnalyzer  # 已删除
from plugins.taiwan.taiwan_analyzer import TaiwanPensionAnalyzer
from plugins.japan.japan_analyzer import JapanPensionAnalyzer
from plugins.uk.uk_analyzer import UKPensionAnalyzer
from plugins.australia.australia_analyzer import AustraliaPensionAnalyzer
from plugins.canada.canada_analyzer import CanadaPensionAnalyzer

class AnalyzerManager:
    """分析器管理器"""

    def __init__(self, engine: PensionEngine):
        self.engine = engine
        self.analyzers = {}
        self._init_analyzers()

    def _init_analyzers(self):
        """初始化所有分析器"""
        self.analyzers = {
            'US': USAPensionAnalyzer(self.engine),
            'HK': HongKongMPFAnalyzer(self.engine),
            'SG': SingaporeCPFAnalyzer(self.engine),
            # 'CN': ChinaPensionAnalyzer(self.engine),  # 已删除
            'TW': TaiwanPensionAnalyzer(self.engine),
            'JP': JapanPensionAnalyzer(self.engine),
            'UK': UKPensionAnalyzer(self.engine),
            'AU': AustraliaPensionAnalyzer(self.engine),
            'CA': CanadaPensionAnalyzer(self.engine)
        }

    def get_analyzer(self, country_code: str):
        """获取指定国家的分析器"""
        return self.analyzers.get(country_code.upper())

    def get_available_countries(self):
        """获取可用的国家列表"""
        return list(self.analyzers.keys())

    def analyze_country(self, country_code: str, monthly_salary: float = 10000):
        """分析指定国家的养老金"""
        analyzer = self.get_analyzer(country_code)
        if analyzer:
            analyzer.analyze_all_scenarios(monthly_salary)
        else:
            print(f"❌ 不支持的国家代码: {country_code}")

    def analyze_countries_comparison(self, country_codes: list, monthly_salary: float = 10000):
        """分析指定国家的养老金对比"""
        from datetime import date
        from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
        from utils.currency_converter import converter

        # 过滤有效的国家代码
        valid_countries = [code.upper() for code in country_codes if code.upper() in self.analyzers]

        if len(valid_countries) < 2:
            print("❌ 至少需要2个有效的国家代码进行对比")
            return

        country_names = []
        for code in valid_countries:
            if code in self.analyzers:
                country_names.append(self.engine.calculators[code].country_name)

        countries_str = "、".join(country_names)
        print(f"🌍 === {countries_str}养老金对比分析系统 ===")
        print(f"对比国家: {', '.join(valid_countries)}")
        print(f"分析退休金情况\n")

        print(f"\n{'='*80}")
        print(f"📊 月薪: {converter.format_amount(monthly_salary, 'CNY')}")
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
            annual_growth_rate=0.0
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
        for code in valid_countries:
            if code in self.engine.calculators:
                calculator = self.engine.calculators[code]
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
