#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国养老金计算器
简化版本，整合了us插件的功能
"""

from typing import Dict, Any, List
import math
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class USAPensionCalculator:
    """美国退休金计算器（社会保障金）"""

    def __init__(self):
        self.country_code = "US"
        self.country_name = "美国"

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算美国退休金 - 简化版"""
        monthly_salary = salary_profile.monthly_salary
        work_years = person.work_years if person.work_years > 0 else 35

        # 社安金缴费率（简化）
        ss_rate = 0.062 * 2  # 雇员+雇主各6.2%

        # 缴费基数上限（2024年）
        max_taxable_earnings = 160200 / 12  # 月度上限
        contribution_base = min(monthly_salary, max_taxable_earnings)

        # 计算累积缴费
        annual_contribution = contribution_base * 12 * ss_rate

        # 简化的社安金计算（实际更复杂）
        # 美国使用平均指数化月收入的复杂公式，这里简化处理
        # 对于高收入者，社安金替代率会降低
        if contribution_base <= 5000:  # 月收入5000美元以下
            replacement_rate = 0.40
        elif contribution_base <= 10000:  # 月收入5000-10000美元
            replacement_rate = 0.30
        else:  # 月收入10000美元以上
            replacement_rate = 0.20

        # 进一步限制高收入者的社安金
        if contribution_base > 13350:  # 超过社安金最高缴费基数
            replacement_rate = 0.15  # 进一步降低替代率

        monthly_benefit = contribution_base * replacement_rate

        total_contribution = annual_contribution * work_years
        retirement_years = 20  # 假设领取20年
        total_benefit = monthly_benefit * 12 * retirement_years

        roi = ((total_benefit / total_contribution) - 1) * 100 if total_contribution > 0 else 0

        # 回本年龄
        retirement_age = 67  # 美国退休年龄
        if monthly_benefit > 0:
            break_even_months = total_contribution / monthly_benefit
            break_even_age = retirement_age + (break_even_months / 12)
            break_even_age = int(break_even_age) if break_even_age < 85 else None
        else:
            break_even_age = None

        return PensionResult(
            monthly_pension=monthly_benefit,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            retirement_account_balance=0.0,  # 社安金没有账户余额概念
            break_even_age=break_even_age,
            roi=roi,
            original_currency="USD",
            details={
                'contribution_base': contribution_base,
                'ss_rate': ss_rate,
                'work_years': work_years,
                'retirement_age': retirement_age,
                'max_taxable_earnings': max_taxable_earnings
            }
        )

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        return 67

    def calculate_future_value(self, present_value: float, years: float, rate: float) -> float:
        """计算未来价值"""
        if rate == 0:
            return present_value * years
        return present_value * ((1 + rate) ** years - 1) / rate
