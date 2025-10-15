#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休金对比系统 - 智能货币转换版
支持货币缩写输入和自动换算
"""

import sys
import argparse
import logging
from datetime import date
from typing import List, Optional

from core.plugin_manager import plugin_manager
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount
from utils.annual_analyzer import AnnualAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SmartPensionComparisonApp:
    """智能退休金对比应用主类"""

    def __init__(self):
        self.plugin_manager = plugin_manager
        self.smart_converter = SmartCurrencyConverter()
        self.annual_analyzer = AnnualAnalyzer()

    def show_help(self):
        """显示帮助信息"""
        available_countries = self.plugin_manager.get_available_countries()

        print("=== 退休金对比系统 ===")
        print("使用方法: python main.py [金额] --国家")
        print()
        print("💡 智能货币输入支持:")
        print("  • 货币代码+金额: cny10000, USD5000, sgd8000")
        print("  • 金额+货币代码: 10000CNY, 5000USD, 8000SGD")
        print("  • 货币符号+金额: ¥10000, $5000, €4000")
        print("  • 纯数字: 10000 (默认为人民币)")
        print()
        print(f"✅ 已加载 {len(available_countries)} 个国家插件:")

        for country_code in sorted(available_countries):
            plugin = self.plugin_manager.get_plugin(country_code)
            if plugin:
                flag = self.get_country_flag(country_code)
                print(f"   {flag} {plugin.COUNTRY_NAME} ({country_code}) - {plugin.CURRENCY}")

        print()
        print("📋 使用示例:")
        print("   python main.py cny30000 --CN        # 分析中国，3万人民币")
        print("   python main.py USD5000 --US         # 分析美国，5千美元")
        print("   python main.py sgd8000 --SG         # 分析新加坡，8千新币")
        print("   python main.py ¥25000 --CN,US,SG    # 对比多个国家")
        print()
        print("   python main.py --list-plugins       # 列出所有插件")
        print("   python main.py --test-plugins        # 测试插件功能")
        print("   python main.py --supported-currencies # 显示支持的货币")
        print()
        print("📊 年度详细分析:")
        print("   python main.py --annual cny30000 --CN    # 中国年度详细分析")
        print("   python main.py --annual USD5000 --US     # 美国年度详细分析")

        if self.plugin_manager.failed_plugins:
            print()
            print(f"⚠️  {len(self.plugin_manager.failed_plugins)} 个插件加载失败:")
            for country, error in self.plugin_manager.failed_plugins.items():
                print(f"   • {country}: {error}")

    def get_country_flag(self, country_code: str) -> str:
        """获取国家国旗emoji"""
        country_flags = {
            'CN': '🇨🇳', 'US': '🇺🇸', 'SG': '🇸🇬',
            'TW': '🇹🇼', 'JP': '🇯🇵', 'UK': '🇬🇧',
        }
        return country_flags.get(country_code.upper(), '🏳️')

    def show_supported_currencies(self):
        """显示支持的货币"""
        print("=== 支持的货币 ===")
        supported_currencies = self.smart_converter.get_supported_currencies()

        for currency_code, info in supported_currencies.items():
            print(f"{currency_code}: {info['name']} ({info['symbol']})")
            print(f"  别名: {info['aliases']}")
            print()

        # 显示实时汇率状态
        print("=== 实时汇率状态 ===")
        connection_status = self.smart_converter.test_realtime_connection()

        # 按优先级排序显示
        sorted_apis = sorted(connection_status.items(), key=lambda x: x[1].get('priority', 999))

        for api_name, api_info in sorted_apis:
            status = api_info['status']
            free = api_info.get('free', True)
            priority = api_info.get('priority', 999)
            response_time = api_info.get('response_time', 0)
            currencies_count = api_info.get('currencies_count', 0)
            error = api_info.get('error', '')

            # 状态图标
            if status == 'success':
                status_icon = "✅"
                status_text = f"可用 ({currencies_count}种货币, {response_time}ms)"
            elif status == 'skipped':
                status_icon = "⏭️"
                status_text = f"跳过 ({error})"
            elif status == 'timeout':
                status_icon = "⏰"
                status_text = f"超时 ({response_time}ms)"
            elif status == 'connection_error':
                status_icon = "🔌"
                status_text = f"连接失败"
            elif status == 'http_error':
                status_icon = "🌐"
                status_text = f"HTTP错误 ({error})"
            elif status == 'invalid_data':
                status_icon = "⚠️"
                status_text = f"数据无效"
            else:
                status_icon = "❌"
                status_text = f"失败 ({error})"

            free_text = "免费" if free else "付费"
            print(f"{status_icon} {api_name} ({free_text}, 优先级{priority}): {status_text}")

        # 显示主要货币的实时汇率
        print("\n=== 主要货币实时汇率 (相对于人民币) ===")
        main_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'SGD', 'HKD', 'NOK']

        for currency in main_currencies:
            try:
                rate_info = self.smart_converter.get_realtime_rate_info('CNY', currency)
                if 'error' not in rate_info:
                    print(f"1 CNY = {rate_info['exchange_rate']:.4f} {currency}")
                else:
                    print(f"{currency}: 汇率获取失败")
            except Exception as e:
                print(f"{currency}: 汇率获取失败 - {e}")

        print(f"\n汇率更新时间: {rate_info.get('last_update', 'N/A')}")

    def list_plugins(self):
        """列出所有插件详情"""
        print("=== 插件详细信息 ===")

        country_info = self.plugin_manager.get_country_info()
        for country_code, info in sorted(country_info.items()):
            flag = self.get_country_flag(country_code)
            print(f"\n{flag} {info['country_name']} ({country_code})")
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
            flag = self.get_country_flag(country_code)

            print(f"\n🧪 测试 {flag} {country_name} ({country_code}):")

            if 'error' in result:
                print(f"   ❌ 测试失败: {result['error']}")
                continue

            # 基础信息
            if 'plugin_info' in result:
                print(f"   ✅ 插件信息正常")

            # 配置验证
            if result.get('config_valid'):
                print(f"   ✅ 配置验证通过")

            # 基础计算测试
            calc_results = result.get('basic_calculations', {})
            if 'error' not in calc_results:
                print(f"   ✅ 基础计算功能正常")
                if 'retirement_age' in calc_results:
                    print(f"      退休年龄: {calc_results['retirement_age']}")
            else:
                print(f"   ❌ 计算测试失败: {calc_results['error']}")

    def analyze_single_country(self, country_code: str, currency_amount: CurrencyAmount):
        """分析单个国家"""
        plugin = self.plugin_manager.get_plugin(country_code)
        if not plugin:
            print(f"❌ 未找到国家 {country_code} 的插件")
            return

        # 转换为目标国家的本地货币
        local_amount = self.smart_converter.convert_to_local(currency_amount, plugin.CURRENCY)

        flag = self.get_country_flag(country_code)
        print(f"=== {flag} {plugin.COUNTRY_NAME} ({country_code}) 分析 ===")
        print(f"输入金额: {self.smart_converter.format_amount(currency_amount)}")
        print(f"本地货币: {self.smart_converter.format_amount(local_amount)}")

        # 让插件自己创建Person对象，因为每个国家的退休年龄不同
        person = plugin.create_person(start_age=30)

        salary_profile = SalaryProfile(
            monthly_salary=local_amount.amount / 12,  # 年薪转月薪
            annual_growth_rate=0.0,
            contribution_start_age=30  # 固定从30岁开始工作
        )

        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )

        try:
            # 计算退休金
            pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)

            # 使用插件的详细分析方法
            if hasattr(plugin, 'print_detailed_analysis'):
                plugin.print_detailed_analysis(person, salary_profile, economic_factors, pension_result, local_amount)
            else:
                # 如果没有详细分析方法，使用简单输出
                print(f"\n📊 退休金分析:")
                print(f"  月退休金: {plugin.format_currency(pension_result.monthly_pension)}")
                print(f"  总缴费: {plugin.format_currency(pension_result.total_contribution)}")
                print(f"  ROI: {pension_result.roi:.2f}%")
                if pension_result.break_even_age:
                    print(f"  回本年龄: {pension_result.break_even_age}岁")

        except Exception as e:
            print(f"❌ 计算失败: {e}")

    def compare_countries(self, countries: List[str], currency_amount: CurrencyAmount):
        """对比多个国家"""
        print(f"=== 多国对比分析 ({', '.join(countries)}) ===")
        print(f"输入金额: {self.smart_converter.format_amount(currency_amount)}")

        # 创建测试数据 - 使用第一个插件创建Person对象
        first_plugin = self.plugin_manager.get_plugin(countries[0])
        person = first_plugin.create_person(start_age=30)

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
                # 转换为本地货币
                local_amount = self.smart_converter.convert_to_local(currency_amount, plugin.CURRENCY)

                salary_profile = SalaryProfile(
                    monthly_salary=local_amount.amount / 12,  # 年薪转月薪
                    annual_growth_rate=0.0,
                    contribution_start_age=22
                )

                # 计算退休金
                pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)

                # 计算税收
                annual_income = local_amount.amount * 12
                tax_result = plugin.calculate_tax(annual_income)

                # 计算社保
                ss_result = plugin.calculate_social_security(local_amount.amount, person.work_years)

                results[country_code] = {
                    'plugin': plugin,
                    'pension': pension_result,
                    'tax': tax_result,
                    'social_security': ss_result,
                    'retirement_age': plugin.get_retirement_age(person),
                    'local_amount': local_amount
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
            flag = self.get_country_flag(country_code)

            # 转换为人民币显示
            monthly_pension_cny = self.smart_converter.convert_to_local(
                CurrencyAmount(pension_result.monthly_pension, plugin.CURRENCY, ""),
                'CNY'
            )
            total_contribution_cny = self.smart_converter.convert_to_local(
                CurrencyAmount(pension_result.total_contribution, plugin.CURRENCY, ""),
                'CNY'
            )

            print(f"{flag}{plugin.COUNTRY_NAME:<8} {self.smart_converter.format_amount(monthly_pension_cny):<15} {self.smart_converter.format_amount(total_contribution_cny):<15} {pension_result.roi:>6.1f}% {retirement_age:>6}岁")

        print("\n💰 税收对比 (人民币):")
        print(f"{'国家':<10} {'年个税':<15} {'有效税率':<10}")
        print("-" * 40)

        for country_code, data in results.items():
            plugin = data['plugin']
            tax_result = data['tax']
            flag = self.get_country_flag(country_code)

            # 转换为人民币显示
            total_tax_cny = self.smart_converter.convert_to_local(
                CurrencyAmount(tax_result.get('total_tax', 0), plugin.CURRENCY, ""),
                'CNY'
            )
            effective_rate = tax_result.get('effective_rate', 0)

            print(f"{flag}{plugin.COUNTRY_NAME:<8} {self.smart_converter.format_amount(total_tax_cny):<15} {effective_rate:>8.1f}%")

    def analyze_annual_detail(self, country_code: str, currency_amount: CurrencyAmount,
                             start_age: int = 30, retirement_age: Optional[int] = None):
        """年度详细分析"""
        try:
            result = self.annual_analyzer.analyze_country(
                country_code, currency_amount, start_age, retirement_age
            )
            self.annual_analyzer.print_annual_analysis(result, show_yearly_detail=True)
        except Exception as e:
            print(f"❌ 年度分析失败: {e}")

def main():
    """主函数"""
    app = SmartPensionComparisonApp()

    # 手动解析参数以支持智能货币输入
    if len(sys.argv) < 2:
        app.show_help()
        return

    # 检查特殊命令
    if '--list-plugins' in sys.argv:
        app.list_plugins()
        return

    if '--test-plugins' in sys.argv:
        app.test_plugins()
        return

    if '--supported-currencies' in sys.argv:
        app.show_supported_currencies()
        return

    if '--help' in sys.argv or '-h' in sys.argv:
        app.show_help()
        return

    # 检查年度分析模式
    is_annual_mode = '--annual' in sys.argv
    if is_annual_mode:
        sys.argv.remove('--annual')  # 移除--annual参数

    # 解析金额参数（支持智能货币输入）
    try:
        amount_input = sys.argv[1]
        # 检查是否是特殊命令
        if amount_input.startswith('--'):
            app.show_help()
            return
        currency_amount = app.smart_converter.parse_amount(amount_input)
    except (ValueError, IndexError) as e:
        print(f"❌ 金额解析失败: {e}")
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
        app.show_help()
        return

    try:
        if is_annual_mode:
            # 年度详细分析模式
            if len(countries) == 1:
                app.analyze_annual_detail(countries[0], currency_amount)
            else:
                print("❌ 年度详细分析模式只支持单个国家")
                app.show_help()
        else:
            # 普通分析模式
            if len(countries) == 1:
                app.analyze_single_country(countries[0], currency_amount)
            else:
                app.compare_countries(countries, currency_amount)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()