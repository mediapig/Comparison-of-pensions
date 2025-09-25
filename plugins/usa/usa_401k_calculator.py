#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国401k计算器
基于2024-2025年IRS最新规定
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import math
from datetime import date

try:
    from .usa_401k_params import (
        USA401kParams,
        EmployerMatchRule,
        USA401kLimits,
        get_401k_params,
        get_employer_match_rule,
        get_401k_limits
    )
except ImportError:
    from usa_401k_params import (
        USA401kParams,
        EmployerMatchRule,
        USA401kLimits,
        get_401k_params,
        get_employer_match_rule,
        get_401k_limits
    )


@dataclass
class USA401kContribution:
    """401k缴费结果"""
    year: int
    age: int
    annual_salary: float

    # 员工缴费
    employee_deferral: float
    catch_up_contribution: float
    total_employee_contribution: float

    # 雇主匹配
    employer_match: float

    # 总缴费
    total_contribution: float

    # 限制信息
    employee_limit: float
    total_limit: float
    compensation_cap: float

    # 合规性
    is_compliant: bool
    excess_amount: float


@dataclass
class USA401kBalance:
    """401k账户余额"""
    total_balance: float
    employee_contributions: float
    employer_contributions: float
    investment_gains: float

    # 按年份分解
    yearly_balances: List[Dict[str, float]]


@dataclass
class USA401kWithdrawal:
    """401k提取结果"""
    monthly_withdrawal: float
    annual_withdrawal: float
    total_withdrawal_period: int  # 年数

    # 提取策略
    withdrawal_strategy: str  # "annuity", "4_percent_rule", "rmd"

    # 税务影响
    taxable_amount: float
    tax_rate: float
    after_tax_amount: float


@dataclass
class USA401kResult:
    """401k计算结果"""
    # 缴费历史
    contribution_history: List[USA401kContribution]

    # 账户余额
    final_balance: USA401kBalance

    # 提取分析
    withdrawal_analysis: USA401kWithdrawal

    # 投资回报
    total_contributions: float
    total_gains: float
    annualized_return: float

    # 合规性
    compliance_summary: Dict[str, Any]


class USA401kCalculator:
    """美国401k计算器"""

    def __init__(self, year: int = 2025):
        """初始化401k计算器"""
        self.year = year
        self.params = get_401k_params(year)
        self.limits = get_401k_limits(year)
        self.employer_match_rule = get_employer_match_rule('tiered_3_2')

    def calculate_401k_lifetime(self,
                              start_age: int,
                              retirement_age: int,
                              initial_annual_salary: float,
                              salary_growth_rate: float = 0.03,
                              deferral_rate: float = 0.10,
                              investment_return_rate: float = None,
                              employer_match_preset: str = 'tiered_3_2') -> USA401kResult:
        """
        计算终身401k

        Args:
            start_age: 开始缴费年龄
            retirement_age: 退休年龄
            initial_annual_salary: 初始年薪
            salary_growth_rate: 薪资年增长率
            deferral_rate: 缴费比例
            investment_return_rate: 投资回报率
            employer_match_preset: 雇主匹配预设

        Returns:
            401k计算结果
        """
        if investment_return_rate is None:
            investment_return_rate = self.params.default_investment_return

        # 设置雇主匹配规则
        self.employer_match_rule = get_employer_match_rule(employer_match_preset)

        # 计算缴费历史
        contribution_history = self._calculate_contribution_history(
            start_age, retirement_age, initial_annual_salary,
            salary_growth_rate, deferral_rate
        )

        # 计算账户余额
        final_balance = self._calculate_balance(
            contribution_history, investment_return_rate
        )

        # 计算提取分析
        withdrawal_analysis = self._calculate_withdrawal(
            final_balance.total_balance, retirement_age
        )

        # 计算投资回报
        total_contributions = sum(contrib.total_contribution for contrib in contribution_history)
        total_gains = final_balance.total_balance - total_contributions
        annualized_return = self._calculate_annualized_return(
            total_contributions, final_balance.total_balance, retirement_age - start_age
        )

        # 合规性总结
        compliance_summary = self._analyze_compliance(contribution_history)

        return USA401kResult(
            contribution_history=contribution_history,
            final_balance=final_balance,
            withdrawal_analysis=withdrawal_analysis,
            total_contributions=total_contributions,
            total_gains=total_gains,
            annualized_return=annualized_return,
            compliance_summary=compliance_summary
        )

    def _calculate_contribution_history(self,
                                      start_age: int,
                                      retirement_age: int,
                                      initial_annual_salary: float,
                                      salary_growth_rate: float,
                                      deferral_rate: float) -> List[USA401kContribution]:
        """计算缴费历史"""
        history = []
        current_salary = initial_annual_salary

        for year_offset in range(retirement_age - start_age):
            year = self.year + year_offset
            age = start_age + year_offset

            # 计算当年缴费
            contribution = self._calculate_yearly_contribution(
                year, age, current_salary, deferral_rate
            )
            history.append(contribution)

            # 薪资增长
            current_salary *= (1 + salary_growth_rate)

        return history

    def _calculate_yearly_contribution(self,
                                     year: int,
                                     age: int,
                                     annual_salary: float,
                                     deferral_rate: float) -> USA401kContribution:
        """计算年度缴费"""
        # 获取年龄相关的缴费限制
        age_limits = self.limits.get_employee_contribution_limit(age)

        # 计算员工缴费
        target_deferral = annual_salary * deferral_rate
        employee_deferral = min(target_deferral, age_limits['base_limit'])

        # 计算追加缴费
        if age_limits['catch_up_limit'] > 0:
            remaining_deferral = max(0, target_deferral - employee_deferral)
            catch_up_contribution = min(remaining_deferral, age_limits['catch_up_limit'])
        else:
            catch_up_contribution = 0

        total_employee_contribution = employee_deferral + catch_up_contribution

        # 计算雇主匹配（基于基础缴费，不包含追加）
        employer_match = self.employer_match_rule.calculate_match(
            employee_deferral, annual_salary
        )

        # 总缴费
        total_contribution = total_employee_contribution + employer_match

        # 合规性检查
        compliance = self.limits.is_contribution_valid(
            total_employee_contribution, employer_match, age
        )

        return USA401kContribution(
            year=year,
            age=age,
            annual_salary=annual_salary,
            employee_deferral=employee_deferral,
            catch_up_contribution=catch_up_contribution,
            total_employee_contribution=total_employee_contribution,
            employer_match=employer_match,
            total_contribution=total_contribution,
            employee_limit=age_limits['total_limit'],
            total_limit=self.limits.get_total_contribution_limit(),
            compensation_cap=self.limits.get_compensation_cap(),
            is_compliant=compliance['overall_valid'],
            excess_amount=compliance['employee_excess'] + compliance['total_excess']
        )

    def _calculate_balance(self,
                         contribution_history: List[USA401kContribution],
                         investment_return_rate: float) -> USA401kBalance:
        """计算账户余额"""
        yearly_balances = []
        total_balance = 0.0
        total_employee_contributions = 0.0
        total_employer_contributions = 0.0

        for i, contrib in enumerate(contribution_history):
            # 计算这笔缴费到退休时的未来价值
            years_to_retirement = len(contribution_history) - i - 1

            if years_to_retirement > 0:
                future_value = contrib.total_contribution * ((1 + investment_return_rate) ** years_to_retirement)
            else:
                future_value = contrib.total_contribution

            total_balance += future_value
            total_employee_contributions += contrib.total_employee_contribution
            total_employer_contributions += contrib.employer_match

            yearly_balances.append({
                'year': contrib.year,
                'age': contrib.age,
                'contribution': contrib.total_contribution,
                'future_value': future_value,
                'cumulative_balance': total_balance
            })

        investment_gains = total_balance - total_employee_contributions - total_employer_contributions

        return USA401kBalance(
            total_balance=total_balance,
            employee_contributions=total_employee_contributions,
            employer_contributions=total_employer_contributions,
            investment_gains=investment_gains,
            yearly_balances=yearly_balances
        )

    def _calculate_withdrawal(self,
                            balance: float,
                            retirement_age: int) -> USA401kWithdrawal:
        """计算提取分析"""
        # 使用4%规则提取（更保守和现实的方法）
        four_percent_annual = balance * 0.04
        four_percent_monthly = four_percent_annual / 12

        # 税务影响（假设25%税率）
        tax_rate = 0.25
        taxable_amount = four_percent_annual
        tax_amount = taxable_amount * tax_rate
        after_tax_amount = taxable_amount - tax_amount

        return USA401kWithdrawal(
            monthly_withdrawal=four_percent_monthly,
            annual_withdrawal=four_percent_annual,
            total_withdrawal_period=25,  # 4%规则通常假设25年
            withdrawal_strategy="4_percent_rule",
            taxable_amount=taxable_amount,
            tax_rate=tax_rate,
            after_tax_amount=after_tax_amount
        )

    def _calculate_annualized_return(self,
                                   total_contributions: float,
                                   final_balance: float,
                                   years: int) -> float:
        """计算年化回报率"""
        if total_contributions <= 0 or years <= 0:
            return 0.0

        # 简化的年化回报率计算
        # 实际应该使用IRR计算
        return (final_balance / total_contributions) ** (1 / years) - 1

    def _analyze_compliance(self,
                          contribution_history: List[USA401kContribution]) -> Dict[str, Any]:
        """分析合规性"""
        total_years = len(contribution_history)
        compliant_years = sum(1 for contrib in contribution_history if contrib.is_compliant)

        total_excess = sum(contrib.excess_amount for contrib in contribution_history)

        return {
            'total_years': total_years,
            'compliant_years': compliant_years,
            'compliance_rate': compliant_years / total_years if total_years > 0 else 0,
            'total_excess': total_excess,
            'has_excess': total_excess > 0
        }

    def get_contribution_scenarios(self,
                                 annual_salary: float,
                                 years: int = 35,
                                 investment_rate: float = 0.07) -> List[Dict[str, Any]]:
        """获取不同缴费比例的401K场景分析"""
        scenarios = []
        deferral_rates = [0.05, 0.08, 0.10, 0.15, 0.20]

        for rate in deferral_rates:
            # 计算年缴费
            annual_contribution = min(annual_salary * rate, 23500)  # 基础上限

            # 计算N年后的余额
            if investment_rate > 0:
                future_value = annual_contribution * ((1 + investment_rate) ** years - 1) / investment_rate
            else:
                future_value = annual_contribution * years

            # 计算月退休金 (25年)
            months = 300
            monthly_pension = future_value / months

            scenarios.append({
                'deferral_rate': rate,
                'annual_contribution': annual_contribution,
                'future_value': future_value,
                'monthly_pension': monthly_pension
            })

        return scenarios

    def get_employer_match_analysis(self, annual_salary: float) -> List[Dict[str, Any]]:
        """获取雇主配比影响分析"""
        analysis = []
        employee_contribution_rates = [0.03, 0.05, 0.08, 0.10]

        for rate in employee_contribution_rates:
            employee_amount = annual_salary * rate

            # 计算雇主配比
            employer_match = self.employer_match_rule.calculate_match(employee_amount, annual_salary)

            total_contribution = employee_amount + employer_match
            match_rate = (employer_match / employee_amount * 100) if employee_amount > 0 else 0

            analysis.append({
                'employee_rate': rate,
                'employee_amount': employee_amount,
                'employer_match': employer_match,
                'total_contribution': total_contribution,
                'match_rate': match_rate
            })

        return analysis


def create_401k_calculator(year: int = 2025) -> USA401kCalculator:
    """创建401k计算器"""
    return USA401kCalculator(year)


if __name__ == "__main__":
    # 测试401k计算器
    print("=== 美国401k计算器测试 ===")

    calculator = create_401k_calculator(2025)

    # 测试终身401k计算
    result = calculator.calculate_401k_lifetime(
        start_age=30,
        retirement_age=65,
        initial_annual_salary=80000,
        salary_growth_rate=0.03,
        deferral_rate=0.10,
        investment_return_rate=0.07
    )

    print(f"\n终身401k计算结果:")
    print(f"总缴费: ${result.total_contributions:,.2f}")
    print(f"最终余额: ${result.final_balance.total_balance:,.2f}")
    print(f"投资回报: ${result.total_gains:,.2f}")
    print(f"年化回报率: {result.annualized_return:.2%}")
    print(f"月退休金: ${result.withdrawal_analysis.monthly_withdrawal:,.2f}")
    print(f"年退休金: ${result.withdrawal_analysis.annual_withdrawal:,.2f}")

    print(f"\n合规性分析:")
    print(f"合规年数: {result.compliance_summary['compliant_years']}/{result.compliance_summary['total_years']}")
    print(f"合规率: {result.compliance_summary['compliance_rate']:.1%}")

    # 测试不同缴费比例场景
    print(f"\n不同缴费比例场景:")
    scenarios = calculator.get_contribution_scenarios(80000, 35, 0.07)
    print(f"{'缴费比例':<10} {'年缴费':<15} {'35年后余额':<20} {'月退休金':<15}")
    print("-" * 60)

    for scenario in scenarios:
        print(f"{scenario['deferral_rate']:>8.1%}  ${scenario['annual_contribution']:>12,.0f}  "
              f"${scenario['future_value']:>17,.0f}  ${scenario['monthly_pension']:>12,.0f}")

    # 测试雇主匹配分析
    print(f"\n雇主匹配分析 (年收入$80,000):")
    match_analysis = calculator.get_employer_match_analysis(80000)
    print(f"{'员工缴费率':<10} {'员工缴费':<15} {'雇主匹配':<15} {'总缴费':<15} {'匹配率':<10}")
    print("-" * 70)

    for analysis in match_analysis:
        print(f"{analysis['employee_rate']:>8.1%}  ${analysis['employee_amount']:>12,.0f}  "
              f"${analysis['employer_match']:>12,.0f}  ${analysis['total_contribution']:>12,.0f}  "
              f"{analysis['match_rate']:>7.1f}%")
