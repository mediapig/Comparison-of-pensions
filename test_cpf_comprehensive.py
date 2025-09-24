#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CPF综合引擎与现有系统的集成
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from core.models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType
from datetime import date
from plugins.singapore.plugin_comprehensive import SingaporeComprehensivePlugin


def test_cpf_comprehensive_integration():
    """测试CPF综合引擎集成"""
    print("=" * 60)
    print("测试CPF综合引擎集成")
    print("=" * 60)
    
    # 创建测试数据
    person = Person(
        name="Test Person",
        birth_date=date(1994, 1, 1),  # 30岁
        gender=Gender.MALE,
        employment_type=EmploymentType.EMPLOYEE,
        start_work_date=date(2024, 1, 1)
    )
    
    salary_profile = SalaryProfile(
        monthly_salary=15000,  # 月薪15,000 SGD
        annual_growth_rate=0.02,
        contribution_start_age=30
    )
    
    economic_factors = EconomicFactors(
        inflation_rate=0.02,
        investment_return_rate=0.04,
        social_security_return_rate=0.04
    )
    
    # 创建插件
    plugin = SingaporeComprehensivePlugin()
    
    # 计算退休金
    result = plugin.calculate_pension(person, salary_profile, economic_factors)
    
    # 显示结果
    print(f"月退休金: ${result.monthly_pension:,.2f}")
    print(f"总缴费: ${result.total_contribution:,.2f}")
    print(f"总收益: ${result.total_benefit:,.2f}")
    print(f"回本年龄: {result.break_even_age}")
    print(f"ROI: {result.roi:.2f}%")
    
    # 显示详细信息
    details = result.details
    print(f"\n工作年限: {details['work_years']}年")
    print(f"退休年龄: {details['retirement_age']}岁")
    
    # CPF账户余额
    accounts_65 = details['cpf_accounts_at_65']
    print(f"\n65岁账户余额:")
    print(f"  OA: ${accounts_65['oa_balance']:,.2f}")
    print(f"  SA: ${accounts_65['sa_balance']:,.2f}")
    print(f"  RA: ${accounts_65['ra_balance']:,.2f}")
    print(f"  MA: ${accounts_65['ma_balance']:,.2f}")
    
    # CPF LIFE分析
    cpf_life = details['cpf_life_analysis']
    print(f"\nCPF LIFE分析:")
    print(f"  计划: {cpf_life['plan']}")
    print(f"  月支付: ${cpf_life['monthly_payout']:,.2f}")
    print(f"  总支付: ${cpf_life['total_payout']:,.2f}")
    print(f"  最终余额: ${cpf_life['final_balance']:,.2f}")
    print(f"  80岁遗赠: ${cpf_life['bequest_at_80']:,.2f}")
    print(f"  支付效率: {cpf_life['payout_efficiency']:.2%}")
    
    # 财务分析
    financial = details['financial_analysis']
    print(f"\n财务分析:")
    print(f"  雇员缴费: ${financial['total_employee_contributions']:,.2f}")
    print(f"  雇主缴费: ${financial['total_employer_contributions']:,.2f}")
    print(f"  总缴费: ${financial['total_contributions']:,.2f}")
    print(f"  总收益: ${financial['total_benefits']:,.2f}")
    print(f"  终值: ${financial['terminal_value']:,.2f}")
    print(f"  个人IRR: {financial['personal_irr']:.2%}" if financial['personal_irr'] else "个人IRR: N/A")
    
    # 验证结果
    validation = details['validation']
    print(f"\n验证结果:")
    print(f"  验证通过: {validation['passed']}")
    if validation['errors']:
        print("  错误:")
        for error in validation['errors']:
            print(f"    - {error}")
    
    return result


def test_cpf_life_plans():
    """测试CPF LIFE计划比较"""
    print("\n" + "=" * 60)
    print("测试CPF LIFE计划比较")
    print("=" * 60)
    
    plugin = SingaporeComprehensivePlugin()
    
    # 测试不同RA余额的计划比较
    ra_balances = [500000, 750000, 1000000]
    
    for ra_balance in ra_balances:
        print(f"\nRA65余额: ${ra_balance:,}")
        
        # 比较计划
        plans = plugin.compare_cpf_life_plans(ra_balance)
        
        for plan, result in plans.items():
            print(f"  {plan.upper()}计划:")
            print(f"    首月退休金: ${result.monthly_payouts[0]:,.2f}")
            print(f"    总退休金: ${result.total_payout:,.2f}")
            print(f"    最终余额: ${result.final_balance:,.2f}")
            print(f"    80岁遗赠: ${result.bequest_at_80:,.2f}")


def test_sensitivity_analysis():
    """测试敏感性分析"""
    print("\n" + "=" * 60)
    print("测试敏感性分析")
    print("=" * 60)
    
    plugin = SingaporeComprehensivePlugin()
    
    # 运行敏感性分析
    sensitivity = plugin.run_sensitivity_analysis(
        start_age=30,
        retirement_age=65,
        end_age=90,
        annual_salary=180000,
        salary_growth_rate=0.02,
        ra_target_type="FRS",
        cpf_life_plan="standard"
    )
    
    print("起始年龄敏感性:")
    for age, data in sensitivity['start_age_sensitivity'].items():
        print(f"  {age}岁开始: 月退休金 ${data['monthly_pension']:,.0f}, IRR {data['personal_irr']:.1%}" if data['personal_irr'] else f"  {age}岁开始: 月退休金 ${data['monthly_pension']:,.0f}, IRR N/A")
    
    print("\n薪资水平敏感性:")
    for salary, data in sensitivity['salary_sensitivity'].items():
        print(f"  年薪 ${salary:,}: 月退休金 ${data['monthly_pension']:,.0f}, IRR {data['personal_irr']:.1%}" if data['personal_irr'] else f"  年薪 ${salary:,}: 月退休金 ${data['monthly_pension']:,.0f}, IRR N/A")


def main():
    """主函数"""
    # 测试集成
    result = test_cpf_comprehensive_integration()
    
    # 测试CPF LIFE计划
    test_cpf_life_plans()
    
    # 测试敏感性分析
    test_sensitivity_analysis()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()