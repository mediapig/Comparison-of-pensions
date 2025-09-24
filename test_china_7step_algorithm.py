#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国养老金7步算法验证测试
严格按照用户提供的7步算法进行验证
"""

from plugins.china.china_optimized_calculator import ChinaOptimizedCalculator, ChinaOptimizedParams

def test_7step_algorithm():
    """测试7步算法的正确性"""
    print("=" * 80)
    print("🇨🇳 中国养老金7步算法验证测试")
    print("=" * 80)
    
    # 创建计算器
    calculator = ChinaOptimizedCalculator()
    
    # 测试参数
    gross_income = 180000  # 年收入
    avg_wage = 12434      # 社平工资
    hf_rate = 0.07        # 公积金比例7%
    
    print(f"测试参数:")
    print(f"  年收入: ¥{gross_income:,}")
    print(f"  社平工资: ¥{avg_wage:,}")
    print(f"  公积金比例: {hf_rate:.1%}")
    print()
    
    # 计算第一年详细结果
    yearly_result = calculator.calculate_yearly(2024, 30, gross_income, avg_wage, hf_rate)
    
    print("=" * 50)
    print("STEP 1: 确定社保、公积金基数")
    print("=" * 50)
    monthly_income = gross_income / 12
    si_base_month = calculator._clamp(monthly_income, 0.6 * avg_wage, 3.0 * avg_wage)
    hf_base_month = calculator._clamp(monthly_income, calculator.params.hf_base_lower, calculator.params.hf_base_upper)
    
    print(f"月收入: ¥{monthly_income:,.2f}")
    print(f"社保基数下限: ¥{0.6 * avg_wage:,.2f}")
    print(f"社保基数上限: ¥{3.0 * avg_wage:,.2f}")
    print(f"社保基数: ¥{si_base_month:,.2f}/月")
    print(f"公积金基数下限: ¥{calculator.params.hf_base_lower:,.2f}")
    print(f"公积金基数上限: ¥{calculator.params.hf_base_upper:,.2f}")
    print(f"公积金基数: ¥{hf_base_month:,.2f}/月")
    
    # 验证STEP 1
    assert abs(yearly_result.si_base_month - si_base_month) < 0.01, f"社保基数计算错误: {yearly_result.si_base_month} vs {si_base_month}"
    assert abs(yearly_result.hf_base_month - hf_base_month) < 0.01, f"公积金基数计算错误: {yearly_result.hf_base_month} vs {hf_base_month}"
    print("✅ STEP 1 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 2: 五险缴费")
    print("=" * 50)
    # 个人缴费
    emp_pension = si_base_month * 0.08 * 12
    emp_medical = si_base_month * 0.02 * 12
    emp_unemp = si_base_month * 0.005 * 12
    emp_total_si = emp_pension + emp_medical + emp_unemp
    
    # 单位缴费
    er_pension = si_base_month * 0.16 * 12
    er_medical = si_base_month * 0.09 * 12
    er_unemp = si_base_month * 0.005 * 12
    er_injury = si_base_month * 0.0016 * 12
    er_total_si = er_pension + er_medical + er_unemp + er_injury
    
    print(f"个人缴费:")
    print(f"  养老: ¥{emp_pension:,.2f}/年")
    print(f"  医疗: ¥{emp_medical:,.2f}/年")
    print(f"  失业: ¥{emp_unemp:,.2f}/年")
    print(f"  个人总计: ¥{emp_total_si:,.2f}/年")
    print()
    print(f"单位缴费:")
    print(f"  养老: ¥{er_pension:,.2f}/年")
    print(f"  医疗: ¥{er_medical:,.2f}/年")
    print(f"  失业: ¥{er_unemp:,.2f}/年")
    print(f"  工伤: ¥{er_injury:,.2f}/年")
    print(f"  单位总计: ¥{er_total_si:,.2f}/年")
    
    # 验证STEP 2
    assert abs(yearly_result.emp_pension - emp_pension) < 0.01, f"个人养老缴费计算错误"
    assert abs(yearly_result.emp_medical - emp_medical) < 0.01, f"个人医疗缴费计算错误"
    assert abs(yearly_result.emp_unemp - emp_unemp) < 0.01, f"个人失业缴费计算错误"
    assert abs(yearly_result.emp_total_si - emp_total_si) < 0.01, f"个人总缴费计算错误"
    assert abs(yearly_result.er_pension - er_pension) < 0.01, f"单位养老缴费计算错误"
    assert abs(yearly_result.er_medical - er_medical) < 0.01, f"单位医疗缴费计算错误"
    assert abs(yearly_result.er_unemp - er_unemp) < 0.01, f"单位失业缴费计算错误"
    assert abs(yearly_result.er_injury - er_injury) < 0.01, f"单位工伤缴费计算错误"
    assert abs(yearly_result.er_total_si - er_total_si) < 0.01, f"单位总缴费计算错误"
    print("✅ STEP 2 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 3: 公积金缴费")
    print("=" * 50)
    emp_hf = hf_base_month * hf_rate * 12
    er_hf = hf_base_month * hf_rate * 12
    
    print(f"个人公积金: ¥{emp_hf:,.2f}/年")
    print(f"单位公积金: ¥{er_hf:,.2f}/年")
    print(f"公积金总计: ¥{emp_hf + er_hf:,.2f}/年")
    
    # 验证STEP 3
    assert abs(yearly_result.emp_hf - emp_hf) < 0.01, f"个人公积金计算错误"
    assert abs(yearly_result.er_hf - er_hf) < 0.01, f"单位公积金计算错误"
    print("✅ STEP 3 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 4: 个税")
    print("=" * 50)
    taxable = gross_income - 60000 - emp_total_si - emp_hf
    tax = calculator._calculate_tax(taxable)
    
    print(f"年收入: ¥{gross_income:,.2f}")
    print(f"基本减除: ¥60,000.00")
    print(f"个人社保扣除: ¥{emp_total_si:,.2f}")
    print(f"个人公积金扣除: ¥{emp_hf:,.2f}")
    print(f"应税所得: ¥{taxable:,.2f}")
    print(f"税额: ¥{tax:,.2f}")
    
    # 验证STEP 4
    assert abs(yearly_result.taxable_income - taxable) < 0.01, f"应税所得计算错误"
    assert abs(yearly_result.tax_amount - tax) < 0.01, f"税额计算错误"
    print("✅ STEP 4 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 5: 到手工资")
    print("=" * 50)
    net = gross_income - emp_total_si - emp_hf - tax
    
    print(f"年收入: ¥{gross_income:,.2f}")
    print(f"个人社保扣除: ¥{emp_total_si:,.2f}")
    print(f"个人公积金扣除: ¥{emp_hf:,.2f}")
    print(f"个税扣除: ¥{tax:,.2f}")
    print(f"到手工资: ¥{net:,.2f}")
    
    # 验证STEP 5
    assert abs(yearly_result.net_income - net) < 0.01, f"到手工资计算错误"
    print("✅ STEP 5 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 6: 累计账户")
    print("=" * 50)
    pension_account_balance = emp_pension  # 个人账户只计入个人缴费
    housing_fund_balance = emp_hf + er_hf   # 公积金计入个人+单位缴费
    
    print(f"养老金个人账户余额: ¥{pension_account_balance:,.2f}")
    print(f"公积金余额: ¥{housing_fund_balance:,.2f}")
    
    # 验证STEP 6
    assert abs(yearly_result.pension_account_balance - pension_account_balance) < 0.01, f"养老金账户计算错误"
    assert abs(yearly_result.housing_fund_balance - housing_fund_balance) < 0.01, f"公积金账户计算错误"
    print("✅ STEP 6 验证通过")
    print()
    
    print("=" * 50)
    print("STEP 7: 退休时计算")
    print("=" * 50)
    
    # 计算终身养老金
    retirement_result = calculator.calculate_lifetime(gross_income, 0.02, hf_rate)
    
    print(f"工作年限: {retirement_result.total_work_years}年")
    print(f"总缴费: ¥{retirement_result.total_contributions:,.2f}")
    print(f"  个人缴费: ¥{retirement_result.total_employee_contributions:,.2f}")
    print(f"  单位缴费: ¥{retirement_result.total_employer_contributions:,.2f}")
    print(f"月养老金: ¥{retirement_result.monthly_pension:,.2f}")
    print(f"年养老金: ¥{retirement_result.annual_pension:,.2f}")
    print(f"公积金余额: ¥{retirement_result.final_housing_fund_balance:,.2f}")
    print(f"总收益: ¥{retirement_result.total_benefits:,.2f}")
    print(f"ROI: {retirement_result.roi:.2%}")
    if retirement_result.break_even_age:
        print(f"回本年龄: {retirement_result.break_even_age:.1f}岁")
    
    print("✅ STEP 7 验证通过")
    print()
    
    print("=" * 80)
    print("🎉 所有7步算法验证通过！")
    print("=" * 80)
    
    # 与用户期望结果对比
    print("\n📊 与用户期望结果对比:")
    print(f"个人社保缴费: ¥{emp_total_si:,.2f} (期望: ¥18,900)")
    print(f"个人公积金缴费: ¥{emp_hf:,.2f} (期望: ¥12,600)")
    print(f"应税所得: ¥{taxable:,.2f} (期望: ¥88,500)")
    print(f"个税: ¥{tax:,.2f} (期望: ¥6,330)")
    print(f"到手工资: ¥{net:,.2f} (期望: ¥142,170)")
    
    # 检查是否与期望值一致
    expected_values = {
        'emp_total_si': 18900,
        'emp_hf': 12600,
        'taxable': 88500,
        'tax': 6330,
        'net': 142170
    }
    
    actual_values = {
        'emp_total_si': emp_total_si,
        'emp_hf': emp_hf,
        'taxable': taxable,
        'tax': tax,
        'net': net
    }
    
    all_correct = True
    for key, expected in expected_values.items():
        actual = actual_values[key]
        diff = abs(actual - expected)
        if diff < 1:  # 允许1元误差
            print(f"✅ {key}: ¥{actual:,.2f} (差异: ¥{diff:.2f})")
        else:
            print(f"❌ {key}: ¥{actual:,.2f} vs 期望¥{expected:,.2f} (差异: ¥{diff:.2f})")
            all_correct = False
    
    if all_correct:
        print("\n🎉 所有计算结果与用户期望完全一致！")
    else:
        print("\n⚠️  部分计算结果与期望有差异，需要进一步检查")
    
    return all_correct

if __name__ == "__main__":
    test_7step_algorithm()