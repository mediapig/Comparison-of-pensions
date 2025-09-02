#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
退休金对比系统 - 主程序
重构后的轻量化版本，使用分析器管理器和税收计算器
"""

import sys
from core.pension_engine import PensionEngine
from analyzers.analyzer_manager import AnalyzerManager


def create_pension_engine():
    """创建并注册所有国家计算器"""
    engine = PensionEngine()

    # 导入所有计算器
    from plugins.china.china_calculator import ChinaPensionCalculator
    from plugins.usa.usa_calculator import USAPensionCalculator
    from plugins.taiwan.taiwan_calculator import TaiwanPensionCalculator
    from plugins.hongkong.hongkong_calculator import HongKongPensionCalculator
    from plugins.singapore.singapore_calculator import SingaporePensionCalculator
    from plugins.japan.japan_calculator import JapanPensionCalculator
    from plugins.uk.uk_calculator import UKPensionCalculator
    from plugins.australia.australia_calculator import AustraliaPensionCalculator
    from plugins.canada.canada_calculator import CanadaPensionCalculator

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

def show_help():
    """显示帮助信息"""
    print("=== 退休金对比系统 ===")
    print("计算两个固定场景：")
    print("- 月薪5万人民币，工作35年，按各国实际退休年龄，领取20年")
    print("- 月薪5千人民币，工作35年，按各国实际退休年龄，领取20年")
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

def main():
    """主函数"""
    # 检查多国对比参数
    comparison_countries = parse_country_comparison()

    if comparison_countries:
        # 创建计算引擎和分析器管理器
        engine = create_pension_engine()
        analyzer_manager = AnalyzerManager(engine)

        # 执行多国对比
        analyzer_manager.analyze_countries_comparison(comparison_countries)
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

    # 创建计算引擎和分析器管理器
    engine = create_pension_engine()
    analyzer_manager = AnalyzerManager(engine)

    # 检查单一国家参数
    if ca_only:
        # 使用加拿大综合分析器
        from plugins.canada.canada_comprehensive_analyzer import CanadaComprehensiveAnalyzer

        # 分析两个场景
        print("=== 加拿大高收入场景分析 ===")
        ca_analyzer = CanadaComprehensiveAnalyzer(engine)
        ca_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 加拿大低收入场景分析 ===")
        ca_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif au_only:
        # 使用澳大利亚综合分析器
        from plugins.australia.australia_comprehensive_analyzer import AustraliaComprehensiveAnalyzer

        # 分析两个场景
        print("=== 澳大利亚高收入场景分析 ===")
        au_analyzer = AustraliaComprehensiveAnalyzer(engine)
        au_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 澳大利亚低收入场景分析 ===")
        au_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif usa_only:
        # 使用美国综合分析器
        from plugins.usa.usa_comprehensive_analyzer import USAComprehensiveAnalyzer

        # 分析两个场景
        print("=== 美国高收入场景分析 ===")
        usa_analyzer = USAComprehensiveAnalyzer(engine)
        usa_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 美国低收入场景分析 ===")
        usa_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif cn_only:
        # 使用中国综合分析器
        from plugins.china.china_comprehensive_analyzer import ChinaComprehensiveAnalyzer

        # 分析两个场景
        print("=== 中国高收入场景分析 ===")
        cn_analyzer = ChinaComprehensiveAnalyzer(engine)
        cn_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 中国低收入场景分析 ===")
        cn_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif hk_only:
        # 使用香港综合分析器
        from plugins.hongkong.hongkong_comprehensive_analyzer import HongKongComprehensiveAnalyzer

        # 分析两个场景
        print("=== 香港高收入场景分析 ===")
        hk_analyzer = HongKongComprehensiveAnalyzer(engine)
        hk_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 香港低收入场景分析 ===")
        hk_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif tw_only:
        # 使用台湾综合分析器
        from plugins.taiwan.taiwan_comprehensive_analyzer import TaiwanComprehensiveAnalyzer

        # 分析两个场景
        print("=== 台湾高收入场景分析 ===")
        tw_analyzer = TaiwanComprehensiveAnalyzer(engine)
        tw_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 台湾低收入场景分析 ===")
        tw_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif jp_only:
        # 使用日本综合分析器
        from plugins.japan.japan_comprehensive_analyzer import JapanComprehensiveAnalyzer

        # 分析两个场景
        print("=== 日本高收入场景分析 ===")
        jp_analyzer = JapanComprehensiveAnalyzer(engine)
        jp_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 日本低收入场景分析 ===")
        jp_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return
    elif uk_only:
        # 使用英国综合分析器
        from plugins.uk.uk_comprehensive_analyzer import UKComprehensiveAnalyzer

        # 分析两个场景
        print("=== 英国高收入场景分析 ===")
        uk_analyzer = UKComprehensiveAnalyzer(engine)
        uk_analyzer.analyze_comprehensive(50000)  # 月薪5万人民币

        print("\n" + "="*80)
        print("=== 英国低收入场景分析 ===")
        uk_analyzer.analyze_comprehensive(5000)   # 月薪5千人民币
        return

    # 如果没有指定参数，显示帮助信息
    show_help()
    print(f"\n已注册 {len(analyzer_manager.get_available_countries())} 个国家/地区的计算器")
    print(f"支持的国家: {', '.join(analyzer_manager.get_available_countries())}")



if __name__ == "__main__":
    main()
