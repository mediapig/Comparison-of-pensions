#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日本修正计算逻辑
验证修正后的计算是否更准确
"""

import sys
sys.path.append('.')

from plugins.japan.japan_corrected_calculator import JapanCorrectedCalculator, calc_salary_deduction, calc_social_security_corrected
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date

def test_corrected_calculations():
    """测试修正后的计算"""
    print("=== 日本修正计算逻辑测试 ===")
    
    # 测试参数
    test_cases = [
        {"salary": 500_000, "name": "低收入"},
        {"salary": 5_000_000, "name": "中等收入"},
        {"salary": 20_000_000, "name": "高收入"}
    ]
    
    calculator = JapanCorrectedCalculator()
    
    for case in test_cases:
        salary_annual = case["salary"]
        print(f"\n--- {case['name']}测试 (年收入: {salary_annual:,} 日元) ---")
        
        # 创建测试数据
        person = Person(
            name="测试用户",
            birth_date=date(1994, 1, 1),  # 30岁
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(2024, 1, 1)
        )
        
        salary_profile = SalaryProfile(
            monthly_salary=salary_annual / 12,
            annual_growth_rate=0.0,
            contribution_start_age=30
        )
        
        economic_factors = EconomicFactors(
            inflation_rate=0.02,
            investment_return_rate=0.05,
            social_security_return_rate=0.03
        )
        
        # 计算综合结果
        comprehensive_result = calculator.calculate_comprehensive(person, salary_profile, economic_factors)
        
        print(f"月退休金: {comprehensive_result['monthly_pension']:,.0f} 日元")
        print(f"总缴费(雇员): {comprehensive_result['total_contribution']:,.0f} 日元")
        print(f"ROI: {comprehensive_result['roi']:.1f}%")
        print(f"回本年龄: {comprehensive_result['break_even_age']:.1f} 岁")
        
        # 计算税收
        tax_result = calculator.calculate_tax_detailed(salary_annual)
        
        print(f"应税收入: {tax_result['taxable_income']:,.0f} 日元")
        print(f"所得税: {tax_result['income_tax']:,.0f} 日元")
        print(f"居民税: {tax_result['resident_tax']:,.0f} 日元")
        print(f"总税收: {tax_result['total_tax']:,.0f} 日元")
        print(f"有效税率: {tax_result['effective_rate']:.1f}%")
        
        # 社保详细结果
        social_security = tax_result['social_security']
        print(f"厚生年金(员工): {social_security['kosei']['employee']:,.0f} 日元/月")
        print(f"健康保险(员工): {social_security['kenko']['employee']:,.0f} 日元/月")
        print(f"雇用保险(员工): {social_security['koyo']['employee']:,.0f} 日元/月")
        print(f"社保总计(员工): {social_security['total_employee']:,.0f} 日元/年")
        
        # 扣除项详细
        deductions = tax_result['deductions']
        print(f"工资所得控除: {deductions['salary_deduction']:,.0f} 日元")
        print(f"基础控除: {deductions['basic_deduction']:,.0f} 日元")
        print(f"社保扣除: {deductions['ss_deduction']:,.0f} 日元")

def test_salary_deduction():
    """测试工资所得控除"""
    print("\n=== 工资所得控除测试 ===")
    
    test_salaries = [500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000]
    
    for salary in test_salaries:
        deduction = calc_salary_deduction(salary)
        print(f"年收入 {salary:>8,} 日元 → 工资所得控除 {deduction:>8,} 日元")

def test_social_security_limits():
    """测试社保上限"""
    print("\n=== 社保上限测试 ===")
    
    test_salaries = [500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000]
    
    for salary in test_salaries:
        monthly_salary = salary / 12
        ss = calc_social_security_corrected(monthly_salary)
        
        print(f"月薪 {monthly_salary:>8,.0f} 日元:")
        print(f"  厚生年金基数: {ss['kosei']['base']:>8,.0f} 日元 (上限65万)")
        print(f"  健康保险基数: {ss['kenko']['base']:>8,.0f} 日元 (上限139万)")
        print(f"  厚生年金(员工): {ss['kosei']['employee']:>8,.0f} 日元/月")
        print(f"  健康保险(员工): {ss['kenko']['employee']:>8,.0f} 日元/月")
        print(f"  雇用保险(员工): {ss['koyo']['employee']:>8,.0f} 日元/月")
        print()

if __name__ == "__main__":
    test_corrected_calculations()
    test_salary_deduction()
    test_social_security_limits()