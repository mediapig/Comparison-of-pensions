#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IRR计算器 - 性能优化版
使用向量化操作和缓存机制提升计算速度
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from functools import lru_cache
import math


class IRRCalculatorOptimized:
    """IRR计算器 - 性能优化版"""

    @staticmethod
    def calculate_irr(cash_flows: List[float], max_iterations: int = 100, tolerance: float = 1e-6) -> float:
        """计算IRR - 优化版"""
        if not cash_flows or len(cash_flows) < 2:
            return 0.0
        
        # 转换为numpy数组进行向量化计算
        cash_flows_array = np.array(cash_flows)
        
        # 检查是否有正负现金流
        if np.all(cash_flows_array >= 0) or np.all(cash_flows_array <= 0):
            return 0.0
        
        # 使用牛顿-拉夫逊方法优化
        return IRRCalculatorOptimized._newton_raphson_irr(cash_flows_array, max_iterations, tolerance)

    @staticmethod
    def _newton_raphson_irr(cash_flows: np.ndarray, max_iterations: int, tolerance: float) -> float:
        """牛顿-拉夫逊方法计算IRR - 向量化版本"""
        # 初始猜测
        rate = 0.1
        
        for _ in range(max_iterations):
            # 计算现值函数和导数
            pv, dpv = IRRCalculatorOptimized._calculate_pv_and_derivative(cash_flows, rate)
            
            if abs(pv) < tolerance:
                return rate
            
            if abs(dpv) < tolerance:
                break
                
            # 牛顿-拉夫逊更新
            new_rate = rate - pv / dpv
            
            # 防止发散
            if new_rate < -0.99:
                new_rate = -0.99
            elif new_rate > 10.0:
                new_rate = 10.0
            
            # 检查收敛
            if abs(new_rate - rate) < tolerance:
                return new_rate
                
            rate = new_rate
        
        return rate

    @staticmethod
    def _calculate_pv_and_derivative(cash_flows: np.ndarray, rate: float) -> Tuple[float, float]:
        """计算现值函数和导数 - 向量化版本"""
        n = len(cash_flows)
        periods = np.arange(n)
        
        # 现值函数: NPV = sum(CF[i] / (1 + r)^i)
        discount_factors = (1 + rate) ** periods
        pv = np.sum(cash_flows / discount_factors)
        
        # 导数: dNPV/dr = sum(-i * CF[i] / (1 + r)^(i+1))
        derivative_factors = periods * cash_flows / ((1 + rate) ** (periods + 1))
        dpv = -np.sum(derivative_factors)
        
        return pv, dpv

    @staticmethod
    def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
        """计算NPV - 优化版"""
        if not cash_flows:
            return 0.0
        
        cash_flows_array = np.array(cash_flows)
        periods = np.arange(len(cash_flows_array))
        
        # 向量化计算NPV
        discount_factors = (1 + discount_rate) ** periods
        npv = np.sum(cash_flows_array / discount_factors)
        
        return npv

    @staticmethod
    @lru_cache(maxsize=256)
    def calculate_cpf_irr(monthly_salary: float,
                         start_age: int = 30,
                         retirement_age: int = 65,
                         terminal_age: int = 90,
                         frequency: str = 'annual') -> Dict[str, Any]:
        """
        计算CPF的IRR - 优化版（带缓存）
        """
        # 构建现金流 - 使用优化版本
        cash_flow_data = IRRCalculatorOptimized.build_cpf_cash_flows_optimized(
            monthly_salary, start_age, retirement_age, terminal_age, frequency
        )
        
        cash_flows = cash_flow_data['cash_flows']
        
        # 计算IRR
        irr_value = IRRCalculatorOptimized.calculate_irr(cash_flows)
        
        # 计算NPV
        npv_value = IRRCalculatorOptimized.calculate_npv(cash_flows, irr_value) if irr_value else 0
        
        # 计算其他指标 - 向量化计算
        cash_flows_array = np.array(cash_flows)
        negative_flows = cash_flows_array[cash_flows_array < 0]
        positive_flows = cash_flows_array[cash_flows_array > 0]
        
        total_employee_contrib = abs(np.sum(negative_flows))
        total_benefits = np.sum(positive_flows)
        net_benefit = total_benefits - total_employee_contrib
        
        # 计算90岁时各账户余额
        annual_salary = monthly_salary * 12
        terminal_accounts = IRRCalculatorOptimized._calculate_terminal_accounts_optimized(annual_salary, start_age, retirement_age, terminal_age)
        
        return {
            'irr': irr_value,
            'npv': npv_value,
            'cash_flows': cash_flows,
            'cash_flow_details': cash_flow_data['cash_flow_details'],
            'terminal_accounts': terminal_accounts,
            'summary': {
                'total_employee_contributions': total_employee_contrib,
                'total_benefits': total_benefits,
                'net_benefit': net_benefit,
                'total_periods': len(cash_flows),
                'frequency': frequency
            },
            'analysis': {
                'irr_percentage': irr_value * 100 if irr_value else None,
                'is_positive_return': irr_value > 0 if irr_value else False,
                'payback_period_years': None
            }
        }

    @staticmethod
    def build_cpf_cash_flows_optimized(monthly_salary: float,
                                     start_age: int,
                                     retirement_age: int,
                                     terminal_age: int,
                                     frequency: str = 'annual') -> Dict[str, Any]:
        """
        构建CPF现金流 - 优化版
        """
        annual_salary = monthly_salary * 12
        work_years = retirement_age - start_age
        retirement_years = terminal_age - retirement_age
        
        # 使用向量化计算工作期现金流
        work_periods = np.arange(work_years)
        annual_contributions = np.full(work_years, -annual_salary * 0.20)  # 员工缴费为负现金流
        
        # 计算退休期现金流
        ra_balance = IRRCalculatorOptimized._calculate_ra_balance_optimized(annual_salary, start_age, retirement_age)
        monthly_payout = IRRCalculatorOptimized._calculate_monthly_payout_optimized(ra_balance)
        
        # 构建退休期现金流
        retirement_periods = np.arange(retirement_years)
        annual_payouts = np.full(retirement_years, monthly_payout * 12)
        
        # 计算终值
        terminal_value = IRRCalculatorOptimized._calculate_terminal_value_optimized(annual_salary, start_age, retirement_age, terminal_age)
        
        # 合并现金流
        cash_flows = np.concatenate([annual_contributions, annual_payouts, [terminal_value]])
        
        # 构建详细信息
        cash_flow_details = []
        
        # 工作期详情
        for i, contrib in enumerate(annual_contributions):
            cash_flow_details.append({
                'age': start_age + i,
                'month': 12,
                'period': i + 1,
                'cash_flow': contrib,
                'type': 'employee_contribution',
                'description': f'员工CPF缴费 (年龄{start_age + i})'
            })
        
        # 退休期详情
        for i, payout in enumerate(annual_payouts):
            cash_flow_details.append({
                'age': retirement_age + i,
                'month': 12,
                'period': work_years + i + 1,
                'cash_flow': payout,
                'type': 'retirement_payout',
                'description': f'退休金领取 (年龄{retirement_age + i})'
            })
        
        # 终值详情
        cash_flow_details.append({
            'age': terminal_age,
            'month': 12,
            'period': work_years + retirement_years + 1,
            'cash_flow': terminal_value,
            'type': 'terminal_value',
            'description': f'终值 (年龄{terminal_age})'
        })
        
        return {
            'cash_flows': cash_flows.tolist(),
            'cash_flow_details': cash_flow_details,
            'total_periods': len(cash_flows),
            'frequency': frequency,
            'summary': {
                'total_employee_contributions': abs(np.sum(annual_contributions)),
                'total_retirement_payouts': np.sum(annual_payouts),
                'terminal_value': terminal_value,
                'net_cash_flow': np.sum(cash_flows)
            }
        }

    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_ra_balance_optimized(annual_salary: float, start_age: int, retirement_age: int) -> float:
        """计算65岁时的RA余额 - 优化版"""
        work_years = retirement_age - start_age
        base = min(annual_salary, 102000)
        
        # 向量化计算各账户余额
        total_contrib_per_year = base * 0.37
        OA = total_contrib_per_year * (0.23 / 0.37) * work_years
        SA = total_contrib_per_year * (0.06 / 0.37) * work_years
        MA = total_contrib_per_year * (0.08 / 0.37) * work_years
        
        # 55岁时转入RA
        if retirement_age >= 55:
            RA = SA + OA * 0.5
            
            # 55-65岁利息累积
            RA *= (1.04 ** 10)
        else:
            RA = SA + OA * 0.5
        
        return RA

    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_monthly_payout_optimized(ra_balance: float) -> float:
        """计算月退休金 - 优化版"""
        if ra_balance <= 0:
            return 0.0
        
        # 简化的年金计算
        annual_rate = 0.035
        years = 25
        monthly_rate = annual_rate / 12
        n = years * 12
        
        if abs(monthly_rate) < 1e-12:
            return ra_balance / n
        
        return ra_balance * (monthly_rate / (1 - (1 + monthly_rate) ** (-n)))

    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_terminal_value_optimized(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> float:
        """计算终值 - 优化版"""
        terminal_accounts = IRRCalculatorOptimized._calculate_terminal_accounts_optimized(annual_salary, start_age, retirement_age, terminal_age)
        return terminal_accounts['total']
    
    @staticmethod
    @lru_cache(maxsize=128)
    def _calculate_terminal_accounts_optimized(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> Dict[str, float]:
        """计算90岁时各账户的详细余额 - 优化版"""
        work_years = retirement_age - start_age
        base = min(annual_salary, 102000)
        
        # 向量化计算各账户余额
        total_contrib_per_year = base * 0.37
        OA = total_contrib_per_year * (0.23 / 0.37) * work_years
        MA = total_contrib_per_year * (0.08 / 0.37) * work_years
        
        # 55岁时转入RA
        if retirement_age >= 55:
            OA_remaining = OA * 0.5
            
            # 55-65岁利息累积
            OA_remaining *= (1.025 ** 10)
            MA *= (1.04 ** 10)
            
            # 65-90岁：OA和MA继续累积利息
            remaining_years = terminal_age - retirement_age
            OA_remaining *= (1.025 ** remaining_years)
            MA *= (1.04 ** remaining_years)
        else:
            OA_remaining = OA * 0.5
        
        return {
            'OA': OA_remaining,
            'SA': 0,  # SA已转入RA
            'MA': MA,
            'RA': 0,  # RA已用于年金
            'total': OA_remaining + MA
        }

    @staticmethod
    def benchmark_performance(test_cases: List[Tuple[float, int, int]] = None) -> Dict:
        """性能基准测试"""
        import time
        
        if test_cases is None:
            test_cases = [
                (10000, 30, 65),
                (8000, 25, 60),
                (12000, 35, 70),
            ]
        
        results = []
        
        for monthly_salary, start_age, retirement_age in test_cases:
            start_time = time.time()
            
            # 执行计算
            IRRCalculatorOptimized.calculate_cpf_irr(monthly_salary, start_age, retirement_age, 90, 'annual')
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            results.append({
                'monthly_salary': monthly_salary,
                'start_age': start_age,
                'retirement_age': retirement_age,
                'execution_time': execution_time
            })
        
        return {
            'test_cases': results,
            'average_time': sum(r['execution_time'] for r in results) / len(results),
            'total_time': sum(r['execution_time'] for r in results)
        }