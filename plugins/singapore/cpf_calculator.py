#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF计算器 - 修正版
使用验证过的正确CPF计算逻辑
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass
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


class SingaporeCPFCalculator:
    """新加坡CPF计算器 - 修正版"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

    def calculate_lifetime_cpf(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """计算终身CPF - 使用简化的正确模型"""
        annual_salary = monthly_salary * 12
        
        # 使用简化的CPF模型
        result = self._cpf_model(annual_salary, start_age, retirement_age - start_age)
        
        # 计算总缴费（员工+雇主）
        total_lifetime = result['employee_contrib_total'] * 0.37 / 0.20  # 员工缴费 / 20% * 37%
        
        return {
            'total_lifetime': total_lifetime,
            'total_employee': result['employee_contrib_total'],  # 员工部分
            'total_employer': total_lifetime - result['employee_contrib_total'],  # 雇主部分
            'total_oa': total_lifetime * 0.23 / 0.37,  # OA部分
            'total_sa': total_lifetime * 0.06 / 0.37,  # SA部分
            'total_ra': result['RA_at_65'],  # RA余额
            'total_ma': result['MA_remaining'],  # MA余额
            'final_balances': {
                'oa_balance': result['OA_remaining'],
                'sa_balance': 0,  # SA全部转入RA
                'ra_balance': result['RA_at_65'],
                'ma_balance': result['MA_remaining']
            }
        }

    def _cpf_model(self, income, start_age, work_years):
        """简化的CPF模型 - 基于我们验证过的正确逻辑"""
        # === 工作期 ===
        employee_contrib_total = 0  # 雇员总缴费（用于IRR）
        OA = 0
        SA = 0
        MA = 0
        
        for age in range(start_age, start_age + work_years):
            base = min(income, 102000)   # 年薪上限
            employee_contrib = base * 0.20  # 雇员缴费
            employer_contrib = base * 0.17   # 雇主缴费
            total_contrib = employee_contrib + employer_contrib  # 总缴费37%
            
            employee_contrib_total += employee_contrib
            
            # 按比例分配 OA, SA, MA（确保分配总额等于总缴费）
            OA += total_contrib * 0.23 / 0.37  # OA: 23%
            SA += total_contrib * 0.06 / 0.37  # SA: 6%
            MA += total_contrib * 0.08 / 0.37  # MA: 8%
        
        # === 55岁时，转入RA ===
        RA = 0
        OA_remaining = 0
        if start_age + work_years >= 55:
            # 假设SA全部转入RA，OA部分转入RA
            RA = SA + OA * 0.5  # 假设OA的一半转入RA
            OA_remaining = OA * 0.5  # OA剩余部分
            
            # 55–65岁利息累积
            for i in range(10):
                RA *= 1.04   # 年息4%
                OA_remaining *= 1.025  # OA年息2.5%
                MA *= 1.04  # MA年息4%
        else:
            OA_remaining = OA
        
        # === 65岁开始领取 ===
        # 使用新的CPF Life计算方法
        if RA > 0:
            from .cpf_payout_calculator import SingaporeCPFPayoutCalculator
            payout_calculator = SingaporeCPFPayoutCalculator()
            
            # 使用CPF Life Standard计划计算月养老金
            cpf_life_result = payout_calculator.compute_cpf_life_payout(
                RA65=RA,
                plan="standard",
                start_age=65,
                nominal_discount_rate=0.035,  # 3.5%年利率
                expected_life_years=25,       # 25年退休期
                escalating_rate=0.02,         # 2%通胀率
                payments_per_year=12
            )
            
            payout_per_month = cpf_life_result['monthly_payout']
            total_payout = sum(cpf_life_result['monthly_schedule'])  # 使用CPF Life计算的总领取
        else:
            payout_per_month = 0
            total_payout = 0
        
        # 计算终值（90岁时的所有CPF账户余额）
        terminal_value = OA_remaining + MA  # SA已转入RA，RA已用于年金
        
        return {
            'RA_at_65': RA,
            'monthly_payout': payout_per_month,
            'total_payout': total_payout,
            'employee_contrib_total': employee_contrib_total,  # 雇员总缴费
            'OA_remaining': OA_remaining,
            'MA_remaining': MA,
            'terminal_value': terminal_value
        }

    def calculate_annual_contribution(self, monthly_salary: float, age: int) -> CPFContribution:
        """计算年度CPF缴费"""
        annual_salary = monthly_salary * 12
        base = min(annual_salary, 102000)  # 年薪上限
        
        # 计算总缴费
        total_contribution = base * 0.37
        total_contribution = min(total_contribution, 37740)  # 年缴费上限
        
        # 分配比例
        oa_contribution = total_contribution * 0.23 / 0.37
        sa_contribution = total_contribution * 0.06 / 0.37
        ma_contribution = total_contribution * 0.08 / 0.37
        
        # 员工和雇主缴费
        employee_contribution = total_contribution * 0.20 / 0.37
        employer_contribution = total_contribution * 0.17 / 0.37
        
        return CPFContribution(
            oa_contribution=oa_contribution,
            sa_contribution=sa_contribution,
            ra_contribution=0,  # 55岁前没有RA
            ma_contribution=ma_contribution,
            total_contribution=total_contribution,
            employee_contribution=employee_contribution,
            employer_contribution=employer_contribution
        )

    def get_contribution_rates(self, age: int) -> Dict[str, float]:
        """获取缴费比例"""
        return {
            'employee': 0.20,
            'employer': 0.17,
            'total': 0.37
        }

    def get_account_allocation_rates(self, age: int) -> Dict[str, float]:
        """获取账户分配比例"""
        return {
            'oa': 0.23,
            'sa': 0.06,
            'ma': 0.08
        }
    
    def calculate_irr_analysis(self, monthly_salary: float, start_age: int = 30, retirement_age: int = 65) -> Dict:
        """
        计算CPF的IRR分析 - 修正版
        
        Args:
            monthly_salary: 月薪
            start_age: 开始工作年龄
            retirement_age: 退休年龄
            
        Returns:
            包含IRR和详细分析的字典
        """
        # 使用新的IRR计算器
        irr_result = IRRCalculator.calculate_cpf_irr(
            monthly_salary=monthly_salary,
            start_age=start_age,
            retirement_age=retirement_age,
            terminal_age=90,
            frequency='annual'
        )
        
        # 获取传统模型结果用于对比
        traditional_result = self._cpf_model(monthly_salary * 12, start_age, retirement_age - start_age)
        
        return {
            'irr_value': irr_result['irr'],
            'irr_percentage': irr_result['analysis']['irr_percentage'],
            'npv_value': irr_result['npv'],
            'cash_flows': irr_result['cash_flows'],
            'cash_flow_details': irr_result['cash_flow_details'],
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