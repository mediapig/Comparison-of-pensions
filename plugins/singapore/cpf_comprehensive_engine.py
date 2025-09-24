#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF综合引擎 - 基于详细规格的完整实现
实现所有CPF规则：BHS管理、RA建立、CPF LIFE计算、IRR分析等
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
import math
import json
from datetime import datetime
import numpy as np


@dataclass
class CPFParameters:
    """CPF系统参数配置"""
    # 基础参数
    start_year: int = 2024
    start_age: int = 30
    retirement_age: int = 65
    end_age: int = 90
    
    # 薪资参数
    annual_salary: float = 180000
    salary_growth_rate: float = 0.02
    annual_cpf_ceiling: float = 102000
    
    # 利率参数
    oa_rate: float = 0.025  # OA年息2.5%
    sa_rate: float = 0.04   # SA年息4%
    ma_rate: float = 0.04   # MA年息4%
    ra_rate: float = 0.04   # RA年息4%
    
    # CPF LIFE参数
    premium_rate: float = 0.035  # 年金贴现率3.5%
    escalating_growth: float = 0.02  # Escalating计划年增长2%
    basic_premium_ratio: float = 0.15  # Basic计划年金池比例15%
    
    # RA目标参数
    ra_target_type: str = "FRS"  # "FRS", "ERS", "BRS", "CUSTOM"
    custom_ra_target: Optional[float] = None
    ers_multiplier: float = 2.0
    brs_multiplier: float = 0.5
    
    # 55岁处理参数
    withdraw_excess_oa: bool = False  # 是否提取超额OA
    
    # CPF LIFE计划
    cpf_life_plan: str = "standard"  # "standard", "escalating", "basic"
    
    # IRR计算参数
    use_personal_irr: bool = True  # True=个人IRR(仅雇员缴费), False=制度IRR(雇员+雇主)
    
    # 自定义函数
    bhs_function: Optional[Callable[[int], float]] = None
    frs_function: Optional[Callable[[int], float]] = None
    allocation_function: Optional[Callable[[int], Tuple[float, float, float]]] = None


@dataclass
class CPFAccountState:
    """CPF账户状态"""
    oa_balance: float = 0.0
    sa_balance: float = 0.0
    ma_balance: float = 0.0
    ra_balance: float = 0.0
    
    def total_balance(self) -> float:
        return self.oa_balance + self.sa_balance + self.ma_balance + self.ra_balance


@dataclass
class CPFYearResult:
    """年度CPF计算结果"""
    year: int
    age: int
    salary: float
    cpf_base: float
    employee_contrib: float
    employer_contrib: float
    total_contrib: float
    
    # 账户分配
    oa_allocation: float
    sa_allocation: float
    ma_allocation: float
    ma_overflow: float  # MA超额部分
    
    # 年终余额
    oa_balance: float
    sa_balance: float
    ma_balance: float
    ra_balance: float
    
    # BHS信息
    bhs_limit: float
    cohort_bhs_locked: bool = False


@dataclass
class CPFLifeResult:
    """CPF LIFE计算结果"""
    plan: str
    ra65_balance: float
    monthly_payouts: List[float]
    total_payout: float
    final_balance: float
    bequest_curve: List[float]
    
    # 分析指标
    payout_efficiency: float
    bequest_at_80: float
    bequest_at_90: float


@dataclass
class CPFComprehensiveResult:
    """CPF综合分析结果"""
    # 基础信息
    parameters: CPFParameters
    work_years: int
    retirement_years: int
    
    # 年度结果
    yearly_results: List[CPFYearResult]
    
    # 55岁RA建立
    ra_established_at_55: float
    oa_remaining_at_55: float
    sa_remaining_at_55: float
    cash_withdrawn_at_55: float
    
    # 65岁状态
    ra_balance_at_65: float
    oa_balance_at_65: float
    ma_balance_at_65: float
    
    # CPF LIFE结果
    cpf_life_result: CPFLifeResult
    
    # 财务分析
    total_employee_contributions: float
    total_employer_contributions: float
    total_contributions: float
    total_benefits: float
    terminal_value: float
    
    # IRR分析
    personal_irr: Optional[float]
    system_irr: Optional[float]
    npv_personal: Optional[float]
    npv_system: Optional[float]
    
    # 现金流
    monthly_cashflows: List[float]
    
    # 验证信息
    validation_passed: bool
    validation_errors: List[str]


class CPFComprehensiveEngine:
    """CPF综合计算引擎"""
    
    def __init__(self, parameters: Optional[CPFParameters] = None):
        self.params = parameters or CPFParameters()
        self._setup_default_functions()
    
    def _setup_default_functions(self):
        """设置默认函数"""
        if self.params.bhs_function is None:
            self.params.bhs_function = self._default_bhs_function
        
        if self.params.frs_function is None:
            self.params.frs_function = self._default_frs_function
        
        if self.params.allocation_function is None:
            self.params.allocation_function = self._default_allocation_function
    
    def _default_bhs_function(self, year: int) -> float:
        """默认BHS函数"""
        bhs_table = {
            2024: 71500,
            2025: 73500,
            2026: 75500,
            2027: 77500,
            2028: 79500,
            2029: 81500,
            2030: 83500,
        }
        
        if year in bhs_table:
            return bhs_table[year]
        
        # 线性外推
        if year > 2030:
            return bhs_table[2030] * (1.03 ** (year - 2030))
        elif year < 2024:
            return bhs_table[2024] * (0.97 ** (2024 - year))
        
        return bhs_table[2024]
    
    def _default_frs_function(self, year: int) -> float:
        """默认FRS函数"""
        frs_table = {
            2024: 205800,
            2025: 212000,
            2026: 218000,
            2027: 224000,
            2028: 230000,
            2029: 236000,
            2030: 242000,
        }
        
        if year in frs_table:
            return frs_table[year]
        
        # 线性外推
        if year > 2030:
            return frs_table[2030] * (1.03 ** (year - 2030))
        elif year < 2024:
            return frs_table[2024] * (0.97 ** (2024 - year))
        
        return frs_table[2024]
    
    def _default_allocation_function(self, age: int) -> Tuple[float, float, float]:
        """默认账户分配函数"""
        # 基于年龄的分配比例 (OA%, SA%, MA%)
        if age <= 35:
            return (0.23, 0.06, 0.08)
        elif age <= 45:
            return (0.23, 0.06, 0.08)
        elif age <= 50:
            return (0.23, 0.06, 0.08)
        elif age <= 55:
            return (0.23, 0.06, 0.08)
        elif age <= 60:
            return (0.23, 0.06, 0.08)
        elif age <= 65:
            return (0.23, 0.06, 0.08)
        else:
            return (0.23, 0.06, 0.08)
    
    def _get_cpf_rates(self, age: int) -> Tuple[float, float]:
        """获取CPF缴费比例"""
        if age <= 35:
            return (0.20, 0.17)
        elif age <= 45:
            return (0.20, 0.17)
        elif age <= 50:
            return (0.20, 0.17)
        elif age <= 55:
            return (0.20, 0.17)
        elif age <= 60:
            return (0.20, 0.17)
        elif age <= 65:
            return (0.20, 0.17)
        else:
            return (0.075, 0.075)
    
    def _calculate_bhs_limit(self, age: int, year: int) -> Tuple[float, bool]:
        """计算BHS限制"""
        if age < 65:
            # 65岁前使用当年BHS
            return self.params.bhs_function(year), False
        else:
            # 65岁及以后使用cohort BHS（锁定值）
            cohort_year = self.params.start_year + (65 - self.params.start_age)
            return self.params.bhs_function(cohort_year), True
    
    def _process_ma_overflow(self, ma_balance: float, bhs_limit: float, age: int) -> Tuple[float, float]:
        """处理MA超额"""
        if ma_balance <= bhs_limit + 1e-6:
            return ma_balance, 0.0
        
        overflow = ma_balance - bhs_limit
        return bhs_limit, overflow
    
    def _allocate_contributions(self, age: int, year: int, salary: float, 
                              accounts: CPFAccountState) -> CPFYearResult:
        """分配年度缴费"""
        # 计算缴费基数
        cpf_base = min(salary, self.params.annual_cpf_ceiling)
        
        # 获取缴费比例
        emp_rate, empr_rate = self._get_cpf_rates(age)
        employee_contrib = cpf_base * emp_rate
        employer_contrib = cpf_base * empr_rate
        total_contrib = employee_contrib + employer_contrib
        
        # 获取账户分配比例
        oa_pct, sa_pct, ma_pct = self.params.allocation_function(age)
        
        # 计算分配金额
        oa_allocation = cpf_base * oa_pct
        sa_allocation = cpf_base * sa_pct
        ma_allocation = cpf_base * ma_pct
        
        # 处理MA超额
        bhs_limit, cohort_locked = self._calculate_bhs_limit(age, year)
        ma_room = max(0.0, bhs_limit - accounts.ma_balance)
        ma_actual_allocation = min(ma_allocation, ma_room)
        ma_overflow = ma_allocation - ma_actual_allocation
        
        # 更新账户余额
        accounts.oa_balance += oa_allocation
        accounts.sa_balance += sa_allocation
        accounts.ma_balance += ma_actual_allocation
        
        # 处理MA超额：<55岁转到SA，≥55岁转到RA
        if ma_overflow > 0:
            if age < 55:
                accounts.sa_balance += ma_overflow
            else:
                accounts.ra_balance += ma_overflow
        
        # 年终计息
        accounts.oa_balance *= (1 + self.params.oa_rate)
        accounts.sa_balance *= (1 + self.params.sa_rate)
        accounts.ma_balance *= (1 + self.params.ma_rate)
        accounts.ra_balance *= (1 + self.params.ra_rate)
        
        # 检查MA是否因利息超过BHS上限
        ma_balance_after_interest, ma_interest_overflow = self._process_ma_overflow(
            accounts.ma_balance, bhs_limit, age
        )
        accounts.ma_balance = ma_balance_after_interest
        
        if ma_interest_overflow > 0:
            if age < 55:
                accounts.sa_balance += ma_interest_overflow
            else:
                accounts.ra_balance += ma_interest_overflow
        
        return CPFYearResult(
            year=year,
            age=age,
            salary=salary,
            cpf_base=cpf_base,
            employee_contrib=employee_contrib,
            employer_contrib=employer_contrib,
            total_contrib=total_contrib,
            oa_allocation=oa_allocation,
            sa_allocation=sa_allocation,
            ma_allocation=ma_actual_allocation,
            ma_overflow=ma_overflow + ma_interest_overflow,
            oa_balance=accounts.oa_balance,
            sa_balance=accounts.sa_balance,
            ma_balance=accounts.ma_balance,
            ra_balance=accounts.ra_balance,
            bhs_limit=bhs_limit,
            cohort_bhs_locked=cohort_locked
        )
    
    def _establish_ra_at_55(self, accounts: CPFAccountState, year: int) -> Tuple[float, float, float, float]:
        """55岁建立RA"""
        # 计算RA目标金额
        if self.params.ra_target_type == "FRS":
            ra_target = self.params.frs_function(year)
        elif self.params.ra_target_type == "ERS":
            ra_target = self.params.frs_function(year) * self.params.ers_multiplier
        elif self.params.ra_target_type == "BRS":
            ra_target = self.params.frs_function(year) * self.params.brs_multiplier
        elif self.params.ra_target_type == "CUSTOM":
            ra_target = self.params.custom_ra_target or self.params.frs_function(year)
        else:
            ra_target = self.params.frs_function(year)
        
        # 先转移SA到RA
        sa_to_ra = min(accounts.sa_balance, ra_target)
        accounts.ra_balance += sa_to_ra
        accounts.sa_balance -= sa_to_ra
        
        # 如果RA目标未达到，从OA转移
        remaining_target = ra_target - accounts.ra_balance
        if remaining_target > 0:
            oa_to_ra = min(accounts.oa_balance, remaining_target)
            accounts.ra_balance += oa_to_ra
            accounts.oa_balance -= oa_to_ra
        
        # 处理超额OA
        cash_withdrawn = 0.0
        if self.params.withdraw_excess_oa and accounts.oa_balance > 1e-6:
            cash_withdrawn = accounts.oa_balance
            accounts.oa_balance = 0.0
        
        return accounts.ra_balance, accounts.oa_balance, accounts.sa_balance, cash_withdrawn
    
    def _calculate_cpf_life(self, ra65_balance: float) -> CPFLifeResult:
        """计算CPF LIFE"""
        months = (self.params.end_age - self.params.retirement_age) * 12
        
        if self.params.cpf_life_plan == "standard":
            return self._calculate_standard_plan(ra65_balance, months)
        elif self.params.cpf_life_plan == "escalating":
            return self._calculate_escalating_plan(ra65_balance, months)
        elif self.params.cpf_life_plan == "basic":
            return self._calculate_basic_plan(ra65_balance, months)
        else:
            raise ValueError(f"Unknown CPF LIFE plan: {self.params.cpf_life_plan}")
    
    def _calculate_standard_plan(self, ra65_balance: float, months: int) -> CPFLifeResult:
        """计算Standard计划"""
        premium = ra65_balance
        monthly_rate = self.params.premium_rate / 12
        
        # 计算月支付额
        if abs(monthly_rate) < 1e-12:
            monthly_payout = premium / months
        else:
            monthly_payout = premium * (monthly_rate / (1 - (1 + monthly_rate) ** (-months)))
        
        # 计算月度现金流
        monthly_payouts = []
        bequest_curve = []
        current_premium = premium
        
        for month in range(months):
            # 年金池计息
            current_premium *= (1 + monthly_rate)
            
            # 支付
            payout = min(monthly_payout, current_premium)
            current_premium -= payout
            
            monthly_payouts.append(payout)
            bequest_curve.append(max(0.0, current_premium))
        
        total_payout = sum(monthly_payouts)
        final_balance = bequest_curve[-1] if bequest_curve else 0.0
        
        return CPFLifeResult(
            plan="standard",
            ra65_balance=ra65_balance,
            monthly_payouts=monthly_payouts,
            total_payout=total_payout,
            final_balance=final_balance,
            bequest_curve=bequest_curve,
            payout_efficiency=total_payout / ra65_balance if ra65_balance > 0 else 0,
            bequest_at_80=self._get_bequest_at_age(bequest_curve, 80),
            bequest_at_90=self._get_bequest_at_age(bequest_curve, 90)
        )
    
    def _calculate_escalating_plan(self, ra65_balance: float, months: int) -> CPFLifeResult:
        """计算Escalating计划"""
        premium = ra65_balance
        monthly_rate = self.params.premium_rate / 12
        monthly_growth = self.params.escalating_growth / 12
        
        # 计算首月支付额
        if abs(monthly_rate - monthly_growth) < 1e-12:
            monthly_payout = premium / months
        else:
            monthly_payout = premium * ((monthly_rate - monthly_growth) / 
                                       (1 - ((1 + monthly_growth) / (1 + monthly_rate)) ** months))
        
        # 计算月度现金流
        monthly_payouts = []
        bequest_curve = []
        current_premium = premium
        
        for month in range(months):
            # 年金池计息
            current_premium *= (1 + monthly_rate)
            
            # 支付（考虑增长）
            year_index = month // 12
            payout = monthly_payout * ((1 + self.params.escalating_growth) ** year_index)
            payout = min(payout, current_premium)
            current_premium -= payout
            
            monthly_payouts.append(payout)
            bequest_curve.append(max(0.0, current_premium))
        
        total_payout = sum(monthly_payouts)
        final_balance = bequest_curve[-1] if bequest_curve else 0.0
        
        return CPFLifeResult(
            plan="escalating",
            ra65_balance=ra65_balance,
            monthly_payouts=monthly_payouts,
            total_payout=total_payout,
            final_balance=final_balance,
            bequest_curve=bequest_curve,
            payout_efficiency=total_payout / ra65_balance if ra65_balance > 0 else 0,
            bequest_at_80=self._get_bequest_at_age(bequest_curve, 80),
            bequest_at_90=self._get_bequest_at_age(bequest_curve, 90)
        )
    
    def _calculate_basic_plan(self, ra65_balance: float, months: int) -> CPFLifeResult:
        """计算Basic计划"""
        premium = ra65_balance * self.params.basic_premium_ratio
        ra_remaining = ra65_balance - premium
        
        monthly_rate = self.params.premium_rate / 12
        ra_rate = self.params.ra_rate / 12
        
        # 第一阶段：从RA支付（到90岁）
        phase1_months = min(months, (90 - self.params.retirement_age) * 12)
        phase2_months = months - phase1_months
        
        monthly_payouts = []
        bequest_curve = []
        
        # 第一阶段：从RA支付
        if phase1_months > 0:
            if abs(ra_rate) < 1e-12:
                ra_monthly_payout = ra_remaining / phase1_months
            else:
                ra_monthly_payout = ra_remaining * (ra_rate / (1 - (1 + ra_rate) ** (-phase1_months)))
            
            current_premium = premium
            current_ra = ra_remaining
            
            for month in range(phase1_months):
                # 年金池计息
                current_premium *= (1 + monthly_rate)
                # RA计息
                current_ra *= (1 + ra_rate)
                
                # 支付
                payout = min(ra_monthly_payout, current_ra)
                current_ra -= payout
                
                monthly_payouts.append(payout)
                bequest_curve.append(max(0.0, current_premium) + max(0.0, current_ra))
        
        # 第二阶段：从年金池支付
        if phase2_months > 0:
            if abs(monthly_rate) < 1e-12:
                premium_monthly_payout = current_premium / phase2_months
            else:
                premium_monthly_payout = current_premium * (monthly_rate / (1 - (1 + monthly_rate) ** (-phase2_months)))
            
            for month in range(phase2_months):
                # 年金池计息
                current_premium *= (1 + monthly_rate)
                
                # 支付
                payout = min(premium_monthly_payout, current_premium)
                current_premium -= payout
                
                monthly_payouts.append(payout)
                bequest_curve.append(max(0.0, current_premium))
        
        total_payout = sum(monthly_payouts)
        final_balance = bequest_curve[-1] if bequest_curve else 0.0
        
        return CPFLifeResult(
            plan="basic",
            ra65_balance=ra65_balance,
            monthly_payouts=monthly_payouts,
            total_payout=total_payout,
            final_balance=final_balance,
            bequest_curve=bequest_curve,
            payout_efficiency=total_payout / ra65_balance if ra65_balance > 0 else 0,
            bequest_at_80=self._get_bequest_at_age(bequest_curve, 80),
            bequest_at_90=self._get_bequest_at_age(bequest_curve, 90)
        )
    
    def _get_bequest_at_age(self, bequest_curve: List[float], target_age: int) -> float:
        """获取指定年龄的遗赠金额"""
        if target_age <= self.params.retirement_age:
            return 0.0
        
        month_index = (target_age - self.params.retirement_age) * 12
        if month_index < len(bequest_curve):
            return bequest_curve[month_index]
        else:
            return bequest_curve[-1] if bequest_curve else 0.0
    
    def _calculate_irr(self, cashflows: List[float]) -> Optional[float]:
        """计算IRR - 改进版，避免溢出"""
        if not cashflows or len(cashflows) < 2:
            return None
        
        # 检查现金流是否有效
        if all(cf >= 0 for cf in cashflows) or all(cf <= 0 for cf in cashflows):
            return None
        
        # 使用二分法，更稳定
        def npv(rate):
            try:
                return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows))
            except (OverflowError, ZeroDivisionError):
                return float('inf') if rate > 0 else float('-inf')
        
        # 寻找合适的区间
        low, high = -0.99, 1.0
        max_iter = 100
        tolerance = 1e-8
        
        # 检查边界
        npv_low = npv(low)
        npv_high = npv(high)
        
        if npv_low * npv_high > 0:
            # 尝试更宽的区间
            low, high = -0.999, 10.0
            npv_low = npv(low)
            npv_high = npv(high)
            
            if npv_low * npv_high > 0:
                return None
        
        # 二分法求解
        for _ in range(max_iter):
            mid = (low + high) / 2
            npv_mid = npv(mid)
            
            if abs(npv_mid) < tolerance or (high - low) < tolerance:
                return mid
            
            if npv_low * npv_mid <= 0:
                high, npv_high = mid, npv_mid
            else:
                low, npv_low = mid, npv_mid
        
        return (low + high) / 2
    
    def _calculate_npv(self, cashflows: List[float], discount_rate: float = 0.04) -> float:
        """计算NPV - 改进版，避免溢出"""
        try:
            return sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(cashflows))
        except (OverflowError, ZeroDivisionError):
            # 如果发生溢出，使用更保守的贴现率
            conservative_rate = min(discount_rate, 0.1)  # 限制在10%以内
            return sum(cf / ((1 + conservative_rate) ** t) for t, cf in enumerate(cashflows))
    
    def _validate_results(self, result: CPFComprehensiveResult) -> Tuple[bool, List[str]]:
        """验证结果"""
        errors = []
        
        # 检查MA余额不超过BHS
        for year_result in result.yearly_results:
            if year_result.ma_balance > year_result.bhs_limit + 1e-6:
                errors.append(f"Age {year_result.age}: MA balance {year_result.ma_balance:.2f} exceeds BHS limit {year_result.bhs_limit:.2f}")
        
        # 检查账户余额非负
        for year_result in result.yearly_results:
            if year_result.oa_balance < -1e-6:
                errors.append(f"Age {year_result.age}: OA balance is negative: {year_result.oa_balance:.2f}")
            if year_result.sa_balance < -1e-6:
                errors.append(f"Age {year_result.age}: SA balance is negative: {year_result.sa_balance:.2f}")
            if year_result.ma_balance < -1e-6:
                errors.append(f"Age {year_result.age}: MA balance is negative: {year_result.ma_balance:.2f}")
            if year_result.ra_balance < -1e-6:
                errors.append(f"Age {year_result.age}: RA balance is negative: {year_result.ra_balance:.2f}")
        
        # 检查现金流平衡
        total_contributions = sum(yr.total_contrib for yr in result.yearly_results)
        if abs(total_contributions - result.total_contributions) > 1e-6:
            errors.append(f"Total contributions mismatch: calculated {total_contributions:.2f}, stored {result.total_contributions:.2f}")
        
        return len(errors) == 0, errors
    
    def run_comprehensive_simulation(self) -> CPFComprehensiveResult:
        """运行综合模拟"""
        # 初始化
        accounts = CPFAccountState()
        yearly_results = []
        monthly_cashflows = []
        
        # 工作期（到54岁）
        current_salary = self.params.annual_salary
        
        for age in range(self.params.start_age, 55):
            year = self.params.start_year + (age - self.params.start_age)
            
            # 分配缴费
            year_result = self._allocate_contributions(age, year, current_salary, accounts)
            yearly_results.append(year_result)
            
            # 记录月度现金流（负值）
            monthly_employee = -(year_result.employee_contrib / 12)
            monthly_system = -((year_result.employee_contrib + year_result.employer_contrib) / 12)
            
            if self.params.use_personal_irr:
                monthly_cashflows.extend([monthly_employee] * 12)
            else:
                monthly_cashflows.extend([monthly_system] * 12)
            
            # 薪资增长
            current_salary *= (1 + self.params.salary_growth_rate)
        
        # 55岁：先处理年度缴费，再建立RA
        age = 55
        year = self.params.start_year + (age - self.params.start_age)
        year_result = self._allocate_contributions(age, year, current_salary, accounts)
        yearly_results.append(year_result)
        
        # 记录月度现金流
        monthly_employee = -(year_result.employee_contrib / 12)
        monthly_system = -((year_result.employee_contrib + year_result.employer_contrib) / 12)
        
        if self.params.use_personal_irr:
            monthly_cashflows.extend([monthly_employee] * 12)
        else:
            monthly_cashflows.extend([monthly_system] * 12)
        
        # 建立RA
        ra_at_55, oa_at_55, sa_at_55, cash_at_55 = self._establish_ra_at_55(accounts, year)
        
        # 处理55岁提取的现金
        if cash_at_55 > 0:
            monthly_cashflows[-1] += cash_at_55
        
        # 56-64岁
        for age in range(56, self.params.retirement_age):
            year = self.params.start_year + (age - self.params.start_age)
            year_result = self._allocate_contributions(age, year, current_salary, accounts)
            yearly_results.append(year_result)
            
            # 记录月度现金流
            monthly_employee = -(year_result.employee_contrib / 12)
            monthly_system = -((year_result.employee_contrib + year_result.employer_contrib) / 12)
            
            if self.params.use_personal_irr:
                monthly_cashflows.extend([monthly_employee] * 12)
            else:
                monthly_cashflows.extend([monthly_system] * 12)
            
            # 薪资增长
            current_salary *= (1 + self.params.salary_growth_rate)
        
        # 65岁开始CPF LIFE
        ra65_balance = accounts.ra_balance
        cpf_life_result = self._calculate_cpf_life(ra65_balance)
        
        # 添加退休金现金流
        monthly_cashflows.extend(cpf_life_result.monthly_payouts)
        
        # 计算终值
        oa_at_65 = accounts.oa_balance
        ma_at_65 = accounts.ma_balance
        
        # 退休期OA/MA继续计息
        retirement_years = self.params.end_age - self.params.retirement_age
        oa_terminal = oa_at_65 * ((1 + self.params.oa_rate) ** retirement_years)
        ma_terminal = ma_at_65 * ((1 + self.params.ma_rate) ** retirement_years)
        
        terminal_value = cpf_life_result.final_balance + oa_terminal + ma_terminal
        monthly_cashflows.append(terminal_value)
        
        # 计算财务指标
        total_employee_contrib = sum(yr.employee_contrib for yr in yearly_results)
        total_employer_contrib = sum(yr.employer_contrib for yr in yearly_results)
        total_contributions = total_employee_contrib + total_employer_contrib
        total_benefits = cpf_life_result.total_payout + terminal_value
        
        # 计算IRR
        personal_irr = self._calculate_irr(monthly_cashflows)
        system_irr = None
        
        # 计算系统IRR（如果需要）
        if not self.params.use_personal_irr:
            system_cashflows = []
            for yr in yearly_results:
                monthly_system = -((yr.employee_contrib + yr.employer_contrib) / 12)
                system_cashflows.extend([monthly_system] * 12)
            system_cashflows.extend(cpf_life_result.monthly_payouts)
            system_cashflows.append(terminal_value)
            system_irr = self._calculate_irr(system_cashflows)
        
        # 计算NPV
        npv_personal = self._calculate_npv(monthly_cashflows)
        npv_system = None
        if not self.params.use_personal_irr:
            system_cashflows = []
            for yr in yearly_results:
                monthly_system = -((yr.employee_contrib + yr.employer_contrib) / 12)
                system_cashflows.extend([monthly_system] * 12)
            system_cashflows.extend(cpf_life_result.monthly_payouts)
            system_cashflows.append(terminal_value)
            npv_system = self._calculate_npv(system_cashflows)
        
        # 创建结果
        result = CPFComprehensiveResult(
            parameters=self.params,
            work_years=self.params.retirement_age - self.params.start_age,
            retirement_years=self.params.end_age - self.params.retirement_age,
            yearly_results=yearly_results,
            ra_established_at_55=ra_at_55,
            oa_remaining_at_55=oa_at_55,
            sa_remaining_at_55=sa_at_55,
            cash_withdrawn_at_55=cash_at_55,
            ra_balance_at_65=ra65_balance,
            oa_balance_at_65=oa_at_65,
            ma_balance_at_65=ma_at_65,
            cpf_life_result=cpf_life_result,
            total_employee_contributions=total_employee_contrib,
            total_employer_contributions=total_employer_contrib,
            total_contributions=total_contributions,
            total_benefits=total_benefits,
            terminal_value=terminal_value,
            personal_irr=personal_irr,
            system_irr=system_irr,
            npv_personal=npv_personal,
            npv_system=npv_system,
            monthly_cashflows=monthly_cashflows,
            validation_passed=False,
            validation_errors=[]
        )
        
        # 验证结果
        validation_passed, validation_errors = self._validate_results(result)
        result.validation_passed = validation_passed
        result.validation_errors = validation_errors
        
        return result
    
    def compare_plans(self, ra65_balance: float) -> Dict[str, CPFLifeResult]:
        """比较不同CPF LIFE计划"""
        plans = ["standard", "escalating", "basic"]
        results = {}
        
        for plan in plans:
            original_plan = self.params.cpf_life_plan
            self.params.cpf_life_plan = plan
            results[plan] = self._calculate_cpf_life(ra65_balance)
            self.params.cpf_life_plan = original_plan
        
        return results
    
    def analyze_bequest_scenarios(self, ra65_balance: float, plan: str, 
                                 death_ages: List[int] = None) -> Dict[int, float]:
        """分析遗赠情景"""
        if death_ages is None:
            death_ages = [70, 75, 80, 85, 90, 95, 100]
        
        original_plan = self.params.cpf_life_plan
        self.params.cpf_life_plan = plan
        cpf_life_result = self._calculate_cpf_life(ra65_balance)
        self.params.cpf_life_plan = original_plan
        
        bequest_scenarios = {}
        for death_age in death_ages:
            bequest_scenarios[death_age] = self._get_bequest_at_age(
                cpf_life_result.bequest_curve, death_age
            )
        
        return bequest_scenarios
    
    def calculate_optimal_plan(self, ra65_balance: float, 
                              preferences: Dict[str, float] = None) -> Dict[str, Any]:
        """计算最优计划"""
        if preferences is None:
            preferences = {
                'income_weight': 0.4,
                'bequest_weight': 0.3,
                'stability_weight': 0.3
            }
        
        plan_results = self.compare_plans(ra65_balance)
        
        # 计算各计划评分
        scores = {}
        for plan, result in plan_results.items():
            # 收入评分（基于总支付）
            income_score = result.total_payout / ra65_balance if ra65_balance > 0 else 0
            
            # 遗赠评分（基于80岁遗赠）
            bequest_score = result.bequest_at_80 / ra65_balance if ra65_balance > 0 else 0
            
            # 稳定性评分（基于支付效率）
            stability_score = result.payout_efficiency
            
            # 综合评分
            total_score = (preferences['income_weight'] * income_score +
                         preferences['bequest_weight'] * bequest_score +
                         preferences['stability_weight'] * stability_score)
            
            scores[plan] = total_score
        
        optimal_plan = max(scores, key=scores.get)
        
        return {
            'optimal_plan': optimal_plan,
            'scores': scores,
            'plan_results': plan_results,
            'recommendation': f"基于当前偏好，推荐{optimal_plan}计划"
        }


# 便捷函数
def create_default_parameters(**kwargs) -> CPFParameters:
    """创建默认参数"""
    return CPFParameters(**kwargs)


def run_cpf_simulation(**kwargs) -> CPFComprehensiveResult:
    """运行CPF模拟"""
    parameters = create_default_parameters(**kwargs)
    engine = CPFComprehensiveEngine(parameters)
    return engine.run_comprehensive_simulation()


def compare_cpf_life_plans(ra65_balance: float, **kwargs) -> Dict[str, CPFLifeResult]:
    """比较CPF LIFE计划"""
    parameters = create_default_parameters(**kwargs)
    engine = CPFComprehensiveEngine(parameters)
    return engine.compare_plans(ra65_balance)


if __name__ == "__main__":
    # 演示
    print("=== CPF综合引擎演示 ===\n")
    
    # 基础案例
    result = run_cpf_simulation(
        start_age=30,
        retirement_age=65,
        end_age=90,
        annual_salary=180000,
        salary_growth_rate=0.02,
        ra_target_type="FRS",
        cpf_life_plan="standard"
    )
    
    print(f"工作年限: {result.work_years}年")
    print(f"退休年限: {result.retirement_years}年")
    print(f"总缴费: ${result.total_contributions:,.2f}")
    print(f"总收益: ${result.total_benefits:,.2f}")
    print(f"月退休金: ${result.cpf_life_result.monthly_payouts[0]:,.2f}")
    print(f"总退休金: ${result.cpf_life_result.total_payout:,.2f}")
    print(f"终值: ${result.terminal_value:,.2f}")
    print(f"个人IRR: {result.personal_irr:.2%}" if result.personal_irr else "个人IRR: N/A")
    print(f"验证通过: {result.validation_passed}")
    
    if result.validation_errors:
        print("验证错误:")
        for error in result.validation_errors:
            print(f"  - {error}")
    
    # 比较不同计划
    print("\n=== CPF LIFE计划比较 ===")
    plan_comparison = compare_cpf_life_plans(result.ra_balance_at_65)
    
    for plan, plan_result in plan_comparison.items():
        print(f"\n{plan.upper()}计划:")
        print(f"  月退休金: ${plan_result.monthly_payouts[0]:,.2f}")
        print(f"  总退休金: ${plan_result.total_payout:,.2f}")
        print(f"  终值: ${plan_result.final_balance:,.2f}")
        print(f"  80岁遗赠: ${plan_result.bequest_at_80:,.2f}")
        print(f"  支付效率: {plan_result.payout_efficiency:.2%}")