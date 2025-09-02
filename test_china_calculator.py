#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中国养老金计算器的新功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugins.china.china_calculator import ChinaPensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date

def test_china_calculator():
    """测试中国养老金计算器"""
    print("=== 测试中国养老金计算器 ===")
    
    # 创建计算器实例
    calculator = ChinaPensionCalculator()
    
    # 创建测试数据 - 使用正确的Person构造函数
    person = Person(
        name="张三",
        birth_date=date(1994, 1, 1),  # 30岁
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2024, 1, 1)
    )
    
    salary_profile = SalaryProfile(
        base_salary=15000,  # 月薪15000元
        annual_growth_rate=0.05  # 年增长5%
    )
    
    economic_factors = EconomicFactors(
        inflation_rate=0.02,
        social_security_return_rate=0.03,
        investment_return_rate=0.06
    )
    
    # 计算养老金
    result = calculator.calculate_pension(person, salary_profile, economic_factors)
    
    print(f"月养老金: {result.monthly_pension:.2f} 元")
    print(f"总缴费: {result.total_contribution:.2f} 元")
    print(f"总收益: {result.total_benefit:.2f} 元")
    print(f"回本年龄: {result.break_even_age} 岁")
    print(f"ROI: {result.roi:.2%}")
    
    print("\n=== 详细税收信息 ===")
    details = result.details
    print(f"个人缴费总额: {details['total_emp']:.2f} 元")
    print(f"单位缴费总额: {details['total_er']:.2f} 元")
    print(f"个人所得税: {details['total_tax']:.2f} 元")
    print(f"税后净收入: {details['net_income']:.2f} 元")
    print(f"有效税率: {details['effective_tax_rate']:.2f}%")
    print(f"月税后净收入: {details['monthly_net_income']:.2f} 元")
    print(f"社保扣除: {details['social_security_deduction']:.2f} 元")
    print(f"住房公积金扣除: {details['housing_fund_deduction']:.2f} 元")
    
    print("\n=== 养老金详细信息 ===")
    print(f"基础养老金: {details['basic_pension']:.2f} 元")
    print(f"个人账户养老金: {details['account_pension']:.2f} 元")
    print(f"个人账户余额: {details['personal_account_balance']:.2f} 元")
    print(f"替代率: {details['replacement_rate']:.2%}")
    print(f"工作年限: {details['work_years']} 年")
    print(f"退休年龄: 63 岁")

def test_tax_calculator():
    """测试税收计算器"""
    print("\n=== 测试税收计算器 ===")
    
    from plugins.china.china_tax_calculator import ChinaTaxCalculator
    
    tax_calc = ChinaTaxCalculator()
    
    # 测试不同收入水平的税收
    test_incomes = [50000, 100000, 200000, 500000]
    
    for income in test_incomes:
        print(f"\n年收入: {income:,.0f} 元")
        
        # 设置专项附加扣除
        deductions = {
            'social_security': 8000,      # 社保扣除
            'housing_fund': 14400,        # 住房公积金
            'education': 12000,           # 子女教育
            'housing': 12000,             # 住房租金/房贷利息
            'elderly': 24000,             # 赡养老人
        }
        
        tax_result = tax_calc.calculate_income_tax(income, deductions)
        
        print(f"  应纳税所得额: {tax_result['taxable_income']:,.2f} 元")
        print(f"  总扣除额: {tax_result['total_deductions']:,.2f} 元")
        print(f"  个人所得税: {tax_result['total_tax']:,.2f} 元")
        print(f"  税后净收入: {tax_calc.calculate_net_income(income, deductions):,.2f} 元")
        print(f"  有效税率: {tax_calc.calculate_effective_tax_rate(income, deductions):.2f}%")

if __name__ == "__main__":
    test_china_calculator()
    test_tax_calculator()
