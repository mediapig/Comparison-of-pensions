#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IRR计算器 - 修正版
正确处理现金流方向和终值
"""

import numpy as np
from typing import List, Dict, Any, Optional
from numpy_financial import irr, npv


class IRRCalculator:
    """IRR计算器 - 修正版"""
    
    @staticmethod
    def calculate_irr(cash_flows: List[float], guess: float = 0.1) -> Optional[float]:
        """
        计算内部收益率 (IRR)
        
        Args:
            cash_flows: 现金流列表，负值表示流出，正值表示流入
            guess: 初始猜测值
            
        Returns:
            IRR值，如果无法计算则返回None
        """
        try:
            # 使用numpy_financial的irr函数
            irr_value = irr(cash_flows)
            return irr_value if not np.isnan(irr_value) else None
        except (ValueError, np.linalg.LinAlgError):
            return None
    
    @staticmethod
    def calculate_npv(cash_flows: List[float], 
                     discount_rate: float) -> float:
        """
        计算净现值 (NPV)
        
        Args:
            cash_flows: 现金流列表
            discount_rate: 贴现率
            
        Returns:
            NPV值
        """
        return npv(discount_rate, cash_flows)
    
    @staticmethod
    def build_cpf_cash_flows(monthly_salary: float,
                           start_age: int,
                           retirement_age: int,
                           terminal_age: int = 90,
                           frequency: str = 'annual') -> Dict[str, Any]:
        """
        构建CPF现金流序列
        
        Args:
            monthly_salary: 月薪
            start_age: 开始工作年龄
            retirement_age: 退休年龄
            terminal_age: 终值年龄（默认90岁）
            frequency: 现金流频率 ('annual' 或 'monthly')
            
        Returns:
            包含现金流和详细信息的字典
        """
        annual_salary = monthly_salary * 12
        work_years = retirement_age - start_age
        retirement_years = terminal_age - retirement_age
        
        if frequency == 'annual':
            # 年度现金流
            cash_flows = []
            cash_flow_details = []
            
            # 工作期：每年雇员缴费（负现金流）
            for year in range(work_years):
                age = start_age + year
                base = min(annual_salary, 102000)  # 年薪上限
                employee_contrib = base * 0.20  # 雇员缴费20%
                cash_flows.append(-employee_contrib)  # 负现金流
                cash_flow_details.append({
                    'age': age,
                    'period': year + 1,
                    'cash_flow': -employee_contrib,
                    'type': 'employee_contribution',
                    'description': f'雇员缴费 (年龄{age})'
                })
            
            # 退休期：每年领取（正现金流）
            # 首先计算RA余额和月领取额
            ra_balance = IRRCalculator._calculate_ra_balance(annual_salary, start_age, retirement_age)
            monthly_payout = ra_balance / 180  # 15年领取期
            annual_payout = monthly_payout * 12
            
            for year in range(retirement_years):
                age = retirement_age + year
                cash_flows.append(annual_payout)  # 正现金流
                cash_flow_details.append({
                    'age': age,
                    'period': work_years + year + 1,
                    'cash_flow': annual_payout,
                    'type': 'retirement_payout',
                    'description': f'退休金领取 (年龄{age})'
                })
            
            # 终值：90岁时的剩余余额（正现金流）
            terminal_value = IRRCalculator._calculate_terminal_value(annual_salary, start_age, retirement_age, terminal_age)
            cash_flows.append(terminal_value)  # 正现金流
            cash_flow_details.append({
                'age': terminal_age,
                'period': work_years + retirement_years + 1,
                'cash_flow': terminal_value,
                'type': 'terminal_value',
                'description': f'终值 (年龄{terminal_age})'
            })
            
        else:  # monthly
            # 月度现金流
            cash_flows = []
            cash_flow_details = []
            
            # 工作期：每月雇员缴费
            for month in range(work_years * 12):
                age_months = start_age * 12 + month
                age = age_months // 12
                base = min(annual_salary, 102000)
                monthly_employee_contrib = base * 0.20 / 12
                cash_flows.append(-monthly_employee_contrib)
                cash_flow_details.append({
                    'age': age,
                    'month': month % 12 + 1,
                    'period': month + 1,
                    'cash_flow': -monthly_employee_contrib,
                    'type': 'employee_contribution',
                    'description': f'雇员缴费 (年龄{age}第{month % 12 + 1}月)'
                })
            
            # 退休期：每月领取
            ra_balance = IRRCalculator._calculate_ra_balance(annual_salary, start_age, retirement_age)
            monthly_payout = ra_balance / 180
            
            for month in range(retirement_years * 12):
                age_months = retirement_age * 12 + month
                age = age_months // 12
                cash_flows.append(monthly_payout)
                cash_flow_details.append({
                    'age': age,
                    'month': month % 12 + 1,
                    'period': work_years * 12 + month + 1,
                    'cash_flow': monthly_payout,
                    'type': 'retirement_payout',
                    'description': f'退休金领取 (年龄{age}第{month % 12 + 1}月)'
                })
            
            # 终值
            terminal_value = IRRCalculator._calculate_terminal_value(annual_salary, start_age, retirement_age, terminal_age)
            cash_flows.append(terminal_value)
            cash_flow_details.append({
                'age': terminal_age,
                'month': 12,
                'period': work_years * 12 + retirement_years * 12 + 1,
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
                'total_employee_contributions': sum([cf for cf in cash_flows if cf < 0]),
                'total_retirement_payouts': sum([cf for cf in cash_flows if cf > 0 and cf != terminal_value]),
                'terminal_value': terminal_value,
                'net_cash_flow': sum(cash_flows)
            }
        }
    
    @staticmethod
    def _calculate_ra_balance(annual_salary: float, start_age: int, retirement_age: int) -> float:
        """计算65岁时的RA余额"""
        work_years = retirement_age - start_age
        OA = 0
        SA = 0
        MA = 0
        
        # 工作期缴费累积
        for age in range(start_age, retirement_age):
            base = min(annual_salary, 102000)
            OA += base * 0.23
            SA += base * 0.06
            MA += base * 0.08
        
        # 55岁时转入RA
        if retirement_age >= 55:
            RA = SA + OA * 0.5  # SA全部转入，OA一半转入
            OA_remaining = OA * 0.5
            
            # 55-65岁利息累积
            for i in range(10):
                RA *= 1.04
                OA_remaining *= 1.025
                MA *= 1.04
        else:
            RA = SA + OA * 0.5
            OA_remaining = OA * 0.5
        
        return RA
    
    @staticmethod
    def _calculate_terminal_value(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> float:
        """计算终值（90岁时的剩余余额）"""
        terminal_accounts = IRRCalculator._calculate_terminal_accounts(annual_salary, start_age, retirement_age, terminal_age)
        return terminal_accounts['total']
    
    @staticmethod
    def _calculate_terminal_accounts(annual_salary: float, start_age: int, retirement_age: int, terminal_age: int) -> Dict[str, float]:
        """计算90岁时各账户的详细余额"""
        work_years = retirement_age - start_age
        OA = 0
        SA = 0
        MA = 0
        
        # 工作期缴费累积
        for age in range(start_age, retirement_age):
            base = min(annual_salary, 102000)
            OA += base * 0.23
            SA += base * 0.06
            MA += base * 0.08
        
        # 55岁时转入RA
        if retirement_age >= 55:
            RA = SA + OA * 0.5
            OA_remaining = OA * 0.5
            
            # 55-65岁利息累积
            for i in range(10):
                RA *= 1.04
                OA_remaining *= 1.025
                MA *= 1.04
            
            # 65-90岁：RA用于年金，OA和MA继续累积利息
            for i in range(terminal_age - retirement_age):
                OA_remaining *= 1.025
                MA *= 1.04
        else:
            OA_remaining = OA * 0.5
            MA = MA
        
        return {
            'OA': OA_remaining,
            'SA': 0,  # SA已转入RA
            'MA': MA,
            'RA': 0,  # RA已用于年金
            'total': OA_remaining + MA
        }
    
    @staticmethod
    def calculate_cpf_irr(monthly_salary: float,
                         start_age: int = 30,
                         retirement_age: int = 65,
                         terminal_age: int = 90,
                         frequency: str = 'annual') -> Dict[str, Any]:
        """
        计算CPF的IRR
        
        Args:
            monthly_salary: 月薪
            start_age: 开始工作年龄
            retirement_age: 退休年龄
            terminal_age: 终值年龄
            frequency: 现金流频率
            
        Returns:
            包含IRR和详细分析的字典
        """
        # 构建现金流
        cash_flow_data = IRRCalculator.build_cpf_cash_flows(
            monthly_salary, start_age, retirement_age, terminal_age, frequency
        )
        
        cash_flows = cash_flow_data['cash_flows']
        
        # 计算IRR
        irr_value = IRRCalculator.calculate_irr(cash_flows)
        
        # 计算NPV（使用IRR作为贴现率）
        npv_value = IRRCalculator.calculate_npv(cash_flows, irr_value) if irr_value else 0
        
        # 计算其他指标
        total_employee_contrib = abs(sum([cf for cf in cash_flows if cf < 0]))
        total_benefits = sum([cf for cf in cash_flows if cf > 0])
        net_benefit = total_benefits - total_employee_contrib
        
        # 计算90岁时各账户余额
        annual_salary = monthly_salary * 12
        terminal_accounts = IRRCalculator._calculate_terminal_accounts(annual_salary, start_age, retirement_age, terminal_age)
        
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
                'payback_period_years': None  # 可以后续计算
            }
        }