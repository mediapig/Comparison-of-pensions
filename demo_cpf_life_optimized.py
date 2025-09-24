#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF LIFE优化计算器演示脚本
展示优化后的CPF LIFE计算功能和性能提升
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from plugins.singapore.cpf_life_optimized import (
    CPFLifeOptimizedCalculator, 
    quick_cpf_life_calculation, 
    compare_all_plans
)
from plugins.singapore.cpf_life_analyzer import (
    CPFLifeAnalyzer, 
    AnalysisConfig, 
    quick_analysis, 
    generate_report
)
from plugins.singapore.cpf_life_performance import (
    CPFLifePerformanceOptimizer, 
    quick_vectorized_analysis, 
    benchmark_cpf_life_performance
)
import time
import json


def demo_basic_calculations():
    """演示基础计算功能"""
    print("=" * 60)
    print("1. 基础CPF LIFE计算演示")
    print("=" * 60)
    
    # 示例RA65余额
    ra65_balance = 300000  # 30万新币
    
    print(f"RA65余额: ${ra65_balance:,.0f}")
    print()
    
    # 快速计算
    print("快速计算示例:")
    quick_result = quick_cpf_life_calculation(ra65_balance, "standard")
    print(f"标准计划 - 月收入: ${quick_result['monthly_income']:,.2f}")
    print(f"标准计划 - 总领取: ${quick_result['total_payout']:,.2f}")
    print(f"标准计划 - 最终余额: ${quick_result['final_balance']:,.2f}")
    print()
    
    # 详细计算器
    calculator = CPFLifeOptimizedCalculator()
    
    print("详细计算示例:")
    result = calculator.cpf_life_simulate(ra65_balance, "standard")
    print(f"月领取计划长度: {len(result.monthly_schedule)} 个月")
    print(f"首月领取: ${result.monthly_schedule[0]:,.2f}")
    print(f"总领取金额: ${result.total_payout:,.2f}")
    print(f"最终余额: ${result.final_balance:,.2f}")
    print(f"遗赠快照 - 70岁: ${result.snapshots['age_70']:,.2f}")
    print(f"遗赠快照 - 80岁: ${result.snapshots['age_80']:,.2f}")
    print(f"遗赠快照 - 90岁: ${result.snapshots['age_90']:,.2f}")
    print()


def demo_plan_comparison():
    """演示计划对比功能"""
    print("=" * 60)
    print("2. CPF LIFE计划对比演示")
    print("=" * 60)
    
    ra65_balance = 300000
    
    # 比较所有计划
    comparison = compare_all_plans(ra65_balance)
    
    print(f"RA65余额: ${ra65_balance:,.0f}")
    print()
    print("计划对比表:")
    print("-" * 80)
    print(f"{'计划':<12} {'初始月收入':<15} {'总领取':<15} {'最终余额':<15} {'80岁遗赠':<15}")
    print("-" * 80)
    
    for plan_data in comparison['comparison_table']:
        print(f"{plan_data['plan']:<12} "
              f"${plan_data['initial_monthly']:<14,.0f} "
              f"${plan_data['total_payout']:<14,.0f} "
              f"${plan_data['final_balance']:<14,.0f} "
              f"${plan_data['bequest_at_80']:<14,.0f}")
    
    print()
    print("汇总:")
    print(f"最高月收入: ${comparison['summary']['highest_monthly']:,.2f}")
    print(f"最高总领取: ${comparison['summary']['highest_total']:,.2f}")
    print(f"最高遗赠: ${comparison['summary']['highest_bequest']:,.2f}")
    print()


def demo_advanced_analysis():
    """演示高级分析功能"""
    print("=" * 60)
    print("3. 高级分析功能演示")
    print("=" * 60)
    
    ra65_balance = 300000
    
    # 创建分析器
    config = AnalysisConfig(
        start_age=65,
        horizon_age=100,
        death_ages=[70, 75, 80, 85, 90, 95, 100],
        risk_scenarios=[0.03, 0.04, 0.05],
        inflation_scenarios=[0.015, 0.02, 0.025]
    )
    
    analyzer = CPFLifeAnalyzer(config)
    
    print(f"RA65余额: ${ra65_balance:,.0f}")
    print()
    
    # 综合分析
    print("正在执行综合分析...")
    start_time = time.time()
    analysis = analyzer.comprehensive_analysis(ra65_balance)
    analysis_time = time.time() - start_time
    
    print(f"分析完成，耗时: {analysis_time:.2f}秒")
    print()
    
    # 显示基础分析结果
    basic_analysis = analysis['basic_analysis']
    optimal_plan = basic_analysis['optimal_plan']
    
    print("最优计划推荐:")
    print(f"推荐计划: {optimal_plan['optimal_plan']}")
    print(f"推荐理由: {optimal_plan['recommendation'].get('reason', '基于综合评分')}")
    print()
    
    # 显示敏感性分析
    if 'sensitivity_analysis' in analysis:
        sensitivity = analysis['sensitivity_analysis']
        print("敏感性分析摘要:")
        
        rate_sensitivity = sensitivity['sensitivity_summary']['rate_sensitivity']
        for plan, data in rate_sensitivity.items():
            print(f"{plan}计划 - 月收入范围: ${data['min_monthly']:,.0f} - ${data['max_monthly']:,.0f}")
            print(f"          波动性: {data['volatility']:.3f}")
        print()
    
    # 显示推荐
    recommendations = analysis['recommendations']
    print("推荐建议:")
    print(f"主要推荐: {recommendations['primary_recommendation']['plan']}计划")
    print("备选方案:")
    for alt in recommendations['alternative_options'][:2]:  # 只显示前2个
        print(f"  - {alt['plan']}计划")
    print()


def demo_bequest_analysis():
    """演示遗赠分析功能"""
    print("=" * 60)
    print("4. 遗赠分析演示")
    print("=" * 60)
    
    ra65_balance = 300000
    calculator = CPFLifeOptimizedCalculator()
    
    print(f"RA65余额: ${ra65_balance:,.0f}")
    print()
    
    # 分析不同计划的遗赠情况
    plans = ["standard", "escalating", "basic"]
    
    for plan in plans:
        print(f"{plan.upper()}计划遗赠分析:")
        bequest_analysis = calculator.analyze_bequest_scenarios(ra65_balance, plan)
        
        print("不同死亡年龄的遗赠情况:")
        for death_age, scenario in bequest_analysis['bequest_scenarios'].items():
            print(f"  {death_age}岁去世: 遗赠 ${scenario['bequest_amount']:,.0f}, "
                  f"已领取 ${scenario['total_received']:,.0f}")
        
        print(f"遗赠范围: ${bequest_analysis['summary']['min_bequest']:,.0f} - "
              f"${bequest_analysis['summary']['max_bequest']:,.0f}")
        print()


def demo_performance_optimization():
    """演示性能优化功能"""
    print("=" * 60)
    print("5. 性能优化演示")
    print("=" * 60)
    
    # 创建性能优化器
    optimizer = CPFLifePerformanceOptimizer()
    
    # 测试数据
    test_sizes = [10, 50, 100]
    ra65_values = [200000, 300000, 400000, 500000]
    
    print("向量化批量分析:")
    start_time = time.time()
    batch_results = optimizer.batch_analysis(ra65_values)
    batch_time = time.time() - start_time
    
    print(f"分析 {len(ra65_values)} 个RA65余额 × 3个计划 = {len(ra65_values) * 3} 个计算")
    print(f"批量分析耗时: {batch_time:.3f}秒")
    print(f"计算速度: {len(ra65_values) * 3 / batch_time:.1f} 计算/秒")
    print()
    
    # 性能基准测试
    print("性能基准测试:")
    benchmark_results = optimizer.benchmark_performance(test_sizes)
    
    print(f"{'规模':<8} {'向量化(秒)':<12} {'传统(秒)':<12} {'加速比':<10}")
    print("-" * 50)
    
    for size, metrics in benchmark_results.items():
        print(f"{size:<8} {metrics['vectorized_time']:<12.3f} "
              f"{metrics['traditional_time']:<12.3f} "
              f"{metrics['vectorized_speedup']:<10.1f}x")
    print()


def demo_report_generation():
    """演示报告生成功能"""
    print("=" * 60)
    print("6. 报告生成演示")
    print("=" * 60)
    
    ra65_balance = 300000
    
    # 生成文本报告
    print("生成文本报告:")
    text_report = generate_report(ra65_balance, 'text')
    
    # 显示报告的前几行
    report_lines = text_report.split('\n')
    for line in report_lines[:20]:  # 只显示前20行
        print(line)
    
    if len(report_lines) > 20:
        print("...")
        print(f"(报告共 {len(report_lines)} 行)")
    print()
    
    # 生成JSON报告
    print("生成JSON报告:")
    json_report = generate_report(ra65_balance, 'json')
    json_data = json.loads(json_report)
    
    print(f"JSON报告包含 {len(json_data)} 个主要部分:")
    for key in json_data.keys():
        print(f"  - {key}")
    print()


def demo_parameter_customization():
    """演示参数自定义功能"""
    print("=" * 60)
    print("7. 参数自定义演示")
    print("=" * 60)
    
    ra65_balance = 300000
    calculator = CPFLifeOptimizedCalculator()
    
    print(f"RA65余额: ${ra65_balance:,.0f}")
    print()
    
    # 测试不同参数设置
    parameter_sets = [
        {"r_prem": 0.03, "r_ra": 0.03, "g_esc": 0.015, "p_basic": 0.10},
        {"r_prem": 0.04, "r_ra": 0.04, "g_esc": 0.020, "p_basic": 0.15},
        {"r_prem": 0.05, "r_ra": 0.05, "g_esc": 0.025, "p_basic": 0.20},
    ]
    
    print("不同参数设置的影响:")
    print(f"{'参数组合':<30} {'标准计划月收入':<15} {'递增计划月收入':<15}")
    print("-" * 70)
    
    for params in parameter_sets:
        calculator.set_parameters(**params)
        
        standard_result = calculator.cpf_life_simulate(ra65_balance, "standard")
        escalating_result = calculator.cpf_life_simulate(ra65_balance, "escalating")
        
        param_str = f"r_prem={params['r_prem']:.1%}, g_esc={params['g_esc']:.1%}"
        print(f"{param_str:<30} "
              f"${standard_result.monthly_schedule[0]:<14,.0f} "
              f"${escalating_result.monthly_schedule[0]:<14,.0f}")
    
    # 重置参数
    calculator.set_parameters()
    print()


def main():
    """主函数"""
    print("新加坡CPF LIFE优化计算器演示")
    print("=" * 60)
    print("本演示展示了优化后的CPF LIFE计算功能，包括:")
    print("1. 基础计算功能")
    print("2. 计划对比分析")
    print("3. 高级分析功能")
    print("4. 遗赠分析")
    print("5. 性能优化")
    print("6. 报告生成")
    print("7. 参数自定义")
    print()
    
    try:
        demo_basic_calculations()
        demo_plan_comparison()
        demo_advanced_analysis()
        demo_bequest_analysis()
        demo_performance_optimization()
        demo_report_generation()
        demo_parameter_customization()
        
        print("=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("优化后的CPF LIFE计算器提供了以下改进:")
        print("✓ 更精确的年金计算")
        print("✓ 完整的遗赠分析")
        print("✓ 多计划对比功能")
        print("✓ 敏感性分析")
        print("✓ 性能优化")
        print("✓ 详细的报告生成")
        print("✓ 灵活的参数设置")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()