#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF计算器
基于2024-2025年最新CPF政策
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass


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
    """新加坡CPF计算器"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'
        
        # 2025年CPF参数
        self.ow_ceiling = 7400        # 月薪上限
        self.annual_limit = 37740     # 年度缴费上限
        self.bhs = 75500             # 基本医疗储蓄上限
        self.frs = 198800           # 全额退休储蓄（2024年）

    def rate_by_age(self, age: int) -> float:
        """根据年龄获取CPF总缴费率"""
        if age <= 35:
            return 0.37  # 员工20% + 雇主17%
        elif age <= 45:
            return 0.37  # 员工20% + 雇主17%
        elif age <= 50:
            return 0.37  # 员工20% + 雇主17%
        elif age <= 55:
            return 0.37  # 员工20% + 雇主17%
        elif age <= 60:
            return 0.26  # 员工13% + 雇主13%
        elif age <= 65:
            return 0.165 # 员工7.5% + 雇主9%
        else:
            return 0.125 # 员工5% + 雇主7.5%

    def ratio_by_age(self, age: int) -> Tuple[float, float, float]:
        """根据年龄获取CPF账户分配比例 (OA, SA/RA, MA)"""
        if age <= 35:
            return (0.6216, 0.1622, 0.2162)  # OA: 62.16%, SA: 16.22%, MA: 21.62%
        elif age <= 45:
            return (0.6216, 0.1622, 0.2162)  # OA: 62.16%, SA: 16.22%, MA: 21.62%
        elif age <= 50:
            return (0.5676, 0.2162, 0.2162)  # OA: 56.76%, SA: 21.62%, MA: 21.62%
        elif age <= 55:
            return (0.5135, 0.2703, 0.2162)  # OA: 51.35%, SA: 27.03%, MA: 21.62%
        elif age <= 60:
            return (0.4615, 0.3077, 0.2308)  # OA: 46.15%, RA: 30.77%, MA: 23.08%
        elif age <= 65:
            return (0.4545, 0.3030, 0.2424)  # OA: 45.45%, RA: 30.30%, MA: 24.24%
        else:
            return (0.4000, 0.4000, 0.2000)  # OA: 40%, RA: 40%, MA: 20%

    def calculate_cpf_split(self, 
                          month_salary: float, 
                          age: int, 
                          balances: CPFAccountBalances = None) -> CPFContribution:
        """
        计算CPF账户分配
        
        Args:
            month_salary: 月薪
            age: 年龄
            balances: CPF账户余额
            
        Returns:
            CPF缴费结果
        """
        if balances is None:
            balances = CPFAccountBalances()

        # 1) 基数：本月 OW 计费额
        ow_base = min(month_salary, self.ow_ceiling)
        
        # 2) 年龄段总费率
        total_rate = self.rate_by_age(age)
        cpf_due_this_month = ow_base * total_rate
        
        # 计算员工和雇主缴费
        if age <= 60:
            employee_rate = 0.20 if age <= 55 else 0.13
            employer_rate = total_rate - employee_rate
        else:
            employee_rate = 0.075 if age <= 65 else 0.05
            employer_rate = total_rate - employee_rate
            
        employee_contribution = ow_base * employee_rate
        employer_contribution = ow_base * employer_rate

        # 3) 账户比例
        share_OA, share_SA_or_RA, share_MA = self.ratio_by_age(age)

        # 4) 先分 MA（受 BHS）
        to_MA = cpf_due_this_month * share_MA
        room_MA = max(0, self.bhs - balances.ma_balance)
        put_MA = min(to_MA, room_MA)
        overflow_from_MA = to_MA - put_MA

        # 5) SA/RA 分配（≥55 用 RA，且受 FRS）
        to_SAR = cpf_due_this_month * share_SA_or_RA + overflow_from_MA
        if age >= 55:
            room_RA = max(0, self.frs - balances.ra_balance)
            put_RA = min(to_SAR, room_RA)
            overflow_from_SAR = to_SAR - put_RA
            put_SA = 0
        else:
            put_SA = to_SAR
            overflow_from_SAR = 0
            put_RA = 0

        # 6) OA 分配 = OA 份额 + 上述溢出
        put_OA = cpf_due_this_month * share_OA + overflow_from_SAR

        return CPFContribution(
            oa_contribution=round(put_OA, 2),
            sa_contribution=round(put_SA, 2),
            ra_contribution=round(put_RA, 2),
            ma_contribution=round(put_MA, 2),
            total_contribution=round(put_OA + put_SA + put_RA + put_MA, 2),
            employee_contribution=round(employee_contribution, 2),
            employer_contribution=round(employer_contribution, 2)
        )

    def calculate_annual_cpf(self, 
                           monthly_salary: float, 
                           age: int, 
                           work_years: int = 1,
                           initial_balances: CPFAccountBalances = None) -> Dict:
        """
        计算年度CPF缴费
        
        Args:
            monthly_salary: 月薪
            age: 年龄
            work_years: 工作年限
            initial_balances: 初始CPF账户余额
            
        Returns:
            年度CPF计算结果
        """
        if initial_balances is None:
            initial_balances = CPFAccountBalances()

        # 计算年度缴费
        annual_oa = 0
        annual_sa = 0
        annual_ra = 0
        annual_ma = 0
        annual_employee = 0
        annual_employer = 0

        current_balances = CPFAccountBalances(
            oa_balance=initial_balances.oa_balance,
            sa_balance=initial_balances.sa_balance,
            ra_balance=initial_balances.ra_balance,
            ma_balance=initial_balances.ma_balance
        )

        monthly_contributions = []
        
        for month in range(12):
            contribution = self.calculate_cpf_split(monthly_salary, age, current_balances)
            
            # 更新账户余额
            current_balances.oa_balance += contribution.oa_contribution
            current_balances.sa_balance += contribution.sa_contribution
            current_balances.ra_balance += contribution.ra_contribution
            current_balances.ma_balance += contribution.ma_contribution
            
            # 累加年度数据
            annual_oa += contribution.oa_contribution
            annual_sa += contribution.sa_contribution
            annual_ra += contribution.ra_contribution
            annual_ma += contribution.ma_contribution
            annual_employee += contribution.employee_contribution
            annual_employer += contribution.employer_contribution
            
            monthly_contributions.append({
                'month': month + 1,
                'oa': contribution.oa_contribution,
                'sa': contribution.sa_contribution,
                'ra': contribution.ra_contribution,
                'ma': contribution.ma_contribution,
                'total': contribution.total_contribution,
                'employee': contribution.employee_contribution,
                'employer': contribution.employer_contribution
            })

        return {
            'annual_oa': annual_oa,
            'annual_sa': annual_sa,
            'annual_ra': annual_ra,
            'annual_ma': annual_ma,
            'annual_employee': annual_employee,
            'annual_employer': annual_employer,
            'annual_total': annual_oa + annual_sa + annual_ra + annual_ma,
            'monthly_contributions': monthly_contributions,
            'final_balances': {
                'oa_balance': current_balances.oa_balance,
                'sa_balance': current_balances.sa_balance,
                'ra_balance': current_balances.ra_balance,
                'ma_balance': current_balances.ma_balance
            }
        }

    def calculate_lifetime_cpf(self, 
                              monthly_salary: float, 
                              start_age: int, 
                              retirement_age: int,
                              initial_balances: CPFAccountBalances = None) -> Dict:
        """
        计算终身CPF缴费
        
        Args:
            monthly_salary: 月薪
            start_age: 开始工作年龄
            retirement_age: 退休年龄
            initial_balances: 初始CPF账户余额
            
        Returns:
            终身CPF计算结果
        """
        if initial_balances is None:
            initial_balances = CPFAccountBalances()

        work_years = retirement_age - start_age
        total_oa = 0
        total_sa = 0
        total_ra = 0
        total_ma = 0
        total_employee = 0
        total_employer = 0

        current_balances = CPFAccountBalances(
            oa_balance=initial_balances.oa_balance,
            sa_balance=initial_balances.sa_balance,
            ra_balance=initial_balances.ra_balance,
            ma_balance=initial_balances.ma_balance
        )

        yearly_data = []
        
        for year in range(work_years):
            current_age = start_age + year
            annual_result = self.calculate_annual_cpf(
                monthly_salary, current_age, 1, current_balances
            )
            
            # 更新余额
            current_balances.oa_balance = annual_result['final_balances']['oa_balance']
            current_balances.sa_balance = annual_result['final_balances']['sa_balance']
            current_balances.ra_balance = annual_result['final_balances']['ra_balance']
            current_balances.ma_balance = annual_result['final_balances']['ma_balance']
            
            # 累加数据
            total_oa += annual_result['annual_oa']
            total_sa += annual_result['annual_sa']
            total_ra += annual_result['annual_ra']
            total_ma += annual_result['annual_ma']
            total_employee += annual_result['annual_employee']
            total_employer += annual_result['annual_employer']
            
            yearly_data.append({
                'age': current_age,
                'year': year + 1,
                'oa': annual_result['annual_oa'],
                'sa': annual_result['annual_sa'],
                'ra': annual_result['annual_ra'],
                'ma': annual_result['annual_ma'],
                'total': annual_result['annual_total'],
                'employee': annual_result['annual_employee'],
                'employer': annual_result['annual_employer'],
                'balances': annual_result['final_balances'].copy()
            })

        return {
            'total_oa': total_oa,
            'total_sa': total_sa,
            'total_ra': total_ra,
            'total_ma': total_ma,
            'total_employee': total_employee,
            'total_employer': total_employee + total_employer,
            'total_lifetime': total_oa + total_sa + total_ra + total_ma,
            'yearly_data': yearly_data,
            'final_balances': {
                'oa_balance': current_balances.oa_balance,
                'sa_balance': current_balances.sa_balance,
                'ra_balance': current_balances.ra_balance,
                'ma_balance': current_balances.ma_balance
            }
        }

    def get_cpf_info(self, age: int) -> Dict:
        """获取CPF信息"""
        total_rate = self.rate_by_age(age)
        share_OA, share_SA_or_RA, share_MA = self.ratio_by_age(age)
        
        if age <= 60:
            employee_rate = 0.20 if age <= 55 else 0.13
            employer_rate = total_rate - employee_rate
        else:
            employee_rate = 0.075 if age <= 65 else 0.05
            employer_rate = total_rate - employee_rate

        return {
            'age': age,
            'total_rate': total_rate,
            'employee_rate': employee_rate,
            'employer_rate': employer_rate,
            'oa_ratio': share_OA,
            'sa_ra_ratio': share_SA_or_RA,
            'ma_ratio': share_MA,
            'ow_ceiling': self.ow_ceiling,
            'annual_limit': self.annual_limit,
            'bhs': self.bhs,
            'frs': self.frs
        }