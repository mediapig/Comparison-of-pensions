#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本
测试原始版本和优化版本的性能差异
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from plugins.singapore.cpf_calculator import SingaporeCPFCalculator
from plugins.singapore.cpf_calculator_optimized import SingaporeCPFCalculatorOptimized
from utils.irr_calculator import IRRCalculator
from utils.irr_calculator_optimized import IRRCalculatorOptimized


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.test_cases = [
            (5000, 30, 65),   # 月薪5000，30-65岁
            (8000, 25, 60),   # 月薪8000，25-60岁
            (12000, 35, 70),  # 月薪12000，35-70岁
            (15000, 28, 62),  # 月薪15000，28-62岁
            (20000, 32, 67),  # 月薪20000，32-67岁
        ]
        
        self.iterations = 5  # 每个测试用例运行5次取平均值
    
    def test_cpf_calculator_performance(self):
        """测试CPF计算器性能"""
        print("CPF计算器性能对比测试")
        print("=" * 60)
        
        # 创建计算器实例
        original_calculator = SingaporeCPFCalculator()
        optimized_calculator = SingaporeCPFCalculatorOptimized()
        
        total_original_time = 0
        total_optimized_time = 0
        results = []
        
        for i, (monthly_salary, start_age, retirement_age) in enumerate(self.test_cases, 1):
            print(f"测试用例 {i}: 月薪{monthly_salary}, 年龄{start_age}-{retirement_age}")
            
            # 测试原始版本
            original_times = []
            for _ in range(self.iterations):
                start_time = time.time()
                original_result = original_calculator.calculate_lifetime_cpf(monthly_salary, start_age, retirement_age)
                original_times.append(time.time() - start_time)
            
            # 测试优化版本
            optimized_times = []
            for _ in range(self.iterations):
                start_time = time.time()
                optimized_result = optimized_calculator.calculate_lifetime_cpf(monthly_salary, start_age, retirement_age)
                optimized_times.append(time.time() - start_time)
            
            # 计算平均值
            avg_original_time = sum(original_times) / len(original_times)
            avg_optimized_time = sum(optimized_times) / len(optimized_times)
            
            total_original_time += avg_original_time
            total_optimized_time += avg_optimized_time
            
            # 计算改进
            improvement = (avg_original_time - avg_optimized_time) / avg_original_time * 100 if avg_original_time > 0 else 0
            speedup = avg_original_time / avg_optimized_time if avg_optimized_time > 0 else float('inf')
            
            # 验证结果一致性
            result_consistency = abs(original_result["total_lifetime"] - optimized_result["total_lifetime"]) < 0.01
            
            result = {
                'test_case': (monthly_salary, start_age, retirement_age),
                'original_time': avg_original_time,
                'optimized_time': avg_optimized_time,
                'improvement_percent': improvement,
                'speedup_factor': speedup,
                'result_consistency': result_consistency
            }
            results.append(result)
            
            print(f"  原始版本平均时间: {avg_original_time:.4f}秒")
            print(f"  优化版本平均时间: {avg_optimized_time:.4f}秒")
            print(f"  改进比例: {improvement:.2f}%")
            print(f"  加速倍数: {speedup:.2f}x")
            print(f"  结果一致性: {result_consistency}")
            print()
        
        # 总体统计
        overall_improvement = (total_original_time - total_optimized_time) / total_original_time * 100
        overall_speedup = total_original_time / total_optimized_time
        
        print("总体性能对比:")
        print(f"总原始时间: {total_original_time:.4f}秒")
        print(f"总优化时间: {total_optimized_time:.4f}秒")
        print(f"总体改进: {overall_improvement:.2f}%")
        print(f"总体加速: {overall_speedup:.2f}x")
        print()
        
        return {
            'individual_results': results,
            'overall_improvement': overall_improvement,
            'overall_speedup': overall_speedup,
            'total_original_time': total_original_time,
            'total_optimized_time': total_optimized_time
        }
    
    def test_irr_calculator_performance(self):
        """测试IRR计算器性能"""
        print("IRR计算器性能对比测试")
        print("=" * 60)
        
        total_original_time = 0
        total_optimized_time = 0
        results = []
        
        for i, (monthly_salary, start_age, retirement_age) in enumerate(self.test_cases, 1):
            print(f"测试用例 {i}: 月薪{monthly_salary}, 年龄{start_age}-{retirement_age}")
            
            # 测试原始版本
            original_times = []
            for _ in range(self.iterations):
                start_time = time.time()
                original_result = IRRCalculator.calculate_cpf_irr(monthly_salary, start_age, retirement_age, 90, 'annual')
                original_times.append(time.time() - start_time)
            
            # 测试优化版本
            optimized_times = []
            for _ in range(self.iterations):
                start_time = time.time()
                optimized_result = IRRCalculatorOptimized.calculate_cpf_irr(monthly_salary, start_age, retirement_age, 90, 'annual')
                optimized_times.append(time.time() - start_time)
            
            # 计算平均值
            avg_original_time = sum(original_times) / len(original_times)
            avg_optimized_time = sum(optimized_times) / len(optimized_times)
            
            total_original_time += avg_original_time
            total_optimized_time += avg_optimized_time
            
            # 计算改进
            improvement = (avg_original_time - avg_optimized_time) / avg_original_time * 100 if avg_original_time > 0 else 0
            speedup = avg_original_time / avg_optimized_time if avg_optimized_time > 0 else float('inf')
            
            # 验证结果一致性
            result_consistency = abs(original_result["irr"] - optimized_result["irr"]) < 1e-6
            
            result = {
                'test_case': (monthly_salary, start_age, retirement_age),
                'original_time': avg_original_time,
                'optimized_time': avg_optimized_time,
                'improvement_percent': improvement,
                'speedup_factor': speedup,
                'result_consistency': result_consistency
            }
            results.append(result)
            
            print(f"  原始版本平均时间: {avg_original_time:.4f}秒")
            print(f"  优化版本平均时间: {avg_optimized_time:.4f}秒")
            print(f"  改进比例: {improvement:.2f}%")
            print(f"  加速倍数: {speedup:.2f}x")
            print(f"  结果一致性: {result_consistency}")
            print()
        
        # 总体统计
        overall_improvement = (total_original_time - total_optimized_time) / total_original_time * 100
        overall_speedup = total_original_time / total_optimized_time
        
        print("总体性能对比:")
        print(f"总原始时间: {total_original_time:.4f}秒")
        print(f"总优化时间: {total_optimized_time:.4f}秒")
        print(f"总体改进: {overall_improvement:.2f}%")
        print(f"总体加速: {overall_speedup:.2f}x")
        print()
        
        return {
            'individual_results': results,
            'overall_improvement': overall_improvement,
            'overall_speedup': overall_speedup,
            'total_original_time': total_original_time,
            'total_optimized_time': total_optimized_time
        }
    
    def run_all_tests(self):
        """运行所有性能测试"""
        print("开始性能测试套件")
        print("=" * 80)
        print()
        
        # CPF计算器测试
        cpf_results = self.test_cpf_calculator_performance()
        
        print("\n" + "=" * 80 + "\n")
        
        # IRR计算器测试
        irr_results = self.test_irr_calculator_performance()
        
        # 生成测试报告
        self.generate_report(cpf_results, irr_results)
        
        return {
            'cpf_results': cpf_results,
            'irr_results': irr_results
        }
    
    def generate_report(self, cpf_results, irr_results):
        """生成性能测试报告"""
        print("\n" + "=" * 80)
        print("性能测试报告")
        print("=" * 80)
        
        print(f"CPF计算器优化效果:")
        print(f"  平均改进: {cpf_results['overall_improvement']:.2f}%")
        print(f"  平均加速: {cpf_results['overall_speedup']:.2f}x")
        print(f"  时间节省: {cpf_results['total_original_time'] - cpf_results['total_optimized_time']:.4f}秒")
        
        print(f"\nIRR计算器优化效果:")
        print(f"  平均改进: {irr_results['overall_improvement']:.2f}%")
        print(f"  平均加速: {irr_results['overall_speedup']:.2f}x")
        print(f"  时间节省: {irr_results['total_original_time'] - irr_results['total_optimized_time']:.4f}秒")
        
        # 计算总体改进
        total_original = cpf_results['total_original_time'] + irr_results['total_original_time']
        total_optimized = cpf_results['total_optimized_time'] + irr_results['total_optimized_time']
        total_improvement = (total_original - total_optimized) / total_original * 100
        total_speedup = total_original / total_optimized
        
        print(f"\n总体优化效果:")
        print(f"  总体改进: {total_improvement:.2f}%")
        print(f"  总体加速: {total_speedup:.2f}x")
        print(f"  总时间节省: {total_original - total_optimized:.4f}秒")
        
        print("\n优化技术总结:")
        print("1. 向量化计算替代for循环")
        print("2. LRU缓存机制避免重复计算")
        print("3. 简化的年金公式")
        print("4. 优化的IRR计算方法")
        print("5. 预计算常用比率")


def main():
    """主函数"""
    test_suite = PerformanceTestSuite()
    results = test_suite.run_all_tests()
    
    return results


if __name__ == "__main__":
    main()