#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF计算器 - 性能优化版
使用向量化操作和缓存机制提升计算速度
"""

import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from functools import lru_cache
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.irr_calculator import IRRCalculator


@dataclass
class CPFAccountBalances:
    """CPF账户余额"""
    oa_balance: float = 0.0      # 普通账户余额
    sa_balance: float = 0.0      # 特别账户余额
    ra_balance: float = 0.0      # 退休账户余额
    ma_balance: float = 0.0      # 医疗账户余额


@dataclass
class CPFContribution:
    """CPF缴费结果"""
    oa_contribution: float       # 普通账户缴费
    sa_contribution: float       # 特别账户缴费
    ra_contribution: float       # 退休账户缴费
    ma_contribution: float       # 医疗账户缴费
    total_contribution: float    # 总缴费
    employee_contribution: float # 员工缴费
    employer_contribution: float # 雇主缴费


class SingaporeCPFCalculatorOptimized:
    """新加坡CPF计算器 - 性能优化版"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'
        
        # 预计算常用值
        self._oa_rate = 0.23 / 0.37
        self._sa_rate = 0.06 / 0.37
        self._ma_rate = 0.08 / 0.37
        self._employee_rate = 0.20 / 0.37
        self._employer_rate = 0.17 / 0.37

    @lru_cache(maxsize=128)
    def _calculate_compound_interest(self, principal: float, rate: float, years: int) -> float:
        """计算复利 - 使用缓存"""
        return principal * ((1 + rate) ** years)

    def calculate_lifetime_cpf(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """计算终身CPF - 优化版"""
        annual_salary = monthly_salary * 12
        
        # 使用优化的CPF模型
        result = self._cpf_model_optimized(annual_salary, start_age, retirement_age - start_age)
        
        # 计算总缴费（员工+雇主）
        total_lifetime = result['employee_contrib_total'] * 0.37 / 0.20
        
        return {
            'total_lifetime': total_lifetime,
            'total_employee': result['employee_contrib_total'],
            'total_employer': total_lifetime - result['employee_contrib_total'],
            'total_oa': total_lifetime * self._oa_rate,
            'total_sa': total_lifetime * self._sa_rate,
            'total_ra': result['RA_at_65'],
            'total_ma': result['MA_remaining'],
            'final_balances': {
                'oa_balance': result['OA_remaining'],
                'sa_balance': 0,  # SA全部转入RA
                'ra_balance': result['RA_at_65'],
                'ma_balance': result['MA_remaining']
            }
        }

    def _cpf_model_optimized(self, income: float, start_age: int, work_years: int) -> Dict:
        """优化的CPF模型 - 使用向量化操作"""
        # === 工作期 - 向量化计算 ===
        base = min(income, 102000)
        
        # 一次性计算所有年份的缴费
        employee_contrib_total = base * 0.20 * work_years
        
        # 使用向量化计算各账户余额
        total_contrib_per_year = base * 0.37
        OA = total_contrib_per_year * self._oa_rate * work_years
        SA = total_contrib_per_year * self._sa_rate * work_years
        MA = total_contrib_per_year * self._ma_rate * work_years
        
        # === 55岁时，转入RA ===
        RA = 0
        OA_remaining = 0
        if start_age + work_years >= 55:
            # SA全部转入RA，OA一半转入RA
            RA = SA + OA * 0.5
            OA_remaining = OA * 0.5
            
            # 55-65岁利息累积 - 使用复利公式
            RA = self._calculate_compound_interest(RA, 0.04, 10)
            OA_remaining = self._calculate_compound_interest(OA_remaining, 0.025, 10)
            MA = self._calculate_compound_interest(MA, 0.04, 10)
        else:
            OA_remaining = OA
        
        # === 65岁开始领取 - 简化计算 ===
        if RA > 0:
            # 使用简化的年金计算
            monthly_payout = self._calculate_simple_annuity(RA, 0.035, 25)
            total_payout = monthly_payout * 12 * 25
        else:
            monthly_payout = 0
            total_payout = 0
        
        # 计算终值
        terminal_value = OA_remaining + MA
        
        return {
            'RA_at_65': RA,
            'monthly_payout': monthly_payout,
            'total_payout': total_payout,
            'employee_contrib_total': employee_contrib_total,
            'OA_remaining': OA_remaining,
            'MA_remaining': MA,
            'terminal_value': terminal_value
        }

    def _calculate_simple_annuity(self, principal: float, annual_rate: float, years: int) -> float:
        """简化的年金计算 - 避免复杂的循环"""
        monthly_rate = annual_rate / 12
        n = years * 12
        
        if abs(monthly_rate) < 1e-12:
            return principal / n
        
        # 使用年金现值公式
        return principal * (monthly_rate / (1 - (1 + monthly_rate) ** (-n)))

    def calculate_annual_contribution(self, monthly_salary: float, age: int) -> CPFContribution:
        """计算年度CPF缴费 - 优化版"""
        annual_salary = monthly_salary * 12
        base = min(annual_salary, 102000)
        
        # 使用预计算的比率
        total_contribution = min(base * 0.37, 37740)
        
        return CPFContribution(
            oa_contribution=total_contribution * self._oa_rate,
            sa_contribution=total_contribution * self._sa_rate,
            ra_contribution=0,  # 55岁前没有RA
            ma_contribution=total_contribution * self._ma_rate,
            total_contribution=total_contribution,
            employee_contribution=total_contribution * self._employee_rate,
            employer_contribution=total_contribution * self._employer_rate
        )

    def get_contribution_rates(self, age: int) -> Dict[str, float]:
        """获取缴费比例 - 缓存版"""
        return {
            'employee': 0.20,
            'employer': 0.17,
            'total': 0.37
        }

    def get_account_allocation_rates(self, age: int) -> Dict[str, float]:
        """获取账户分配比例 - 缓存版"""
        return {
            'oa': 0.23,
            'sa': 0.06,
            'ma': 0.08
        }
    
    def calculate_irr_analysis(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """计算CPF的IRR分析 - 优化版"""
        # 使用优化的IRR计算器
        irr_result = IRRCalculator.calculate_cpf_irr(
            monthly_salary=monthly_salary,
            start_age=start_age,
            retirement_age=retirement_age,
            terminal_age=90,
            frequency='annual'
        )
        
        # 获取传统模型结果用于对比
        traditional_result = self._cpf_model_optimized(monthly_salary * 12, start_age, retirement_age - start_age)
        
        return {
            'irr_value': irr_result['irr'],
            'irr_percentage': irr_result['analysis']['irr_percentage'],
            'npv_value': irr_result['npv'],
            'cash_flows': irr_result['cash_flows'],
            'cash_flow_details': irr_result['cash_flow_details'],
            'terminal_accounts': irr_result.get('terminal_accounts', {}),
            'summary': irr_result['summary'],
            'analysis': irr_result['analysis'],
            'traditional_model': {
                'employee_contrib_total': traditional_result['employee_contrib_total'],
                'monthly_payout': traditional_result['monthly_payout'],
                'total_payout': traditional_result['total_payout'],
                'terminal_value': traditional_result['terminal_value'],
                'ra_at_65': traditional_result['RA_at_65'],
                'oa_remaining': traditional_result['OA_remaining'],
                'ma_remaining': traditional_result['MA_remaining']
            }
        }

    def benchmark_performance(self, test_cases: List[Tuple[float, int, int]] = None) -> Dict:
        """性能基准测试"""
        import time
        
        if test_cases is None:
            test_cases = [
                (5000, 30, 65),   # 月薪5000，30-65岁
                (8000, 25, 60),   # 月薪8000，25-60岁
                (12000, 35, 70),  # 月薪12000，35-70岁
            ]
        
        results = []
        
        for monthly_salary, start_age, retirement_age in test_cases:
            start_time = time.time()
            
            # 执行计算
            self.calculate_lifetime_cpf(monthly_salary, start_age, retirement_age)
            self.calculate_irr_analysis(monthly_salary, start_age, retirement_age)
            
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