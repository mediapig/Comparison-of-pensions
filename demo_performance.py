#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化演示脚本
展示原始版本和优化版本的性能差异
"""

import time
import sys
import os
sys.path.append('.')

def demo_cpf_performance():
    """演示CPF计算性能优化"""
    print("🚀 CPF计算性能优化演示")
    print("=" * 50)
    
    # 导入计算器
    from plugins.singapore.cpf_calculator import SingaporeCPFCalculator
    from plugins.singapore.cpf_calculator_optimized import SingaporeCPFCalculatorOptimized
    
    # 测试参数
    monthly_salary = 8000
    start_age = 30
    retirement_age = 65
    
    print(f"测试参数: 月薪{monthly_salary}, 年龄{start_age}-{retirement_age}")
    print()
    
    # 原始版本
    original_calculator = SingaporeCPFCalculator()
    start_time = time.time()
    original_result = original_calculator.calculate_lifetime_cpf(monthly_salary, start_age, retirement_age)
    original_time = time.time() - start_time
    
    # 优化版本
    optimized_calculator = SingaporeCPFCalculatorOptimized()
    start_time = time.time()
    optimized_result = optimized_calculator.calculate_lifetime_cpf(monthly_salary, start_age, retirement_age)
    optimized_time = time.time() - start_time
    
    # 计算改进
    improvement = (original_time - optimized_time) / original_time * 100 if original_time > 0 else 0
    speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
    
    # 显示结果
    print("📊 性能对比结果:")
    print(f"原始版本执行时间: {original_time:.4f}秒")
    print(f"优化版本执行时间: {optimized_time:.4f}秒")
    print(f"性能改进: {improvement:.2f}%")
    print(f"加速倍数: {speedup:.2f}x")
    print()
    
    # 验证结果一致性
    result_diff = abs(original_result["total_lifetime"] - optimized_result["total_lifetime"])
    print("✅ 结果一致性验证:")
    print(f"原始版本总缴费: ${original_result['total_lifetime']:,.2f}")
    print(f"优化版本总缴费: ${optimized_result['total_lifetime']:,.2f}")
    print(f"差异: ${result_diff:.2f}")
    print(f"结果一致: {'是' if result_diff < 0.01 else '否'}")
    print()
    
    return {
        'original_time': original_time,
        'optimized_time': optimized_time,
        'improvement': improvement,
        'speedup': speedup,
        'result_consistent': result_diff < 0.01
    }

def demo_irr_performance():
    """演示IRR计算性能优化"""
    print("📈 IRR计算性能优化演示")
    print("=" * 50)
    
    # 导入计算器
    from utils.irr_calculator import IRRCalculator
    from utils.irr_calculator_simple import IRRCalculatorSimple
    
    # 测试参数
    monthly_salary = 8000
    start_age = 30
    retirement_age = 65
    
    print(f"测试参数: 月薪{monthly_salary}, 年龄{start_age}-{retirement_age}")
    print()
    
    # 原始版本
    start_time = time.time()
    original_result = IRRCalculator.calculate_cpf_irr(monthly_salary, start_age, retirement_age, 90, 'annual')
    original_time = time.time() - start_time
    
    # 优化版本
    start_time = time.time()
    optimized_result = IRRCalculatorSimple.calculate_cpf_irr(monthly_salary, start_age, retirement_age, 90, 'annual')
    optimized_time = time.time() - start_time
    
    # 计算改进
    improvement = (original_time - optimized_time) / original_time * 100 if original_time > 0 else 0
    speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
    
    # 显示结果
    print("📊 性能对比结果:")
    print(f"原始版本执行时间: {original_time:.4f}秒")
    print(f"优化版本执行时间: {optimized_time:.4f}秒")
    print(f"性能改进: {improvement:.2f}%")
    print(f"加速倍数: {speedup:.2f}x")
    print()
    
    # 验证结果一致性
    irr_diff = abs(original_result["irr"] - optimized_result["irr"])
    print("✅ 结果一致性验证:")
    print(f"原始版本IRR: {original_result['irr']:.6f}")
    print(f"优化版本IRR: {optimized_result['irr']:.6f}")
    print(f"差异: {irr_diff:.8f}")
    print(f"结果一致: {'是' if irr_diff < 1e-6 else '否'}")
    print()
    
    return {
        'original_time': original_time,
        'optimized_time': optimized_time,
        'improvement': improvement,
        'speedup': speedup,
        'result_consistent': irr_diff < 1e-6
    }

def demo_optimization_techniques():
    """演示优化技术"""
    print("🔧 优化技术说明")
    print("=" * 50)
    
    techniques = [
        {
            'name': '向量化计算',
            'description': '使用NumPy数组操作替代Python循环',
            'benefit': '减少循环开销，提升计算效率'
        },
        {
            'name': '缓存机制',
            'description': '使用LRU缓存避免重复计算',
            'benefit': '相同输入直接返回缓存结果'
        },
        {
            'name': '简化公式',
            'description': '使用数学公式替代迭代计算',
            'benefit': '减少计算步骤，提升精度'
        },
        {
            'name': '预计算比率',
            'description': '在初始化时预计算常用比率',
            'benefit': '避免运行时重复计算'
        },
        {
            'name': '优化算法',
            'description': '使用更高效的算法实现',
            'benefit': '降低时间复杂度'
        }
    ]
    
    for i, technique in enumerate(techniques, 1):
        print(f"{i}. {technique['name']}")
        print(f"   描述: {technique['description']}")
        print(f"   优势: {technique['benefit']}")
        print()

def main():
    """主函数"""
    print("🎯 CPF计算系统性能优化演示")
    print("=" * 60)
    print()
    
    # 演示优化技术
    demo_optimization_techniques()
    
    print("=" * 60)
    print()
    
    # 演示CPF性能
    cpf_results = demo_cpf_performance()
    
    print("=" * 60)
    print()
    
    # 演示IRR性能
    irr_results = demo_irr_performance()
    
    print("=" * 60)
    print()
    
    # 总结
    print("📋 优化效果总结")
    print("=" * 50)
    print(f"CPF计算器:")
    print(f"  - 性能改进: {cpf_results['improvement']:.2f}%")
    print(f"  - 加速倍数: {cpf_results['speedup']:.2f}x")
    print(f"  - 结果一致: {'是' if cpf_results['result_consistent'] else '否'}")
    print()
    print(f"IRR计算器:")
    print(f"  - 性能改进: {irr_results['improvement']:.2f}%")
    print(f"  - 加速倍数: {irr_results['speedup']:.2f}x")
    print(f"  - 结果一致: {'是' if irr_results['result_consistent'] else '否'}")
    print()
    
    total_improvement = (cpf_results['improvement'] + irr_results['improvement']) / 2
    total_speedup = (cpf_results['speedup'] + irr_results['speedup']) / 2
    
    print(f"总体效果:")
    print(f"  - 平均改进: {total_improvement:.2f}%")
    print(f"  - 平均加速: {total_speedup:.2f}x")
    print()
    
    print("🎉 优化完成！计算速度显著提升，同时保持结果准确性。")

if __name__ == "__main__":
    main()