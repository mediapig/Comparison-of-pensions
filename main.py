#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休金对比系统 - 简化版主程序
使用方法: python main.py 金额(人民币) --国家
"""

import sys
import argparse
import logging
from datetime import date
from typing import List

from core.plugin_manager import plugin_manager
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PensionComparisonApp:
    """退休金对比应用主类"""

    def __init__(self):
        self.plugin_manager = plugin_manager

        # 汇率表 (2024年汇率，人民币为基准)
        self.exchange_rates = {
            'CNY': 1.0,      # 人民币
            'USD': 0.14,     # 美元
            'SGD': 0.19,     # 新加坡元
            'CAD': 0.19,     # 加拿大元
            'AUD': 0.21,     # 澳大利亚元
            'HKD': 1.08,     # 港币
            'TWD': 4.4,      # 台币
            'JPY': 20.5,     # 日元
            'GBP': 0.11,     # 英镑
        }

    def convert_cny_to_local(self, cny_amount: float, target_currency: str) -> float:
        """将人民币转换为目标货币"""
        if target_currency not in self.exchange_rates:
            return cny_amount

        rate = self.exchange_rates[target_currency]
        return cny_amount * rate

    def show_help(self):
        """显示帮助信息"""
        available_countries = self.plugin_manager.get_available_countries()

        print("=== 退休金对比系统 (简化版) ===")
        print("使用方法: python main.py 金额(人民币) --国家")
        print()
        print(f"✅ 已加载 {len(available_countries)} 个国家插件:")

        for country_code in sorted(available_countries):
            plugin = self.plugin_manager.get_plugin(country_code)
            if plugin:
                print(f"   • {plugin.COUNTRY_NAME} ({country_code}) - {plugin.CURRENCY}")

        print()
        print("📋 使用示例:")
        print("   python main.py 50000 --CN        # 分析中国，月薪5万人民币")
        print("   python main.py 30000 --US        # 分析美国，月薪3万人民币")
        print("   python main.py 25000 --SG        # 分析新加坡，月薪2.5万人民币")
        print()
        print("   python main.py 20000 --cn,us,sg         # 对比多个国家")
        print()
        print("   python main.py --list-plugins    # 列出所有插件")
        print("   python main.py --test-plugins    # 测试插件功能")

        if self.plugin_manager.failed_plugins:
            print()
            print(f"⚠️  {len(self.plugin_manager.failed_plugins)} 个插件加载失败:")
            for country, error in self.plugin_manager.failed_plugins.items():
                print(f"   • {country}: {error}")

    def list_plugins(self):
        """列出所有插件详情"""
        print("=== 插件详细信息 ===")

        country_info = self.plugin_manager.get_country_info()
        for country_code, info in sorted(country_info.items()):
            print(f"\n🇨🇳 {info['country_name']} ({country_code})")
            print(f"   货币: {info['currency']}")
            print(f"   税年: {info['tax_year']}")
            print(f"   外部库: {info['external_adapters']} 个")
            print(f"   支持功能: {', '.join(info['supported_features'])}")

    def test_plugins(self):
        """测试所有插件"""
        print("=== 插件功能测试 ===")

        validation_results = self.plugin_manager.validate_all_plugins()

        for country_code, result in validation_results.items():
            plugin = self.plugin_manager.get_plugin(country_code)
            country_name = plugin.COUNTRY_NAME if plugin else country_code

            print(f"\n🧪 测试 {country_name} ({country_code}):")

            if 'error' in result:
                print(f"   ❌ 测试失败: {result['error']}")
                continue

            # 基础信息
            if 'plugin_info' in result:
                print(f"   ✅ 插件信息正常")

            # 配置验证
            if result.get('config_valid'):
                print(f"   ✅ 配置验证通过")

            # 外部适配器状态
            adapters = result.get('external_adapters_status', [])
            if adapters:
                available_count = sum(1 for adapter in adapters if adapter['available'])
                print(f"   📦 外部库: {available_count}/{len(adapters)} 可用")

            # 基础计算测试
            calc_results = result.get('basic_calculations', {})
            if 'error' not in calc_results:
                print(f"   ✅ 基础计算功能正常")
                if 'retirement_age' in calc_results:
                    print(f"      退休年龄: {calc_results['retirement_age']}")
            else:
                print(f"   ❌ 计算测试失败: {calc_results['error']}")

    def analyze_single_country(self, country_code: str, monthly_salary_cny: float):
        """分析单个国家"""
        plugin = self.plugin_manager.get_plugin(country_code)
        if not plugin:
            print(f"❌ 未找到国家 {country_code} 的插件")
            return

        # 转换货币
        monthly_salary_local = self.convert_cny_to_local(monthly_salary_cny, plugin.CURRENCY)

        print(f"=== {plugin.COUNTRY_NAME} ({country_code}) 分析 ===")
        print(f"月薪: ¥{monthly_salary_cny:,.0f} (人民币) = {plugin.format_currency(monthly_salary_local)}")

        # 创建测试数据
        person = Person(
            name="用户",
            birth_date=date(1985, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2010, 1, 1)
        )

        salary_profile = SalaryProfile(
            monthly_salary=monthly_salary_local,  # 使用本地货币
            annual_growth_rate=0.03,
            contribution_start_age=22
        )

        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )

        try:
            # 计算退休金
            pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)
            print(f"\n📊 退休金分析:")
            print(f"  月退休金: {plugin.format_currency(pension_result.monthly_pension)}")
            print(f"  总缴费: {plugin.format_currency(pension_result.total_contribution)}")
            print(f"  ROI: {pension_result.roi:.2f}%")
            if pension_result.break_even_age:
                print(f"  回本年龄: {pension_result.break_even_age}岁")

            # 计算税收
            annual_income = monthly_salary_local * 12
            tax_result = plugin.calculate_tax(annual_income)
            print(f"\n💰 税务分析:")
            print(f"  年个税: {plugin.format_currency(tax_result.get('total_tax', 0))}")
            print(f"  税后年收入: {plugin.format_currency(tax_result.get('net_income', annual_income))}")
            print(f"  有效税率: {tax_result.get('effective_rate', 0):.1f}%")

            # 计算社保
            ss_result = plugin.calculate_social_security(monthly_salary_local, person.work_years)
            print(f"\n🏦 社保分析:")
            if 'monthly_employee' in ss_result:
                print(f"  员工月缴费: {plugin.format_currency(ss_result['monthly_employee'])}")
            if 'monthly_employer' in ss_result:
                print(f"  雇主月缴费: {plugin.format_currency(ss_result['monthly_employer'])}")
            if 'total_lifetime' in ss_result:
                print(f"  终身总缴费: {plugin.format_currency(ss_result['total_lifetime'])}")

            # 显示人民币对比
            print(f"\n💱 人民币对比:")
            monthly_pension_cny = self.convert_cny_to_local(pension_result.monthly_pension, 'CNY') / self.exchange_rates[plugin.CURRENCY]
            total_contribution_cny = self.convert_cny_to_local(pension_result.total_contribution, 'CNY') / self.exchange_rates[plugin.CURRENCY]
            print(f"  月退休金: ¥{monthly_pension_cny:,.0f}")
            print(f"  总缴费: ¥{total_contribution_cny:,.0f}")

        except Exception as e:
            print(f"❌ 计算失败: {e}")

    def compare_countries(self, countries: List[str], monthly_salary_cny: float):
        """对比多个国家"""
        print(f"=== 多国对比分析 ({', '.join(countries)}) ===")
        print(f"月薪: ¥{monthly_salary_cny:,.0f} (人民币)")

        # 创建测试数据
        person = Person(
            name="对比用户",
            birth_date=date(1985, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2010, 1, 1)
        )

        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )

        results = {}
        errors = {}

        # 计算每个国家
        for country_code in countries:
            plugin = self.plugin_manager.get_plugin(country_code)
            if not plugin:
                errors[country_code] = f"Plugin not found"
                continue

            try:
                # 转换货币
                monthly_salary_local = self.convert_cny_to_local(monthly_salary_cny, plugin.CURRENCY)

                salary_profile = SalaryProfile(
                    monthly_salary=monthly_salary_local,
                    annual_growth_rate=0.03,
                    contribution_start_age=22
                )

                # 计算退休金
                pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)

                # 计算税收
                annual_income = monthly_salary_local * 12
                tax_result = plugin.calculate_tax(annual_income)

                # 计算社保
                ss_result = plugin.calculate_social_security(monthly_salary_local, person.work_years)

                results[country_code] = {
                    'plugin': plugin,
                    'pension': pension_result,
                    'tax': tax_result,
                    'social_security': ss_result,
                    'retirement_age': plugin.get_retirement_age(person)
                }

            except Exception as e:
                errors[country_code] = str(e)

        if errors:
            print(f"\n⚠️  部分国家计算失败:")
            for country, error in errors.items():
                print(f"   {country}: {error}")
            print()

        if not results:
            print("❌ 没有成功计算的国家数据")
            return

        # 显示对比结果
        print("\n📊 退休金对比 (人民币):")
        print(f"{'国家':<10} {'月退休金':<15} {'总缴费':<15} {'ROI':<8} {'退休年龄':<8}")
        print("-" * 60)

        for country_code, data in results.items():
            plugin = data['plugin']
            pension_result = data['pension']
            retirement_age = data['retirement_age']

            # 转换为人民币显示
            monthly_pension_cny = pension_result.monthly_pension / self.exchange_rates[plugin.CURRENCY]
            total_contribution_cny = pension_result.total_contribution / self.exchange_rates[plugin.CURRENCY]

            print(f"{plugin.COUNTRY_NAME:<10} ¥{monthly_pension_cny:>12,.0f} ¥{total_contribution_cny:>12,.0f} {pension_result.roi:>6.1f}% {retirement_age:>6}岁")

        print("\n💰 税收对比 (人民币):")
        print(f"{'国家':<10} {'年个税':<15} {'有效税率':<10}")
        print("-" * 40)

        for country_code, data in results.items():
            plugin = data['plugin']
            tax_result = data['tax']

            # 转换为人民币显示
            total_tax_cny = tax_result.get('total_tax', 0) / self.exchange_rates[plugin.CURRENCY]
            effective_rate = tax_result.get('effective_rate', 0)

            print(f"{plugin.COUNTRY_NAME:<10} ¥{total_tax_cny:>12,.0f} {effective_rate:>8.1f}%")

def main():
    """主函数"""
    # 手动解析参数以支持 --cn,us,sg 格式
    if len(sys.argv) < 2:
        app = PensionComparisonApp()
        app.show_help()
        return

    # 检查特殊命令
    if '--list-plugins' in sys.argv:
        app = PensionComparisonApp()
        app.list_plugins()
        return

    if '--test-plugins' in sys.argv:
        app = PensionComparisonApp()
        app.test_plugins()
        return

    # 解析薪资参数
    try:
        salary = float(sys.argv[1])
    except (ValueError, IndexError):
        app = PensionComparisonApp()
        app.show_help()
        return

    # 查找包含逗号的国家参数
    countries = []
    for arg in sys.argv[2:]:
        if arg.startswith('--') and ',' in arg:
            # 处理 --cn,us,sg 格式
            country_list = arg[2:].split(',')  # 去掉 -- 前缀
            countries = [c.strip().upper() for c in country_list]
            break
        elif arg.startswith('--'):
            # 处理单个国家 --CN 格式
            country = arg[2:].upper()
            countries.append(country)

    if not countries:
        app = PensionComparisonApp()
        app.show_help()
        return

    app = PensionComparisonApp()

    try:
        if len(countries) == 1:
            app.analyze_single_country(countries[0], salary)
        else:
            app.compare_countries(countries, salary)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()