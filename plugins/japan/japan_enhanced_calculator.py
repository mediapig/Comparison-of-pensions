#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本增强计算器
基于更准确的日本社保和税收政策
"""

from typing import Dict, Any, Optional
from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, Gender, EmploymentType

def calc_income_tax(taxable_income: float) -> float:
    """计算日本所得税（简化版）"""
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

def japan_social_security_and_tax(age_start: int = 30, age_retire: int = 65, salary_annual: float = 6_000_000) -> Dict[str, Any]:
    """
    计算日本社保和税收
    
    Args:
        age_start: 开始工作年龄
        age_retire: 退休年龄
        salary_annual: 年收入（日元）
        
    Returns:
        计算结果字典
    """
    years = age_retire - age_start
    salary_monthly = salary_annual / 12

    # === 社保 ===
    # 厚生年金 (18.3% split)
    kosei_annual = min(salary_monthly, 650_000) * 12 * 0.183
    # 健康保険 (10% split)
    kenko_annual = min(salary_monthly, 1_390_000) * 12 * 0.10
    # 雇用保険 (0.9%)
    koyo_annual = salary_annual * 0.009
    # 合计（员工+雇主）
    social_total = (kosei_annual + kenko_annual + koyo_annual) * years

    # === 税务 ===
    taxable_income = salary_annual - (kosei_annual + kenko_annual + koyo_annual)  # 社保扣除
    tax = calc_income_tax(taxable_income) + taxable_income * 0.10  # 所得税 + 居民税

    # === 养老金 ===
    kokumin_pension_month = 66_250  # 固定值
    kosei_pension_month = (min(salary_monthly, 650_000) * 5.481/1000 * years*12) / 12
    total_pension_month = kokumin_pension_month + kosei_pension_month

    return {
        "work_years": years,
        "social_contrib_total": social_total,
        "annual_tax": tax,
        "monthly_pension": total_pension_month,
        "details": {
            "kosei_annual": kosei_annual,
            "kenko_annual": kenko_annual,
            "koyo_annual": koyo_annual,
            "kokumin_pension_month": kokumin_pension_month,
            "kosei_pension_month": kosei_pension_month,
            "taxable_income": taxable_income
        }
    }

class JapanEnhancedCalculator:
    """日本增强计算器"""
    
    def __init__(self):
        self.country_code = 'JP'
        self.country_name = '日本'
        self.currency = 'JPY'
    
    def calculate_comprehensive(self, person: Person, salary_profile: SalaryProfile, 
                              economic_factors: EconomicFactors) -> Dict[str, Any]:
        """综合计算日本养老金、税收、社保"""
        
        # 获取基本参数
        monthly_salary = salary_profile.monthly_salary
        annual_salary = monthly_salary * 12
        work_years = person.work_years if person.work_years > 0 else 35
        retirement_age = 65
        
        # 使用增强计算函数
        result = japan_social_security_and_tax(
            age_start=person.age,
            age_retire=retirement_age,
            salary_annual=annual_salary
        )
        
        # 计算总收益
        retirement_years = 20  # 假设领取20年
        total_benefit = result["monthly_pension"] * 12 * retirement_years
        
        # 计算ROI
        roi = ((total_benefit / result["social_contrib_total"]) - 1) * 100 if result["social_contrib_total"] > 0 else 0
        
        # 计算回本年龄
        break_even_years = result["social_contrib_total"] / (result["monthly_pension"] * 12) if result["monthly_pension"] > 0 else 0
        break_even_age = retirement_age + break_even_years
        
        return {
            "monthly_pension": result["monthly_pension"],
            "total_contribution": result["social_contrib_total"],
            "total_benefit": total_benefit,
            "retirement_account_balance": result["social_contrib_total"],  # 简化处理
            "break_even_age": break_even_age,
            "roi": roi,
            "original_currency": "JPY",
            "details": {
                "work_years": work_years,
                "retirement_age": retirement_age,
                "annual_tax": result["annual_tax"],
                "social_security_breakdown": result["details"]
            }
        }
    
    def calculate_pension_result(self, person: Person, salary_profile: SalaryProfile, 
                               economic_factors: EconomicFactors) -> PensionResult:
        """计算PensionResult对象"""
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
        """详细计算税收"""
        # 计算社保
        monthly_salary = annual_income / 12
        kosei_annual = min(monthly_salary, 650_000) * 12 * 0.183
        kenko_annual = min(monthly_salary, 1_390_000) * 12 * 0.10
        koyo_annual = annual_income * 0.009
        
        # 计算应税收入
        taxable_income = annual_income - (kosei_annual + kenko_annual + koyo_annual)
        
        # 计算税收
        income_tax = calc_income_tax(taxable_income)
        resident_tax = taxable_income * 0.10
        total_tax = income_tax + resident_tax
        
        return {
            "total_tax": total_tax,
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "resident_tax": resident_tax,
            "effective_rate": (total_tax / annual_income * 100) if annual_income > 0 else 0,
            "net_income": annual_income - total_tax,
            "social_security": {
                "kosei": kosei_annual,
                "kenko": kenko_annual,
                "koyo": koyo_annual,
                "total": kosei_annual + kenko_annual + koyo_annual
            }
        }