#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日本计算逻辑
验证我们的计算是否与提供的函数一致
"""

import sys
sys.path.append('.')

from plugins.japan.japan_enhanced_calculator import japan_social_security_and_tax, JapanEnhancedCalculator
from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date

def test_calculation_consistency():
    """测试计算一致性"""
    print("=== 日本计算逻辑测试 ===")
    
    # 测试参数
    age_start = 30
    age_retire = 65
    salary_annual = 6_000_000  # 600万日元
    
    print(f"测试参数:")
    print(f"  开始年龄: {age_start}")
    print(f"  退休年龄: {age_retire}")
    print(f"  年收入: {salary_annual:,} 日元")
    print()
    
    # 使用原始函数
    original_result = japan_social_security_and_tax(age_start, age_retire, salary_annual)
    
    print("原始函数结果:")
    print(f"  工作年限: {original_result['work_years']} 年")
    print(f"  社保缴费总额: {original_result['social_contrib_total']:,.0f} 日元")
    print(f"  年税收: {original_result['annual_tax']:,.0f} 日元")
    print(f"  月退休金: {original_result['monthly_pension']:,.0f} 日元")
    print()
    
    # 使用我们的增强计算器
    calculator = JapanEnhancedCalculator()
    
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
        contribution_start_age=age_start
    )
    
    economic_factors = EconomicFactors(
        inflation_rate=0.02,
        investment_return_rate=0.05,
        social_security_return_rate=0.03
    )
    
    # 计算综合结果
    comprehensive_result = calculator.calculate_comprehensive(person, salary_profile, economic_factors)
    
    print("增强计算器结果:")
    print(f"  月退休金: {comprehensive_result['monthly_pension']:,.0f} 日元")
    print(f"  总缴费: {comprehensive_result['total_contribution']:,.0f} 日元")
    print(f"  总收益: {comprehensive_result['total_benefit']:,.0f} 日元")
    print(f"  ROI: {comprehensive_result['roi']:.1f}%")
    print(f"  回本年龄: {comprehensive_result['break_even_age']:.1f} 岁")
    print()
    
    # 计算税收
    tax_result = calculator.calculate_tax_detailed(salary_annual)
    
    print("税收详细结果:")
    print(f"  应税收入: {tax_result['taxable_income']:,.0f} 日元")
    print(f"  所得税: {tax_result['income_tax']:,.0f} 日元")
    print(f"  居民税: {tax_result['resident_tax']:,.0f} 日元")
    print(f"  总税收: {tax_result['total_tax']:,.0f} 日元")
    print(f"  有效税率: {tax_result['effective_rate']:.1f}%")
    print(f"  净收入: {tax_result['net_income']:,.0f} 日元")
    print()
    
    # 社保详细结果
    social_security = tax_result['social_security']
    print("社保详细结果:")
    print(f"  厚生年金: {social_security['kosei']:,.0f} 日元/年")
    print(f"  健康保险: {social_security['kenko']:,.0f} 日元/年")
    print(f"  雇用保险: {social_security['koyo']:,.0f} 日元/年")
    print(f"  社保总计: {social_security['total']:,.0f} 日元/年")
    print()
    
    # 对比分析
    print("=== 对比分析 ===")
    print(f"月退休金差异: {abs(comprehensive_result['monthly_pension'] - original_result['monthly_pension']):,.0f} 日元")
    print(f"社保缴费差异: {abs(comprehensive_result['total_contribution'] - original_result['social_contrib_total']):,.0f} 日元")
    print(f"税收差异: {abs(tax_result['total_tax'] - original_result['annual_tax']):,.0f} 日元")
    
    # 计算差异百分比
    pension_diff_pct = abs(comprehensive_result['monthly_pension'] - original_result['monthly_pension']) / original_result['monthly_pension'] * 100
    social_diff_pct = abs(comprehensive_result['total_contribution'] - original_result['social_contrib_total']) / original_result['social_contrib_total'] * 100
    tax_diff_pct = abs(tax_result['total_tax'] - original_result['annual_tax']) / original_result['annual_tax'] * 100
    
    print(f"月退休金差异百分比: {pension_diff_pct:.2f}%")
    print(f"社保缴费差异百分比: {social_diff_pct:.2f}%")
    print(f"税收差异百分比: {tax_diff_pct:.2f}%")

if __name__ == "__main__":
    test_calculation_consistency()