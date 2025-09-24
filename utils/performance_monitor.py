#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控工具
用于监控和优化计算性能
"""

import time
import functools
import psutil
import os
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
import threading
import queue


@dataclass
class PerformanceMetrics:
    """性能指标"""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_percent: float
    timestamp: float
    args_hash: str


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.enabled = True
        self._lock = threading.Lock()
    
    def monitor(self, func: Callable) -> Callable:
        """装饰器：监控函数性能"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
            
            # 记录开始状态
            start_time = time.time()
            start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
            start_cpu = psutil.cpu_percent()
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录结束状态
                end_time = time.time()
                end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
                end_cpu = psutil.cpu_percent()
                
                # 计算指标
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                cpu_percent = (start_cpu + end_cpu) / 2
                
                # 记录指标
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    memory_usage=memory_usage,
                    cpu_percent=cpu_percent,
                    timestamp=end_time,
                    args_hash=str(hash(str(args) + str(kwargs)))
                )
                
                with self._lock:
                    self.metrics.append(metric)
                
                return result
                
            except Exception as e:
                # 即使出错也记录性能数据
                end_time = time.time()
                execution_time = end_time - start_time
                
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    memory_usage=0,
                    cpu_percent=0,
                    timestamp=end_time,
                    args_hash=str(hash(str(args) + str(kwargs)))
                )
                
                with self._lock:
                    self.metrics.append(metric)
                
                raise e
        
        return wrapper
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics:
            return {"message": "No performance data available"}
        
        with self._lock:
            metrics_copy = self.metrics.copy()
        
        # 按函数名分组
        function_stats = {}
        for metric in metrics_copy:
            if metric.function_name not in function_stats:
                function_stats[metric.function_name] = {
                    'call_count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                    'total_memory': 0,
                    'avg_memory': 0,
                    'avg_cpu': 0
                }
            
            stats = function_stats[metric.function_name]
            stats['call_count'] += 1
            stats['total_time'] += metric.execution_time
            stats['max_time'] = max(stats['max_time'], metric.execution_time)
            stats['min_time'] = min(stats['min_time'], metric.execution_time)
            stats['total_memory'] += metric.memory_usage
            stats['avg_cpu'] += metric.cpu_percent
        
        # 计算平均值
        for stats in function_stats.values():
            stats['avg_time'] = stats['total_time'] / stats['call_count']
            stats['avg_memory'] = stats['total_memory'] / stats['call_count']
            stats['avg_cpu'] = stats['avg_cpu'] / stats['call_count']
            if stats['min_time'] == float('inf'):
                stats['min_time'] = 0
        
        # 总体统计
        total_calls = len(metrics_copy)
        total_time = sum(m.execution_time for m in metrics_copy)
        total_memory = sum(m.memory_usage for m in metrics_copy)
        avg_cpu = sum(m.cpu_percent for m in metrics_copy) / total_calls
        
        return {
            'overall': {
                'total_calls': total_calls,
                'total_execution_time': total_time,
                'average_execution_time': total_time / total_calls,
                'total_memory_usage': total_memory,
                'average_memory_usage': total_memory / total_calls,
                'average_cpu_percent': avg_cpu
            },
            'by_function': function_stats,
            'slowest_functions': sorted(
                function_stats.items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:5]
        }
    
    def clear_metrics(self):
        """清空性能指标"""
        with self._lock:
            self.metrics.clear()
    
    def enable(self):
        """启用监控"""
        self.enabled = True
    
    def disable(self):
        """禁用监控"""
        self.enabled = False


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(func: Callable) -> Callable:
    """性能监控装饰器"""
    return performance_monitor.monitor(func)


class PerformanceProfiler:
    """性能分析器"""
    
    @staticmethod
    def compare_implementations(original_func: Callable, optimized_func: Callable, 
                             test_cases: List[tuple], iterations: int = 3) -> Dict[str, Any]:
        """比较两个实现的性能"""
        results = {
            'original': [],
            'optimized': [],
            'improvement': {}
        }
        
        for test_case in test_cases:
            # 测试原始实现
            original_times = []
            for _ in range(iterations):
                start_time = time.time()
                try:
                    original_func(*test_case)
                    original_times.append(time.time() - start_time)
                except Exception as e:
                    original_times.append(float('inf'))
            
            # 测试优化实现
            optimized_times = []
            for _ in range(iterations):
                start_time = time.time()
                try:
                    optimized_func(*test_case)
                    optimized_times.append(time.time() - start_time)
                except Exception as e:
                    optimized_times.append(float('inf'))
            
            # 计算平均时间
            avg_original = sum(t for t in original_times if t != float('inf')) / len([t for t in original_times if t != float('inf'))
            avg_optimized = sum(t for t in optimized_times if t != float('inf')) / len([t for t in optimized_times if t != float('inf'))
            
            results['original'].append({
                'test_case': test_case,
                'times': original_times,
                'avg_time': avg_original
            })
            
            results['optimized'].append({
                'test_case': test_case,
                'times': optimized_times,
                'avg_time': avg_optimized
            })
            
            # 计算改进比例
            if avg_original > 0:
                improvement = (avg_original - avg_optimized) / avg_original * 100
                results['improvement'][str(test_case)] = {
                    'time_saved': avg_original - avg_optimized,
                    'improvement_percent': improvement,
                    'speedup_factor': avg_original / avg_optimized if avg_optimized > 0 else float('inf')
                }
        
        return results


def benchmark_cpf_calculations():
    """CPF计算性能基准测试"""
    from plugins.singapore.cpf_calculator import SingaporeCPFCalculator
    from plugins.singapore.cpf_calculator_optimized import SingaporeCPFCalculatorOptimized
    
    # 测试用例
    test_cases = [
        (5000, 30, 65),   # 月薪5000，30-65岁
        (8000, 25, 60),   # 月薪8000，25-60岁
        (12000, 35, 70),  # 月薪12000，35-70岁
        (15000, 28, 62),  # 月薪15000，28-62岁
    ]
    
    # 创建计算器实例
    original_calculator = SingaporeCPFCalculator()
    optimized_calculator = SingaporeCPFCalculatorOptimized()
    
    # 比较性能
    profiler = PerformanceProfiler()
    results = profiler.compare_implementations(
        original_calculator.calculate_lifetime_cpf,
        optimized_calculator.calculate_lifetime_cpf,
        test_cases,
        iterations=5
    )
    
    return results


if __name__ == "__main__":
    # 运行基准测试
    benchmark_results = benchmark_cpf_calculations()
    print("CPF计算性能基准测试结果:")
    print(f"平均改进: {sum(r['improvement_percent'] for r in benchmark_results['improvement'].values()) / len(benchmark_results['improvement']):.2f}%")
    
    for test_case, improvement in benchmark_results['improvement'].items():
        print(f"测试用例 {test_case}:")
        print(f"  时间节省: {improvement['time_saved']:.4f}秒")
        print(f"  改进比例: {improvement['improvement_percent']:.2f}%")
        print(f"  加速倍数: {improvement['speedup_factor']:.2f}x")
        print()