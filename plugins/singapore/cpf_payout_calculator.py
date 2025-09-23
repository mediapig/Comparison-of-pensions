#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF领取计算器
基于CPF Life等退休金领取方案
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CPFPayoutResult:
    """CPF领取结果"""
    monthly_payment: float          # 月领取金额
    total_payments: float          # 总领取金额
    total_interest: float          # 总利息收入
    payout_years: int              # 领取年限
    final_balance: float           # 最终余额
    payout_schedule: List[Dict]    # 领取计划明细


class SingaporeCPFPayoutCalculator:
    """新加坡CPF领取计算器"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

    def compute_payout_schedule(self,
                              principal: float,
                              annual_nominal_rate: float,
                              annual_inflation_rate: float,
                              years: int = 30,
                              freq: int = 12,
                              scheme: str = "level",
                              rounding: bool = True) -> List[Dict]:
        """
        计算CPF领取计划
        
        Args:
            principal: 本金（退休时CPF余额）
            annual_nominal_rate: 年名义利率
            annual_inflation_rate: 年通胀率
            years: 领取年限
            freq: 支付频率（月=12）
            scheme: 领取方案 ("level" 或 "growing")
            rounding: 是否四舍五入到分
            
        Returns:
            领取计划明细列表
        """
        r = annual_nominal_rate / freq          # 月利率
        g = annual_inflation_rate / freq        # 月增长率（用于 growing）
        n = years * freq                        # 总期数（月份）

        # 1) 计算每月支付额（首月，如果是 growing 则为首月金额）
        if scheme == "level":
            if r == 0:
                monthly_payment = principal / n
            else:
                monthly_payment = principal * (r / (1 - (1 + r) ** (-n)))

        elif scheme == "growing":
            # 要求 r != g，若非常接近需要用极限近似
            if abs(r - g) < 1e-12:
                # 当 r ≈ g 时，PMT0 ≈ PV / n（近似）
                monthly_payment = principal / n
            else:
                monthly_payment = principal * ((r - g) / (1 - ((1 + g) / (1 + r)) ** n))
        else:
            raise ValueError("scheme must be 'level' or 'growing'")

        # 可选四舍五入到分
        def round_money(x):
            return round(x + 1e-12, 2) if rounding else x

        monthly_payment = round_money(monthly_payment)

        # 2) 模拟逐月发放（带利息复利）
        balance = principal
        schedule = []
        for m in range(1, n + 1):
            # 计算当月利息
            interest = balance * r

            # 本期支付额
            if scheme == "level":
                payment = monthly_payment
            else:  # growing
                # 如果要按月增长：payment_m = monthly_payment * (1+g)^(m-1)
                payment = monthly_payment * ((1 + g) ** (m - 1))

            # 防止最后一期超额提现：如果 payment > balance + interest，则把 payment 调整为全部余额
            if payment > balance + interest:
                payment = balance + interest

            # 更新余额：先加利息，再减去本期支付
            balance = balance + interest - payment

            # 四舍五入显示
            interest_r = round_money(interest)
            payment_r = round_money(payment)
            balance_r = round_money(balance)

            schedule.append({
                "month": m,
                "payment": payment_r,
                "interest": interest_r,
                "balance_after": balance_r
            })

            # 若余额接近 0，跳出循环
            if balance <= 1e-6:
                break

        return schedule

    def calculate_cpf_life_payout(self,
                                ra_balance: float,
                                sa_balance: float = 0,
                                annual_nominal_rate: float = 0.04,
                                annual_inflation_rate: float = 0.02,
                                payout_years: int = 30,
                                scheme: str = "level") -> CPFPayoutResult:
        """
        计算CPF Life退休金领取
        
        Args:
            ra_balance: RA账户余额
            sa_balance: SA账户余额（如果有）
            annual_nominal_rate: 年名义利率
            annual_inflation_rate: 年通胀率
            payout_years: 领取年限
            scheme: 领取方案
            
        Returns:
            CPF领取结果
        """
        # 合并RA和SA余额作为本金
        total_principal = ra_balance + sa_balance
        
        if total_principal <= 0:
            return CPFPayoutResult(
                monthly_payment=0,
                total_payments=0,
                total_interest=0,
                payout_years=payout_years,
                final_balance=0,
                payout_schedule=[]
            )

        # 计算领取计划
        schedule = self.compute_payout_schedule(
            principal=total_principal,
            annual_nominal_rate=annual_nominal_rate,
            annual_inflation_rate=annual_inflation_rate,
            years=payout_years,
            scheme=scheme
        )

        # 计算汇总数据
        total_payments = sum(item['payment'] for item in schedule)
        total_interest = sum(item['interest'] for item in schedule)
        final_balance = schedule[-1]['balance_after'] if schedule else 0
        monthly_payment = schedule[0]['payment'] if schedule else 0

        return CPFPayoutResult(
            monthly_payment=monthly_payment,
            total_payments=total_payments,
            total_interest=total_interest,
            payout_years=payout_years,
            final_balance=final_balance,
            payout_schedule=scheme
        )

    def calculate_enhanced_retirement_summary(self,
                                            ra_balance: float,
                                            sa_balance: float = 0,
                                            oa_balance: float = 0,
                                            ma_balance: float = 0) -> Dict:
        """
        计算增强版退休金汇总
        
        Args:
            ra_balance: RA账户余额
            sa_balance: SA账户余额
            oa_balance: OA账户余额
            ma_balance: MA账户余额
            
        Returns:
            退休金汇总信息
        """
        total_cpf_balance = ra_balance + sa_balance + oa_balance + ma_balance
        
        # 计算不同方案的月退休金
        level_payout = self.calculate_cpf_life_payout(
            ra_balance, sa_balance, scheme="level"
        )
        
        growing_payout = self.calculate_cpf_life_payout(
            ra_balance, sa_balance, scheme="growing"
        )

        return {
            'total_cpf_balance': total_cpf_balance,
            'account_breakdown': {
                'ra_balance': ra_balance,
                'sa_balance': sa_balance,
                'oa_balance': oa_balance,
                'ma_balance': ma_balance
            },
            'retirement_income': {
                'level_monthly': level_payout.monthly_payment,
                'level_total': level_payout.total_payments,
                'growing_monthly': growing_payout.monthly_payment,
                'growing_total': growing_payout.total_payments
            },
            'payout_options': {
                'level_scheme': {
                    'monthly_payment': level_payout.monthly_payment,
                    'total_payments': level_payout.total_payments,
                    'total_interest': level_payout.total_interest,
                    'payout_years': level_payout.payout_years
                },
                'growing_scheme': {
                    'monthly_payment': growing_payout.monthly_payment,
                    'total_payments': growing_payout.total_payments,
                    'total_interest': growing_payout.total_interest,
                    'payout_years': growing_payout.payout_years
                }
            }
        }

    def get_cpf_life_info(self) -> Dict:
        """获取CPF Life信息"""
        return {
            'scheme_types': ['level', 'growing'],
            'default_nominal_rate': 0.04,  # 4%年利率
            'default_inflation_rate': 0.02,  # 2%通胀率
            'default_payout_years': 30,
            'description': {
                'level': '固定金额领取：每月领取相同金额',
                'growing': '递增金额领取：每月金额按通胀率递增'
            }
        }