#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本修正计算器
基于准确的日本社保和税收政策
"""

from typing import Dict, Any, Optional
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, Gender, EmploymentType

def calc_income_tax_corrected(taxable_income: float) -> float:
    """计算日本所得税（修正版）"""
    if taxable_income <= 0:
        return 0

    # 日本所得税税率表（2024年）
    brackets = [
        (0, 1_950_000, 0.05),
        (1_950_000, 3_300_000, 0.10),
        (3_300_000, 6_950_000, 0.20),
        (6_950_000, 9_000_000, 0.23),
        (9_000_000, 18_000_000, 0.33),
        (18_000_000, 40_000_000, 0.40),
        (40_000_000, float('inf'), 0.45)
    ]

    tax = 0
    for min_income, max_income, rate in brackets:
        if taxable_income > min_income:
            taxable_in_bracket = min(taxable_income - min_income, max_income - min_income)
            tax += taxable_in_bracket * rate

    return tax

def calc_salary_deduction(annual_salary: float) -> float:
    """计算工资所得控除（2024年）- 正确的梯度计算"""
    # 按照用户提供的正确梯度计算
    if annual_salary <= 1_800_000:
        # ≤1.8M：40%−100k
        return annual_salary * 0.4 - 100_000
    elif annual_salary <= 3_600_000:
        # ≤3.6M：30%+80k
        return annual_salary * 0.3 + 80_000
    elif annual_salary <= 6_600_000:
        # ≤6.6M：20%+440k（5M 案例 → 1,440,000）
        return annual_salary * 0.2 + 440_000
    elif annual_salary <= 8_500_000:
        # ≤8.5M：10%+1,100k
        return annual_salary * 0.1 + 1_100_000
    else:
        # ＞8.5M：1,950,000（封顶）（20M 案例 → 1,950,000）
        return 1_950_000

def calc_social_security_corrected(monthly_salary: float) -> Dict[str, float]:
    """计算社保缴费（修正版）"""
    # 厚生年金：18.3%（雇主/雇员各9.15%），上限65万日元/月
    kosei_base = min(monthly_salary, 650_000)
    kosei_total = kosei_base * 0.183
    kosei_employee = kosei_total / 2  # 9.15%
    kosei_employer = kosei_total / 2  # 9.15%

    # 健康保险：约10%（雇主/雇员各5%），上限按健保等级表
    # 健保上限通常比厚生年金高，这里设为139万日元/月
    kenko_base = min(monthly_salary, 1_390_000)
    kenko_total = kenko_base * 0.10
    kenko_employee = kenko_total / 2  # 5%
    kenko_employer = kenko_total / 2  # 5%

    # 雇用保险：员工0.6%，雇主0.3%，无上限
    koyo_total = monthly_salary * 0.009  # 0.6% + 0.3% = 0.9%
    koyo_employee = monthly_salary * 0.006  # 0.6%
    koyo_employer = monthly_salary * 0.003  # 0.3%

    return {
        'kosei': {
            'employee': kosei_employee,
            'employer': kosei_employer,
            'total': kosei_total,
            'base': kosei_base
        },
        'kenko': {
            'employee': kenko_employee,
            'employer': kenko_employer,
            'total': kenko_total,
            'base': kenko_base
        },
        'koyo': {
            'employee': koyo_employee,
            'employer': koyo_employer,
            'total': koyo_total
        }
    }

def calc_pension_corrected(monthly_salary: float, work_years: int) -> Dict[str, float]:
    """计算养老金（修正版）"""
    # 国民年金：固定66,250日元/月（满40年），按工作年限比例
    kokumin_months = work_years * 12
    kokumin_max_months = 40 * 12  # 480个月
    kokumin_rate = min(kokumin_months / kokumin_max_months, 1.0)
    kokumin_monthly = 66_250 * kokumin_rate

    # 厚生年金：平均标准报酬月额 × (5.481/1000) × 加入月数
    # 注意：这里应该计算年额，然后除以12得到月额
    kosei_base = min(monthly_salary, 650_000)  # 厚生年金上限
    kosei_annual = kosei_base * (5.481 / 1000) * work_years * 12  # 年额
    kosei_monthly = kosei_annual / 12  # 月额

    total_monthly = kokumin_monthly + kosei_monthly

    return {
        'kokumin_monthly': kokumin_monthly,
        'kosei_monthly': kosei_monthly,
        'total_monthly': total_monthly,
        'kokumin_rate': kokumin_rate
    }

class JapanCorrectedCalculator:
    """日本修正计算器"""

    def __init__(self):
        self.country_code = 'JP'
        self.country_name = '日本'
        self.currency = 'JPY'

    def calculate_comprehensive(self, person: Person, salary_profile: SalaryProfile,
                              economic_factors: EconomicFactors) -> Dict[str, Any]:
        """综合计算日本养老金、税收、社保（修正版）"""

        # 获取基本参数
        monthly_salary = salary_profile.monthly_salary
        annual_salary = monthly_salary * 12
        work_years = person.work_years if person.work_years > 0 else 35
        retirement_age = 65

        # 计算社保
        social_security = calc_social_security_corrected(monthly_salary)

        # 计算年度社保缴费
        annual_ss_employee = (social_security['kosei']['employee'] +
                            social_security['kenko']['employee'] +
                            social_security['koyo']['employee']) * 12

        annual_ss_employer = (social_security['kosei']['employer'] +
                            social_security['kenko']['employer'] +
                            social_security['koyo']['employer']) * 12

        annual_ss_total = annual_ss_employee + annual_ss_employer

        # 计算税收
        # 1. 工资所得控除
        salary_deduction = calc_salary_deduction(annual_salary)

        # 2. 基础控除
        basic_deduction = 480_000

        # 3. 社保扣除
        ss_deduction = annual_ss_employee

        # 4. 课税所得
        taxable_income = max(0, annual_salary - salary_deduction - basic_deduction - ss_deduction)

        # 5. 所得税
        income_tax = calc_income_tax_corrected(taxable_income)

        # 6. 居民税（按上一年课税所得，这里简化处理）
        resident_tax = taxable_income * 0.10

        total_tax = income_tax + resident_tax

        # 计算养老金
        pension_info = calc_pension_corrected(monthly_salary, work_years)

        # 计算总收益
        retirement_years = 20  # 假设领取20年
        total_benefit = pension_info['total_monthly'] * 12 * retirement_years

        # 计算ROI（只使用雇员缴费）
        roi = ((total_benefit / (annual_ss_employee * work_years)) - 1) * 100 if annual_ss_employee > 0 else 0

        # 计算回本年龄（只使用雇员缴费）
        break_even_years = (annual_ss_employee * work_years) / (pension_info['total_monthly'] * 12) if pension_info['total_monthly'] > 0 else 0
        break_even_age = retirement_age + break_even_years

        return {
            "monthly_pension": pension_info['total_monthly'],
            "total_contribution": annual_ss_employee * work_years,  # 只计算雇员缴费
            "total_benefit": total_benefit,
            "retirement_account_balance": annual_ss_employee * work_years,  # 简化处理
            "break_even_age": break_even_age,
            "roi": roi,
            "original_currency": "JPY",
            "details": {
                "work_years": work_years,
                "retirement_age": retirement_age,
                "annual_tax": total_tax,
                "taxable_income": taxable_income,
                "salary_deduction": salary_deduction,
                "basic_deduction": basic_deduction,
                "income_tax": income_tax,
                "resident_tax": resident_tax,
                "social_security": social_security,
                "pension_info": pension_info,
                "annual_ss_employee": annual_ss_employee,
                "annual_ss_employer": annual_ss_employer,
                "annual_ss_total": annual_ss_total
            }
        }

    def calculate_pension_result(self, person: Person, salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors) -> PensionResult:
        """计算PensionResult对象（修正版）"""
        comprehensive_result = self.calculate_comprehensive(person, salary_profile, economic_factors)

        return PensionResult(
            monthly_pension=comprehensive_result["monthly_pension"],
            total_contribution=comprehensive_result["total_contribution"],
            total_benefit=comprehensive_result["total_benefit"],
            retirement_account_balance=comprehensive_result["retirement_account_balance"],
            break_even_age=comprehensive_result["break_even_age"],
            roi=comprehensive_result["roi"],
            original_currency=comprehensive_result["original_currency"],
            details=comprehensive_result["details"]
        )

    def calculate_tax_detailed(self, annual_income: float) -> Dict[str, Any]:
        """详细计算税收（修正版）"""
        monthly_salary = annual_income / 12

        # 计算社保
        social_security = calc_social_security_corrected(monthly_salary)
        annual_ss_employee = (social_security['kosei']['employee'] +
                            social_security['kenko']['employee'] +
                            social_security['koyo']['employee']) * 12

        # 计算税收
        salary_deduction = calc_salary_deduction(annual_income)
        basic_deduction = 480_000
        ss_deduction = annual_ss_employee

        taxable_income = max(0, annual_income - salary_deduction - basic_deduction - ss_deduction)
        income_tax = calc_income_tax_corrected(taxable_income)
        resident_tax = taxable_income * 0.10
        total_tax = income_tax + resident_tax

        return {
            "total_tax": total_tax,
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "resident_tax": resident_tax,
            "effective_rate": (total_tax / annual_income * 100) if annual_income > 0 else 0,
            "net_income": annual_income - total_tax - annual_ss_employee,
            "deductions": {
                "salary_deduction": salary_deduction,
                "basic_deduction": basic_deduction,
                "ss_deduction": ss_deduction
            },
            "social_security": {
                "kosei": social_security['kosei'],
                "kenko": social_security['kenko'],
                "koyo": social_security['koyo'],
                "total_employee": annual_ss_employee
            }
        }