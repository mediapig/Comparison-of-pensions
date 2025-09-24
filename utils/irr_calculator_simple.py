#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的IRR计算器
专注于性能和准确性
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from functools import lru_cache


class IRRCalculatorSimple:
    """简化的IRR计算器"""

    @staticmethod
    def calculate_irr(cash_flows: List[float], max_iterations: int = 100, tolerance: float = 1e-6) -> float:
        """计算IRR - 简化版"""
        if not cash_flows or len(cash_flows) < 2:
            return 0.0
        
        # 转换为numpy数组
        cash_flows_array = np.array(cash_flows, dtype=float)
        
        # 检查是否有正负现金流
        if np.all(cash_flows_array >= 0) or np.all(cash_flows_array <= 0):
            return 0.0
        
        # 使用二分法查找IRR
        return IRRCalculatorSimple._binary_search_irr(cash_flows_array, tolerance)

    @staticmethod
    def _binary_search_irr(cash_flows: np.ndarray, tolerance: float) -> float:
        """使用二分法查找IRR"""
        # 确定搜索范围
        low = -0.99
        high = 10.0
        
        # 二分搜索
        for _ in range(100):  # 最多100次迭代
            mid = (low + high) / 2
            npv = IRRCalculatorSimple._calculate_npv(cash_flows, mid)
            
            if abs(npv) < tolerance:
                return mid
            
            if npv > 0:
                low = mid
            else:
                high = mid
            
            # 检查收敛
            if high - low < tolerance:
                return mid
        
        return mid

    @staticmethod
    def _calculate_npv(cash_flows: np.ndarray, rate: float) -> float:
        """计算NPV"""
        periods = np.arange(len(cash_flows))
        discount_factors = (1 + rate) ** periods
        return np.sum(cash_flows / discount_factors)

    @staticmethod
    def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
        """计算NPV"""
        if not cash_flows:
            return 0.0
        
        cash_flows_array = np.array(cash_flows)
        periods = np.arange(len(cash_flows_array))
        discount_factors = (1 + discount_rate) ** periods
        return np.sum(cash_flows_array / discount_factors)

    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_cpf_irr(monthly_salary: float,
                         start_age: int = 30,
                         retirement_age: int = 65,
                         terminal_age: int = 90,
                         frequency: str = 'annual') -> Dict[str, Any]:
        """计算CPF的IRR - 简化版"""
        # 构建现金流
        cash_flow_data = IRRCalculatorSimple._build_cpf_cash_flows(
            monthly_salary, start_age, retirement_age, terminal_age, frequency
        )
        
        cash_flows = cash_flow_data['cash_flows']
        
        # 计算IRR
        irr_value = IRRCalculatorSimple.calculate_irr(cash_flows)
        
        # 计算NPV
        npv_value = IRRCalculatorSimple.calculate_npv(cash_flows, irr_value) if irr_value else 0
        
        # 计算其他指标
        cash_flows_array = np.array(cash_flows)
        negative_flows = cash_flows_array[cash_flows_array < 0]
        positive_flows = cash_flows_array[cash_flows_array > 0]
        
        total_employee_contrib = abs(np.sum(negative_flows))
        total_benefits = np.sum(positive_flows)
        net_benefit = total_benefits - total_employee_contrib
        
        # 计算90岁时各账户余额
        annual_salary = monthly_salary * 12
        terminal_accounts = IRRCalculatorSimple._calculate_terminal_accounts(annual_salary, start_age, retirement_age, terminal_age)
        
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
    def _build_cpf_cash_flows(monthly_salary: float,
                             start_age: int,
                             retirement_age: int,
                             terminal_age: int,
                             frequency: str = 'annual') -> Dict[str, Any]:
        """构建CPF现金流 - 简化版"""
        annual_salary = monthly_salary * 12
        work_years = retirement_age - start_age
        retirement_years = terminal_age - retirement_age
        
        # 工作期现金流（员工缴费为负）
        work_cash_flows = [-annual_salary * 0.20] * work_years
        
        # 计算退休期现金流
        ra_balance = IRRCalculatorSimple._calculate_ra_balance(annual_salary, start_age, retirement_age)
        monthly_payout = IRRCalculatorSimple._calculate_monthly_payout(ra_balance)
        annual_payout = monthly_payout * 12
        
        # 退休期现金流
        retirement_cash_flows = [annual_payout] * retirement_years
        
        # 计算终值
        terminal_value = IRRCalculatorSimple._calculate_terminal_value(annual_salary, start_age, retirement_age, terminal_age)
        
        # 合并现金流
        cash_flows = work_cash_flows + retirement_cash_flows + [terminal_value]
        
        # 构建详细信息
        cash_flow_details = []
        
        # 工作期详情
        for i, contrib in enumerate(work_cash_flows):
            cash_flow_details.append({
                'age': start_age + i,
                'month': 12,
                'period': i + 1,
                'cash_flow': contrib,
                'type': 'employee_contribution',
                'description': f'员工CPF缴费 (年龄{start_age + i})'
            })
        
        # 退休期详情
        for i, payout in enumerate(retirement_cash_flows):
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
            'cash_flows': cash_flows,
            'cash_flow_details': cash_flow_details,
            'total_periods': len(cash_flows),
            'frequency': frequency,
            'summary': {
                'total_employee_contributions': abs(sum(work_cash_flows)),
                'total_retirement_payouts': sum(retirement_cash_flows),
                'terminal_value': terminal_value,
                'net_cash_flow': sum(cash_flows)
            }
        }

    @staticmethod
    @lru_cache(maxsize=64)
    def _calculate_ra_balance(annual_salary: float, start_age: int, retirement_age: int) -> float:
        """计算65岁时的RA余额"""
        work_years = retirement_age - start_age
        base = min(annual_salary, 102000)
        
        # 计算各账户余额
        total_contrib_per_year = base * 0.37
        OA = total_contrib_per_year * (0.23 / 0.37) * work_years
        SA = total_contrib_per_year * (0.06 / 0.37) * work_years
        
        # 55岁时转入RA
        if retirement_age >= 55:
            RA = SA + OA * 0.5
            # 55-65岁利息累积
            RA *= (1.04 ** 10)
        else:
            RA = SA + OA * 0.5
        
        return RA

    @staticmethod
    @lru_cache(maxsize=64)
    def _calculate_monthly_payout(ra_balance: float) -> float:
        """计算月退休金"""
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
    @lru_cache(maxsize=64)
    def _calculate_terminal_value(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> float:
        """计算终值"""
        terminal_accounts = IRRCalculatorSimple._calculate_terminal_accounts(annual_salary, start_age, retirement_age, terminal_age)
        return terminal_accounts['total']
    
    @staticmethod
    @lru_cache(maxsize=64)
    def _calculate_terminal_accounts(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> Dict[str, float]:
        """计算90岁时各账户的详细余额"""
        work_years = retirement_age - start_age
        base = min(annual_salary, 102000)
        
        # 计算各账户余额
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