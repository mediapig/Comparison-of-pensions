#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common utilities for pension analysis system
"""

from datetime import date
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from utils.smart_currency_converter import smart_converter

# Initialize currency converter
converter = smart_converter

def create_standard_person() -> Person:
    """Create standard person for analysis"""
    return Person(
        name="测试用户",
        birth_date=date(1990, 1, 1),
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(1990, 7, 1)  # 1990年开始工作，工作到2025年，正好35年
    )

def create_standard_salary_profile(monthly_salary: float, growth_rate: float = 0.00) -> SalaryProfile:
    """Create standard salary profile"""
    return SalaryProfile(
        monthly_salary=monthly_salary,
        annual_growth_rate=growth_rate,
        contribution_start_age=30,
        base_salary=monthly_salary
    )

def create_standard_economic_factors(base_currency: str = "CNY", display_currency: str = None) -> EconomicFactors:
    """Create standard economic factors"""
    return EconomicFactors(
        inflation_rate=0.03,
        investment_return_rate=0.07,
        social_security_return_rate=0.05,
        base_currency=base_currency,
        display_currency=display_currency or base_currency
    )

def print_analysis_header(country_flag: str, country_name: str, scenario_name: str, monthly_salary: float, description: str = ""):
    """Print standardized analysis header"""
    print(f"\n{'='*80}")
    print(f"{country_flag} {country_name}养老金详细分析 - {scenario_name}")
    if description:
        print(description)
    print(f"月薪: {converter.format_amount(monthly_salary, 'CNY')}")
    print(f"工作年限: 35年")
    print(f"退休年龄: 65岁")
    print(f"领取年限: 20年")
    print(f"{'='*80}")

def print_section_header(title: str):
    """Print section header"""
    print(f"\n{title}")
    print("-" * 50)

def print_completion_message(scenario_name: str):
    """Print completion message"""
    print(f"\n{'='*80}")
    print(f"✅ {scenario_name}分析完成")
    print(f"{'='*80}")

def get_country_currency(country_code: str) -> str:
    """Get currency code for a country"""
    currency_map = {
        'CN': 'CNY',
        'US': 'USD',
        'TW': 'TWD',
        'HK': 'HKD',
        'SG': 'SGD',
        'JP': 'JPY',
        'UK': 'GBP',
        'AU': 'AUD',
        'CA': 'CAD'
    }
    return currency_map.get(country_code, 'CNY')