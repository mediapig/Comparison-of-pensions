#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPF综合引擎演示和测试脚本
验证所有CPF规则的正确实现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from cpf_comprehensive_engine import (
    CPFComprehensiveEngine, CPFParameters, CPFComprehensiveResult,
    run_cpf_simulation, compare_cpf_life_plans, create_default_parameters
)
import json
from typing import Dict, List, Any


class CPFDemoRunner:
    """CPF演示运行器"""
    
    def __init__(self):
        self.results = {}
    
    def run_basic_demo(self):
        """运行基础演示"""
        print("=" * 80)
        print("CPF综合引擎 - 基础演示")
        print("=" * 80)
        
        # 基础参数
        params = create_default_parameters(
            start_age=30,
            retirement_age=65,
            end_age=90,
            annual_salary=180000,
            salary_growth_rate=0.02,
            ra_target_type="FRS",
            cpf_life_plan="standard"
        )
        
        engine = CPFComprehensiveEngine(params)
        result = engine.run_comprehensive_simulation()
        
        self.results['basic'] = result
        
        # 显示结果
        self._display_basic_results(result)
        
        return result
    
    def run_ra_target_comparison(self):
        """运行RA目标比较"""
        print("\n" + "=" * 80)
        print("RA目标比较 (FRS vs ERS vs BRS)")
        print("=" * 80)
        
        ra_targets = ["FRS", "ERS", "BRS"]
        ra_results = {}
        
        for target in ra_targets:
            params = create_default_parameters(
                start_age=30,
                retirement_age=65,
                end_age=90,
                annual_salary=180000,
                salary_growth_rate=0.02,
                ra_target_type=target,
                cpf_life_plan="standard"
            )
            
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            ra_results[target] = result
            
            print(f"\n{target}目标:")
            print(f"  55岁RA建立: ${result.ra_established_at_55:,.2f}")
            print(f"  55岁OA剩余: ${result.oa_remaining_at_55:,.2f}")
            print(f"  55岁提取现金: ${result.cash_withdrawn_at_55:,.2f}")
            print(f"  65岁RA余额: ${result.ra_balance_at_65:,.2f}")
            print(f"  月退休金: ${result.cpf_life_result.monthly_payouts[0]:,.2f}")
            print(f"  总退休金: ${result.cpf_life_result.total_payout:,.2f}")
            print(f"  个人IRR: {result.personal_irr:.2%}" if result.personal_irr else "个人IRR: N/A")
        
        self.results['ra_targets'] = ra_results
        return ra_results
    
    def run_cpf_life_plan_comparison(self):
        """运行CPF LIFE计划比较"""
        print("\n" + "=" * 80)
        print("CPF LIFE计划比较 (Standard vs Escalating vs Basic)")
        print("=" * 80)
        
        # 使用FRS目标进行计划比较
        params = create_default_parameters(
            start_age=30,
            retirement_age=65,
            end_age=90,
            annual_salary=180000,
            salary_growth_rate=0.02,
            ra_target_type="FRS"
        )
        
        engine = CPFComprehensiveEngine(params)
        result = engine.run_comprehensive_simulation()
        
        # 比较不同计划
        plan_comparison = engine.compare_plans(result.ra_balance_at_65)
        
        print(f"RA65余额: ${result.ra_balance_at_65:,.2f}")
        print("\n计划比较:")
        
        for plan, plan_result in plan_comparison.items():
            print(f"\n{plan.upper()}计划:")
            print(f"  首月退休金: ${plan_result.monthly_payouts[0]:,.2f}")
            print(f"  总退休金: ${plan_result.total_payout:,.2f}")
            print(f"  最终余额: ${plan_result.final_balance:,.2f}")
            print(f"  80岁遗赠: ${plan_result.bequest_at_80:,.2f}")
            print(f"  90岁遗赠: ${plan_result.bequest_at_90:,.2f}")
            print(f"  支付效率: {plan_result.payout_efficiency:.2%}")
        
        self.results['cpf_life_plans'] = plan_comparison
        return plan_comparison
    
    def run_bequest_analysis(self):
        """运行遗赠分析"""
        print("\n" + "=" * 80)
        print("遗赠情景分析")
        print("=" * 80)
        
        params = create_default_parameters(
            start_age=30,
            retirement_age=65,
            end_age=90,
            annual_salary=180000,
            salary_growth_rate=0.02,
            ra_target_type="FRS"
        )
        
        engine = CPFComprehensiveEngine(params)
        result = engine.run_comprehensive_simulation()
        
        death_ages = [70, 75, 80, 85, 90, 95, 100]
        plans = ["standard", "escalating", "basic"]
        
        print(f"RA65余额: ${result.ra_balance_at_65:,.2f}")
        
        for plan in plans:
            print(f"\n{plan.upper()}计划遗赠分析:")
            bequest_scenarios = engine.analyze_bequest_scenarios(
                result.ra_balance_at_65, plan, death_ages
            )
            
            for death_age, bequest in bequest_scenarios.items():
                print(f"  {death_age}岁去世: ${bequest:,.2f}")
        
        self.results['bequest_analysis'] = {
            'ra65_balance': result.ra_balance_at_65,
            'death_ages': death_ages,
            'plans': plans
        }
    
    def run_sensitivity_analysis(self):
        """运行敏感性分析"""
        print("\n" + "=" * 80)
        print("敏感性分析")
        print("=" * 80)
        
        # 起始年龄敏感性
        print("\n起始年龄敏感性:")
        start_ages = [25, 30, 35, 40]
        for start_age in start_ages:
            params = create_default_parameters(
                start_age=start_age,
                retirement_age=65,
                end_age=90,
                annual_salary=180000,
                salary_growth_rate=0.02,
                ra_target_type="FRS",
                cpf_life_plan="standard"
            )
            
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            
            print(f"  {start_age}岁开始: 月退休金 ${result.cpf_life_result.monthly_payouts[0]:,.0f}, "
                  f"IRR {result.personal_irr:.1%}" if result.personal_irr else "IRR N/A")
        
        # 薪资水平敏感性
        print("\n薪资水平敏感性:")
        salaries = [120000, 180000, 240000, 300000]
        for salary in salaries:
            params = create_default_parameters(
                start_age=30,
                retirement_age=65,
                end_age=90,
                annual_salary=salary,
                salary_growth_rate=0.02,
                ra_target_type="FRS",
                cpf_life_plan="standard"
            )
            
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            
            print(f"  年薪 ${salary:,}: 月退休金 ${result.cpf_life_result.monthly_payouts[0]:,.0f}, "
                  f"IRR {result.personal_irr:.1%}" if result.personal_irr else "IRR N/A")
        
        # 薪资增长敏感性
        print("\n薪资增长敏感性:")
        growth_rates = [0.0, 0.02, 0.03, 0.04]
        for growth in growth_rates:
            params = create_default_parameters(
                start_age=30,
                retirement_age=65,
                end_age=90,
                annual_salary=180000,
                salary_growth_rate=growth,
                ra_target_type="FRS",
                cpf_life_plan="standard"
            )
            
            engine = CPFComprehensiveEngine(params)
            result = engine.run_comprehensive_simulation()
            
            print(f"  增长 {growth:.0%}: 月退休金 ${result.cpf_life_result.monthly_payouts[0]:,.0f}, "
                  f"IRR {result.personal_irr:.1%}" if result.personal_irr else "IRR N/A")
    
    def run_validation_tests(self):
        """运行验证测试"""
        print("\n" + "=" * 80)
        print("验证测试")
        print("=" * 80)
        
        # 测试1: MA余额不超过BHS
        print("\n测试1: MA余额不超过BHS")
        params = create_default_parameters(
            start_age=30,
            retirement_age=65,
            end_age=90,
            annual_salary=300000,  # 高薪资测试MA上限
            salary_growth_rate=0.02,
            ra_target_type="FRS",
            cpf_life_plan="standard"
        )
        
        engine = CPFComprehensiveEngine(params)
        result = engine.run_comprehensive_simulation()
        
        ma_violations = []
        for yr in result.yearly_results:
            if yr.ma_balance > yr.bhs_limit + 1e-6:
                ma_violations.append(f"年龄{yr.age}: MA余额{yr.ma_balance:.2f} > BHS限制{yr.bhs_limit:.2f}")
        
        if ma_violations:
            print("  ❌ MA余额超过BHS限制:")
            for violation in ma_violations:
                print(f"    - {violation}")
        else:
            print("  ✅ MA余额始终在BHS限制内")
        
        # 测试2: 账户余额非负
        print("\n测试2: 账户余额非负")
        negative_balances = []
        for yr in result.yearly_results:
            if yr.oa_balance < -1e-6:
                negative_balances.append(f"年龄{yr.age}: OA余额{yr.oa_balance:.2f}")
            if yr.sa_balance < -1e-6:
                negative_balances.append(f"年龄{yr.age}: SA余额{yr.sa_balance:.2f}")
            if yr.ma_balance < -1e-6:
                negative_balances.append(f"年龄{yr.age}: MA余额{yr.ma_balance:.2f}")
            if yr.ra_balance < -1e-6:
                negative_balances.append(f"年龄{yr.age}: RA余额{yr.ra_balance:.2f}")
        
        if negative_balances:
            print("  ❌ 发现负余额:")
            for balance in negative_balances:
                print(f"    - {balance}")
        else:
            print("  ✅ 所有账户余额均为非负")
        
        # 测试3: 现金流平衡
        print("\n测试3: 现金流平衡")
        total_contributions = sum(yr.total_contrib for yr in result.yearly_results)
        if abs(total_contributions - result.total_contributions) < 1e-6:
            print("  ✅ 现金流平衡验证通过")
        else:
            print(f"  ❌ 现金流不平衡: 计算{total_contributions:.2f} vs 存储{result.total_contributions:.2f}")
        
        # 测试4: 验证结果
        print("\n测试4: 整体验证")
        if result.validation_passed:
            print("  ✅ 整体验证通过")
        else:
            print("  ❌ 整体验证失败:")
            for error in result.validation_errors:
                print(f"    - {error}")
    
    def run_optimal_plan_analysis(self):
        """运行最优计划分析"""
        print("\n" + "=" * 80)
        print("最优计划分析")
        print("=" * 80)
        
        params = create_default_parameters(
            start_age=30,
            retirement_age=65,
            end_age=90,
            annual_salary=180000,
            salary_growth_rate=0.02,
            ra_target_type="FRS"
        )
        
        engine = CPFComprehensiveEngine(params)
        result = engine.run_comprehensive_simulation()
        
        # 不同偏好下的最优计划
        preferences_scenarios = [
            {
                'name': '收入导向',
                'preferences': {'income_weight': 0.6, 'bequest_weight': 0.2, 'stability_weight': 0.2}
            },
            {
                'name': '遗赠导向',
                'preferences': {'income_weight': 0.2, 'bequest_weight': 0.6, 'stability_weight': 0.2}
            },
            {
                'name': '平衡导向',
                'preferences': {'income_weight': 0.4, 'bequest_weight': 0.3, 'stability_weight': 0.3}
            }
        ]
        
        for scenario in preferences_scenarios:
            print(f"\n{scenario['name']}:")
            optimal_analysis = engine.calculate_optimal_plan(
                result.ra_balance_at_65, scenario['preferences']
            )
            
            print(f"  推荐计划: {optimal_analysis['optimal_plan']}")
            print(f"  推荐理由: {optimal_analysis['recommendation']}")
            print("  各计划评分:")
            for plan, score in optimal_analysis['scores'].items():
                print(f"    {plan}: {score:.3f}")
    
    def _display_basic_results(self, result: CPFComprehensiveResult):
        """显示基础结果"""
        print(f"工作年限: {result.work_years}年")
        print(f"退休年限: {result.retirement_years}年")
        print(f"总缴费: ${result.total_contributions:,.2f}")
        print(f"  - 雇员缴费: ${result.total_employee_contributions:,.2f}")
        print(f"  - 雇主缴费: ${result.total_employer_contributions:,.2f}")
        print(f"总收益: ${result.total_benefits:,.2f}")
        print(f"  - 退休金: ${result.cpf_life_result.total_payout:,.2f}")
        print(f"  - 终值: ${result.terminal_value:,.2f}")
        print(f"月退休金: ${result.cpf_life_result.monthly_payouts[0]:,.2f}")
        print(f"个人IRR: {result.personal_irr:.2%}" if result.personal_irr else "个人IRR: N/A")
        print(f"验证通过: {result.validation_passed}")
        
        if result.validation_errors:
            print("验证错误:")
            for error in result.validation_errors:
                print(f"  - {error}")
    
    def export_results(self, filename: str = "cpf_comprehensive_results.json"):
        """导出结果到JSON文件"""
        export_data = {}
        
        for key, result in self.results.items():
            if isinstance(result, CPFComprehensiveResult):
                export_data[key] = {
                    'work_years': result.work_years,
                    'retirement_years': result.retirement_years,
                    'total_contributions': result.total_contributions,
                    'total_benefits': result.total_benefits,
                    'monthly_pension': result.cpf_life_result.monthly_payouts[0],
                    'total_pension': result.cpf_life_result.total_payout,
                    'terminal_value': result.terminal_value,
                    'personal_irr': result.personal_irr,
                    'validation_passed': result.validation_passed
                }
            else:
                export_data[key] = result
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n结果已导出到: {filename}")


def main():
    """主函数"""
    demo = CPFDemoRunner()
    
    # 运行所有演示
    demo.run_basic_demo()
    demo.run_ra_target_comparison()
    demo.run_cpf_life_plan_comparison()
    demo.run_bequest_analysis()
    demo.run_sensitivity_analysis()
    demo.run_validation_tests()
    demo.run_optimal_plan_analysis()
    
    # 导出结果
    demo.export_results()
    
    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()