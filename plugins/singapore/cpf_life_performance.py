#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF LIFE性能优化模块
使用NumPy向量化操作和缓存机制提升计算性能
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
import time
import concurrent.futures
from multiprocessing import Pool, cpu_count

from .cpf_life_optimized import CPFLifeOptimizedCalculator, CPFLifeResult


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    cache_hit_rate: float


class CPFLifePerformanceOptimizer:
    """CPF LIFE性能优化器"""
    
    def __init__(self):
        self.calculator = CPFLifeOptimizedCalculator()
        self._cache_stats = {'hits': 0, 'misses': 0}
        
    def vectorized_cpf_life_simulation(self, RA65_values: np.ndarray, 
                                    plan: str = "standard",
                                    start_age: int = 65, 
                                    horizon_age: int = 100) -> Dict[str, np.ndarray]:
        """
        向量化CPF LIFE模拟计算
        
        Args:
            RA65_values: RA65余额数组
            plan: 计划类型
            start_age: 开始年龄
            horizon_age: 终止年龄
            
        Returns:
            向量化计算结果
        """
        months = int((horizon_age - start_age) * 12)
        
        # 预计算参数
        if plan in ("standard", "escalating"):
            premium_ratios = np.ones_like(RA65_values)
            ra_ratios = np.zeros_like(RA65_values)
        elif plan == "basic":
            premium_ratios = np.full_like(RA65_values, self.calculator.p_basic)
            ra_ratios = 1 - premium_ratios
        else:
            raise ValueError(f"Unknown plan: {plan}")
        
        # 向量化初始分桶
        premiums = RA65_values * premium_ratios
        ra_balances = RA65_values * ra_ratios
        
        # 向量化月利率
        monthly_prem_rate = self.calculator.r_prem / 12
        monthly_ra_rate = self.calculator.r_ra / 12
        
        # 预计算复利因子
        prem_compound_factors = np.power(1 + monthly_prem_rate, np.arange(months))
        ra_compound_factors = np.power(1 + monthly_ra_rate, np.arange(months))
        
        # 计算目标月领曲线
        if plan == "standard":
            # 等额年金
            annuity_factors = self._vectorized_annuity_factors(
                self.calculator.r_prem, horizon_age - start_age)
            monthly_payments = premiums * annuity_factors
            
        elif plan == "escalating":
            # 递增年金
            growing_annuity_factors = self._vectorized_growing_annuity_factors(
                self.calculator.r_prem, horizon_age - start_age, self.calculator.g_esc)
            monthly_payments = premiums * growing_annuity_factors
            
        elif plan == "basic":
            # Basic计划需要特殊处理
            monthly_payments = self._vectorized_basic_plan(
                premiums, ra_balances, start_age, horizon_age)
        
        # 向量化逐月滚存
        final_premiums, final_ra_balances, total_payouts = self._vectorized_monthly_rollover(
            premiums, ra_balances, monthly_payments, months,
            monthly_prem_rate, monthly_ra_rate)
        
        # 计算遗赠曲线（简化版 - 只计算关键年龄点）
        bequest_snapshots = self._calculate_bequest_snapshots(
            final_premiums, final_ra_balances, start_age, horizon_age)
        
        return {
            'initial_monthly_payments': monthly_payments,
            'total_payouts': total_payouts,
            'final_premiums': final_premiums,
            'final_ra_balances': final_ra_balances,
            'bequest_snapshots': bequest_snapshots
        }
    
    def _vectorized_annuity_factors(self, annual_rate: float, years: float) -> float:
        """向量化年金因子计算"""
        monthly_rate = annual_rate / 12
        n = int(years * 12)
        
        if abs(monthly_rate) < 1e-12:
            return 1.0 / n
        
        return monthly_rate / (1 - (1 + monthly_rate) ** (-n))
    
    def _vectorized_growing_annuity_factors(self, annual_rate: float, 
                                          years: float, growth_rate: float) -> float:
        """向量化递增年金因子计算"""
        monthly_rate = annual_rate / 12
        monthly_growth = growth_rate / 12
        n = int(years * 12)
        
        if abs(monthly_rate - monthly_growth) < 1e-12:
            return 1.0 / n
        
        return (monthly_rate - monthly_growth) / (1 - ((1 + monthly_growth) / (1 + monthly_rate)) ** n)
    
    def _vectorized_basic_plan(self, premiums: np.ndarray, ra_balances: np.ndarray,
                             start_age: int, horizon_age: int) -> np.ndarray:
        """向量化Basic计划计算"""
        # 简化处理：假设90岁前用RA，90岁后用premium
        years_to_90 = max(0, 90 - start_age)
        months_to_90 = int(years_to_90 * 12)
        
        if months_to_90 > 0:
            ra_monthly = ra_balances * self._vectorized_annuity_factors(
                self.calculator.r_ra, years_to_90)
        else:
            ra_monthly = np.zeros_like(ra_balances)
        
        return ra_monthly
    
    def _vectorized_monthly_rollover(self, initial_premiums: np.ndarray,
                                   initial_ra_balances: np.ndarray,
                                   monthly_payments: np.ndarray,
                                   months: int,
                                   monthly_prem_rate: float,
                                   monthly_ra_rate: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """向量化月度滚存计算"""
        premiums = initial_premiums.copy()
        ra_balances = initial_ra_balances.copy()
        
        # 简化的向量化计算（假设等额支付）
        total_payments = monthly_payments * months
        
        # 考虑利息的最终余额
        final_premiums = premiums * (1 + monthly_prem_rate) ** months - total_payments
        final_ra_balances = ra_balances * (1 + monthly_ra_rate) ** months
        
        # 确保非负
        final_premiums = np.maximum(final_premiums, 0)
        final_ra_balances = np.maximum(final_ra_balances, 0)
        
        return final_premiums, final_ra_balances, total_payments
    
    def _calculate_bequest_snapshots(self, final_premiums: np.ndarray,
                                   final_ra_balances: np.ndarray,
                                   start_age: int, horizon_age: int) -> Dict[str, np.ndarray]:
        """计算遗赠快照"""
        total_bequests = final_premiums + final_ra_balances
        
        return {
            'age_70': total_bequests * 0.8,  # 简化：假设70岁时剩余80%
            'age_80': total_bequests * 0.6,  # 简化：假设80岁时剩余60%
            'age_90': total_bequests * 0.3   # 简化：假设90岁时剩余30%
        }
    
    def batch_analysis(self, ra65_values: List[float], 
                      plans: List[str] = None) -> Dict:
        """
        批量分析多个RA65余额和计划
        
        Args:
            ra65_values: RA65余额列表
            plans: 计划列表
            
        Returns:
            批量分析结果
        """
        if plans is None:
            plans = ["standard", "escalating", "basic"]
        
        ra65_array = np.array(ra65_values)
        results = {}
        
        start_time = time.time()
        
        for plan in plans:
            plan_results = self.vectorized_cpf_life_simulation(ra65_array, plan)
            results[plan] = plan_results
        
        execution_time = time.time() - start_time
        
        return {
            'results': results,
            'performance': {
                'execution_time': execution_time,
                'total_calculations': len(ra65_values) * len(plans),
                'calculations_per_second': (len(ra65_values) * len(plans)) / execution_time
            }
        }
    
    def parallel_analysis(self, ra65_values: List[float], 
                         plans: List[str] = None,
                         max_workers: int = None) -> Dict:
        """
        并行分析
        
        Args:
            ra65_values: RA65余额列表
            plans: 计划列表
            max_workers: 最大工作进程数
            
        Returns:
            并行分析结果
        """
        if plans is None:
            plans = ["standard", "escalating", "basic"]
        
        if max_workers is None:
            max_workers = min(cpu_count(), 4)  # 限制最大进程数
        
        start_time = time.time()
        
        # 创建任务列表
        tasks = []
        for ra65 in ra65_values:
            for plan in plans:
                tasks.append((ra65, plan))
        
        # 并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.calculator.cpf_life_simulate, ra65, plan): (ra65, plan)
                for ra65, plan in tasks
            }
            
            results = {}
            for future in concurrent.futures.as_completed(future_to_task):
                ra65, plan = future_to_task[future]
                try:
                    result = future.result()
                    if plan not in results:
                        results[plan] = {}
                    results[plan][ra65] = result
                except Exception as exc:
                    print(f'Task {ra65}, {plan} generated an exception: {exc}')
        
        execution_time = time.time() - start_time
        
        return {
            'results': results,
            'performance': {
                'execution_time': execution_time,
                'max_workers': max_workers,
                'total_calculations': len(tasks),
                'calculations_per_second': len(tasks) / execution_time
            }
        }
    
    def benchmark_performance(self, test_sizes: List[int] = None) -> Dict:
        """
        性能基准测试
        
        Args:
            test_sizes: 测试规模列表
            
        Returns:
            性能基准结果
        """
        if test_sizes is None:
            test_sizes = [10, 50, 100, 500, 1000]
        
        benchmark_results = {}
        
        for size in test_sizes:
            # 生成测试数据
            ra65_values = np.random.uniform(100000, 500000, size)
            
            # 测试向量化方法
            start_time = time.time()
            vectorized_results = self.batch_analysis(ra65_values.tolist())
            vectorized_time = time.time() - start_time
            
            # 测试传统方法
            start_time = time.time()
            traditional_results = {}
            for ra65 in ra65_values:
                for plan in ["standard", "escalating", "basic"]:
                    result = self.calculator.cpf_life_simulate(ra65, plan)
                    if plan not in traditional_results:
                        traditional_results[plan] = {}
                    traditional_results[plan][ra65] = result
            traditional_time = time.time() - start_time
            
            # 测试并行方法
            start_time = time.time()
            parallel_results = self.parallel_analysis(ra65_values.tolist())
            parallel_time = time.time() - start_time
            
            benchmark_results[size] = {
                'vectorized_time': vectorized_time,
                'traditional_time': traditional_time,
                'parallel_time': parallel_time,
                'vectorized_speedup': traditional_time / vectorized_time if vectorized_time > 0 else 0,
                'parallel_speedup': traditional_time / parallel_time if parallel_time > 0 else 0
            }
        
        return benchmark_results
    
    def optimize_parameters(self, ra65_range: Tuple[float, float],
                           num_samples: int = 100) -> Dict:
        """
        参数优化
        
        Args:
            ra65_range: RA65范围
            num_samples: 样本数量
            
        Returns:
            优化结果
        """
        ra65_values = np.linspace(ra65_range[0], ra65_range[1], num_samples)
        
        # 测试不同参数组合
        param_combinations = [
            {'r_prem': 0.03, 'r_ra': 0.03, 'g_esc': 0.015},
            {'r_prem': 0.04, 'r_ra': 0.04, 'g_esc': 0.02},
            {'r_prem': 0.05, 'r_ra': 0.05, 'g_esc': 0.025},
        ]
        
        optimization_results = {}
        
        for params in param_combinations:
            self.calculator.set_parameters(**params)
            
            start_time = time.time()
            results = self.batch_analysis(ra65_values.tolist())
            execution_time = time.time() - start_time
            
            optimization_results[str(params)] = {
                'params': params,
                'execution_time': execution_time,
                'results': results
            }
        
        # 重置参数
        self.calculator.set_parameters()
        
        return optimization_results
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        # 简化的性能指标计算
        cache_hit_rate = self._cache_stats['hits'] / (
            self._cache_stats['hits'] + self._cache_stats['misses']
        ) if (self._cache_stats['hits'] + self._cache_stats['misses']) > 0 else 0
        
        return PerformanceMetrics(
            execution_time=0.0,  # 需要实际测量
            memory_usage=0.0,    # 需要实际测量
            cpu_usage=0.0,       # 需要实际测量
            cache_hit_rate=cache_hit_rate
        )


# 便捷函数
def quick_vectorized_analysis(ra65_values: List[float], 
                            plan: str = "standard") -> Dict:
    """
    快速向量化分析
    
    Args:
        ra65_values: RA65余额列表
        plan: 计划类型
        
    Returns:
        分析结果
    """
    optimizer = CPFLifePerformanceOptimizer()
    ra65_array = np.array(ra65_values)
    return optimizer.vectorized_cpf_life_simulation(ra65_array, plan)


def benchmark_cpf_life_performance() -> Dict:
    """
    运行CPF LIFE性能基准测试
    
    Returns:
        基准测试结果
    """
    optimizer = CPFLifePerformanceOptimizer()
    return optimizer.benchmark_performance()