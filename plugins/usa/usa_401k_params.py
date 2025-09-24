#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国401k参数配置
基于2024-2025年IRS最新规定
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class USA401kParams:
    """美国401k参数配置"""

    # 2024年参数
    year_2024 = {
        # 员工缴费限制 (402(g))
        'employee_deferral_limit': 23000,      # 基础限制
        'catch_up_limit_50_plus': 7500,        # 50岁及以上追加
        'super_catch_up_60_63': 11250,         # 60-63岁超级追加

        # 总缴费限制 (415(c))
        'total_contribution_limit': 69000,     # 员工+雇主总限制

        # 薪酬基数限制 (401(a)(17))
        'compensation_cap': 345000,            # 薪酬上限

        # 贷款限制
        'max_loan_amount': 50000,              # 最高贷款额
        'max_loan_percentage': 0.50,           # 账户余额50%
    }

    # 2025年参数
    year_2025 = {
        # 员工缴费限制 (402(g))
        'employee_deferral_limit': 23500,      # 基础限制
        'catch_up_limit_50_plus': 7500,        # 50岁及以上追加
        'super_catch_up_60_63': 11250,         # 60-63岁超级追加

        # 总缴费限制 (415(c))
        'total_contribution_limit': 70000,     # 员工+雇主总限制

        # 薪酬基数限制 (401(a)(17))
        'compensation_cap': 350000,            # 薪酬上限

        # 贷款限制
        'max_loan_amount': 50000,              # 最高贷款额
        'max_loan_percentage': 0.50,           # 账户余额50%
    }

    def __init__(self, year: int = 2025):
        """初始化401k参数"""
        self.year = year
        self.params = self.year_2025 if year >= 2025 else self.year_2024

        # 基础参数
        self.employee_deferral_limit = self.params['employee_deferral_limit']
        self.catch_up_limit_50_plus = self.params['catch_up_limit_50_plus']
        self.super_catch_up_60_63 = self.params['super_catch_up_60_63']
        self.total_contribution_limit = self.params['total_contribution_limit']
        self.compensation_cap = self.params['compensation_cap']
        self.max_loan_amount = self.params['max_loan_amount']
        self.max_loan_percentage = self.params['max_loan_percentage']

        # 年龄相关限制
        self.catch_up_age = 50
        self.super_catch_up_start_age = 60
        self.super_catch_up_end_age = 63

        # 提取规则
        self.early_withdrawal_penalty_age = 59.5
        self.rmd_start_age = 73  # 2023年后出生的人
        self.rmd_start_age_2033 = 75  # 2033年后出生的人

        # 投资回报率假设
        self.default_investment_return = 0.07  # 7%年回报率
        self.conservative_return = 0.05        # 5%保守型
        self.aggressive_return = 0.09          # 9%激进型

        # 通胀率假设
        self.inflation_rate = 0.03             # 3%通胀率

        # 退休年限假设
        self.default_retirement_years = 20     # 20年退休期
        self.life_expectancy = 85              # 预期寿命85岁


@dataclass
class EmployerMatchRule:
    """雇主匹配规则"""

    def __init__(self,
                 match_type: str = "tiered",
                 tier1_rate: float = 1.0,
                 tier1_limit: float = 0.03,
                 tier2_rate: float = 0.5,
                 tier2_limit: float = 0.02,
                 max_match_percentage: float = 0.05):
        """
        初始化雇主匹配规则

        Args:
            match_type: 匹配类型 ("tiered", "simple", "none")
            tier1_rate: 第一层匹配率 (如1.0表示100%匹配)
            tier1_limit: 第一层匹配上限 (如0.03表示3%)
            tier2_rate: 第二层匹配率 (如0.5表示50%匹配)
            tier2_limit: 第二层匹配上限 (如0.02表示2%)
            max_match_percentage: 最大匹配百分比
        """
        self.match_type = match_type
        self.tier1_rate = tier1_rate
        self.tier1_limit = tier1_limit
        self.tier2_rate = tier2_rate
        self.tier2_limit = tier2_limit
        self.max_match_percentage = max_match_percentage

    def calculate_match(self, employee_contribution: float, annual_salary: float) -> float:
        """计算雇主匹配金额"""
        if self.match_type == "none":
            return 0.0

        # 基于薪酬上限计算
        compensation_for_match = min(annual_salary, 350000)  # 2025年薪酬上限

        if self.match_type == "simple":
            # 简单匹配：固定比例匹配
            match_rate = min(self.tier1_rate, self.max_match_percentage)
            return min(employee_contribution * match_rate,
                      compensation_for_match * self.max_match_percentage)

        elif self.match_type == "tiered":
            # 分层匹配：100%匹配前3% + 50%匹配接下2%
            total_match = 0.0

            # 第一层：100%匹配前3%
            tier1_contribution = min(employee_contribution,
                                   compensation_for_match * self.tier1_limit)
            tier1_match = tier1_contribution * self.tier1_rate
            total_match += tier1_match

            # 第二层：50%匹配接下2%
            remaining_contribution = max(0, employee_contribution - tier1_contribution)
            tier2_contribution = min(remaining_contribution,
                                   compensation_for_match * self.tier2_limit)
            tier2_match = tier2_contribution * self.tier2_rate
            total_match += tier2_match

            return total_match

        return 0.0


@dataclass
class USA401kLimits:
    """401k限制计算器"""

    def __init__(self, year: int = 2025):
        self.params = USA401kParams(year)

    def get_employee_contribution_limit(self, age: int) -> Dict[str, float]:
        """获取员工缴费限制"""
        base_limit = self.params.employee_deferral_limit

        if self.params.super_catch_up_start_age <= age <= self.params.super_catch_up_end_age:
            # 60-63岁：使用超级追加
            catch_up = self.params.super_catch_up_60_63
        elif age >= self.params.catch_up_age:
            # 50岁及以上：使用标准追加
            catch_up = self.params.catch_up_limit_50_plus
        else:
            # 50岁以下：无追加
            catch_up = 0

        return {
            'base_limit': base_limit,
            'catch_up_limit': catch_up,
            'total_limit': base_limit + catch_up,
            'age': age,
            'catch_up_type': 'super' if self.params.super_catch_up_start_age <= age <= self.params.super_catch_up_end_age
                           else 'standard' if age >= self.params.catch_up_age
                           else 'none'
        }

    def get_total_contribution_limit(self) -> float:
        """获取总缴费限制（员工+雇主）"""
        return self.params.total_contribution_limit

    def get_compensation_cap(self) -> float:
        """获取薪酬基数上限"""
        return self.params.compensation_cap

    def is_contribution_valid(self,
                            employee_contribution: float,
                            employer_match: float,
                            age: int) -> Dict[str, bool]:
        """验证缴费是否合规"""
        limits = self.get_employee_contribution_limit(age)

        # 检查员工缴费限制
        employee_valid = employee_contribution <= limits['total_limit']

        # 检查总缴费限制（不包含追加缴费）
        base_employee = min(employee_contribution, limits['base_limit'])
        total_valid = (base_employee + employer_match) <= self.params.total_contribution_limit

        return {
            'employee_valid': employee_valid,
            'total_valid': total_valid,
            'overall_valid': employee_valid and total_valid,
            'employee_excess': max(0, employee_contribution - limits['total_limit']),
            'total_excess': max(0, (base_employee + employer_match) - self.params.total_contribution_limit)
        }


# 预定义的雇主匹配规则
EMPLOYER_MATCH_PRESETS = {
    'none': EmployerMatchRule(match_type="none"),
    'simple_3_percent': EmployerMatchRule(match_type="simple", tier1_rate=1.0, max_match_percentage=0.03),
    'simple_6_percent': EmployerMatchRule(match_type="simple", tier1_rate=0.5, max_match_percentage=0.06),
    'tiered_3_2': EmployerMatchRule(match_type="tiered", tier1_rate=1.0, tier1_limit=0.03,
                                   tier2_rate=0.5, tier2_limit=0.02),
    'tiered_4_2': EmployerMatchRule(match_type="tiered", tier1_rate=1.0, tier1_limit=0.04,
                                   tier2_rate=0.5, tier2_limit=0.02),
    'tiered_6_3': EmployerMatchRule(match_type="tiered", tier1_rate=1.0, tier1_limit=0.06,
                                   tier2_rate=0.5, tier2_limit=0.03),
}


def get_401k_params(year: int = 2025) -> USA401kParams:
    """获取401k参数"""
    return USA401kParams(year)


def get_employer_match_rule(preset: str = 'tiered_3_2') -> EmployerMatchRule:
    """获取雇主匹配规则"""
    return EMPLOYER_MATCH_PRESETS.get(preset, EMPLOYER_MATCH_PRESETS['tiered_3_2'])


def get_401k_limits(year: int = 2025) -> USA401kLimits:
    """获取401k限制计算器"""
    return USA401kLimits(year)


if __name__ == "__main__":
    # 测试参数配置
    print("=== 美国401k参数配置测试 ===")

    # 测试2025年参数
    params_2025 = get_401k_params(2025)
    print(f"\n2025年参数:")
    print(f"员工基础缴费限制: ${params_2025.employee_deferral_limit:,}")
    print(f"50岁及以上追加: ${params_2025.catch_up_limit_50_plus:,}")
    print(f"60-63岁超级追加: ${params_2025.super_catch_up_60_63:,}")
    print(f"总缴费限制: ${params_2025.total_contribution_limit:,}")
    print(f"薪酬上限: ${params_2025.compensation_cap:,}")

    # 测试限制计算器
    limits = get_401k_limits(2025)

    print(f"\n不同年龄的缴费限制:")
    for age in [30, 50, 55, 60, 63, 65]:
        limit_info = limits.get_employee_contribution_limit(age)
        print(f"年龄{age}岁: ${limit_info['total_limit']:,} "
              f"(基础${limit_info['base_limit']:,} + 追加${limit_info['catch_up_limit']:,})")

    # 测试雇主匹配规则
    print(f"\n雇主匹配规则测试:")
    match_rule = get_employer_match_rule('tiered_3_2')

    test_cases = [
        (50000, 0.03),  # 年收入5万，缴费3%
        (50000, 0.05),  # 年收入5万，缴费5%
        (100000, 0.10), # 年收入10万，缴费10%
    ]

    for annual_salary, deferral_rate in test_cases:
        employee_contribution = annual_salary * deferral_rate
        employer_match = match_rule.calculate_match(employee_contribution, annual_salary)
        match_rate = (employer_match / employee_contribution * 100) if employee_contribution > 0 else 0

        print(f"年收入${annual_salary:,}, 缴费{deferral_rate:.1%}: "
              f"员工${employee_contribution:,.0f}, 雇主匹配${employer_match:,.0f} "
              f"(匹配率{match_rate:.1f}%)")
