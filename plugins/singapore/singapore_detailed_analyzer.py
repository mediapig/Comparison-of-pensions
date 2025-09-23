#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡详细分析器
提供详细的CPF分析输出
"""

from typing import Dict, Any
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount


class SingaporeDetailedAnalyzer:
    """新加坡详细分析器"""

    def __init__(self):
        self.smart_converter = SmartCurrencyConverter()

    def print_detailed_analysis(self, 
                               plugin,
                               person: Person,
                               salary_profile: SalaryProfile,
                               economic_factors: EconomicFactors,
                               pension_result: PensionResult,
                               local_amount: CurrencyAmount):
        """打印详细的新加坡CPF分析"""
        
        # 显示详细的第一年分析
        print(f"\n=== 第一年 (30岁) ===")
        print(f"年收入: {plugin.format_currency(local_amount.amount)}")
        print(f"CPF缴费基数: {plugin.format_currency(min(local_amount.amount, 102000))} (受年薪上限限制)")
        print(f"雇员费率: 20.0%")
        print(f"雇主费率: 17.0%")
        print(f"总费率: 37.0%")
        print(f"年缴费金额: {plugin.format_currency(min(local_amount.amount, 102000) * 0.37)}")
        print(f"雇员CPF缴费: {plugin.format_currency(min(local_amount.amount, 102000) * 0.20)}")
        print(f"雇主CPF缴费: {plugin.format_currency(min(local_amount.amount, 102000) * 0.17)}")
        
        print(f"\nCPF分配 (基于工资基数):")
        base = min(local_amount.amount, 102000)
        print(f"  OA (普通账户): {plugin.format_currency(base * 0.23)} (23.0% of base)")
        print(f"  SA (特别账户): {plugin.format_currency(base * 0.06)} (6.0% of base)")
        print(f"  MA (医疗账户): {plugin.format_currency(base * 0.08)} (8.0% of base)")

        # 计算税收
        annual_income = local_amount.amount
        taxable_income = annual_income - (base * 0.20)  # 减去雇员CPF缴费
        tax_result = plugin.calculate_tax(taxable_income)  # 使用应税收入计算税款
        print(f"\n应税收入: {plugin.format_currency(taxable_income)}")
        print(f"所得税 (累进税率): {plugin.format_currency(tax_result.get('total_tax', 0))}")
        print(f"实际到手收入: {plugin.format_currency(taxable_income - tax_result.get('total_tax', 0))}")

        # 显示35年工作期总计
        print(f"\n=== 35年工作期总计 (30-64岁) ===")
        
        # 计算CPF缴费基数（考虑年薪上限）
        cpf_base = min(annual_income, 102000)
        
        # CPF缴费是固定的，不随工资增长而变化（除非工资超过上限）
        annual_cpf_total = cpf_base * 0.37
        annual_cpf_employee = cpf_base * 0.20
        annual_cpf_employer = cpf_base * 0.17
        
        # 35年总缴费（不含利息）
        total_cpf_employee = annual_cpf_employee * 35
        total_cpf_employer = annual_cpf_employer * 35
        total_cpf_total = annual_cpf_total * 35
        
        # CPF分配总计（不含利息）
        total_cpf_OA = cpf_base * 0.23 * 35
        total_cpf_SA = cpf_base * 0.06 * 35
        total_cpf_MA = cpf_base * 0.08 * 35
        
        # 验证：总缴费应该等于各账户分配之和
        assert abs(total_cpf_total - (total_cpf_OA + total_cpf_SA + total_cpf_MA)) < 1e-6, \
            f"CPF分配不匹配: 总缴费={total_cpf_total}, 分配合计={total_cpf_OA + total_cpf_SA + total_cpf_MA}"
        
        # 计算总收入（考虑工资增长）
        total_salary = 0
        total_tax = 0
        for year in range(35):
            salary = annual_income * (1.03 ** year)  # 3%年增长
            total_salary += salary
            total_tax += plugin.calculate_tax(salary).get('total_tax', 0)
        
        print(f"总收入: {plugin.format_currency(total_salary)}")
        print(f"总CPF缴费 (雇员): {plugin.format_currency(total_cpf_employee)}")
        print(f"总CPF缴费 (雇主): {plugin.format_currency(total_cpf_employer)}")
        print(f"总CPF缴费 (合计): {plugin.format_currency(total_cpf_total)}")
        
        print(f"\nCPF分配总计:")
        print(f"  OA (普通账户): {plugin.format_currency(total_cpf_OA)}")
        print(f"  SA (特别账户): {plugin.format_currency(total_cpf_SA)}")
        print(f"  MA (医疗账户): {plugin.format_currency(total_cpf_MA)}")
        
        print(f"\n总税费: {plugin.format_currency(total_tax)}")
        print(f"实际到手收入: {plugin.format_currency(total_salary - total_cpf_employee - total_tax)}")

        # 显示退休期分析
        print(f"\n=== 退休期分析 (65-90岁) ===")
        print(f"退休期总领取: {plugin.format_currency(pension_result.monthly_pension * 12 * 25)}")
        print(f"月领取金额: {plugin.format_currency(pension_result.monthly_pension)}")
        print(f"年领取金额: {plugin.format_currency(pension_result.monthly_pension * 12)}")
        print(f"退休期年数: 25年")

        # 显示最终账户余额
        if hasattr(pension_result, 'details') and pension_result.details and 'cpf_accounts' in pension_result.details:
            accounts = pension_result.details['cpf_accounts']
            print(f"\n=== 最终CPF账户余额 (90岁) ===")
            print(f"OA余额: {plugin.format_currency(accounts.get('oa_balance', 0))}")
            print(f"SA余额: {plugin.format_currency(accounts.get('sa_balance', 0))}")
            print(f"MA余额: {plugin.format_currency(accounts.get('ma_balance', 0))}")
            print(f"RA余额: {plugin.format_currency(accounts.get('ra_balance', 0))}")
            total_balance = sum([accounts.get('oa_balance', 0), accounts.get('sa_balance', 0), 
                               accounts.get('ma_balance', 0), accounts.get('ra_balance', 0)])
            print(f"总CPF余额: {plugin.format_currency(total_balance)}")

        # 显示ROI分析
        print(f"\n=== ROI分析 ===")
        print(f"简单回报率: {pension_result.roi:.1f}%")
        print(f"IRR (内部收益率): {pension_result.roi:.2f}%")
        if pension_result.break_even_age:
            print(f"回本年龄: {pension_result.break_even_age}岁")
            print(f"回本时间: {pension_result.break_even_age - 65}年")
        else:
            print("在90岁前无法回本")

        # 显示人民币对比
        print(f"\n💱 人民币对比:")
        monthly_pension_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.monthly_pension, plugin.CURRENCY, ""), 
            'CNY'
        )
        total_contribution_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(pension_result.total_contribution, plugin.CURRENCY, ""), 
            'CNY'
        )
        print(f"  月退休金: {self.smart_converter.format_amount(monthly_pension_cny)}")
        print(f"  总缴费: {self.smart_converter.format_amount(total_contribution_cny)}")

    def _print_death_at_90_scenarios(self, plugin, pension_result: PensionResult):
        """打印90岁去世场景分析"""
        
        # 导入CPF payout calculator
        from .cpf_payout_calculator import SingaporeCPFPayoutCalculator
        
        print(f"\n=== 90岁去世场景分析 ===")
        
        # 获取RA余额
        ra_balance = 0
        if hasattr(pension_result, 'details') and pension_result.details and 'cpf_accounts' in pension_result.details:
            accounts = pension_result.details['cpf_accounts']
            ra_balance = accounts.get('ra_balance', 0)
        
        if ra_balance <= 0:
            print("⚠️  RA账户余额为0，无法进行90岁去世场景分析")
            return
        
        # 创建CPF payout calculator
        payout_calculator = SingaporeCPFPayoutCalculator()
        
        print(f"基于RA账户余额: {plugin.format_currency(ra_balance)}")
        print()
        
        # 场景1: 90岁去世不留余额（花完所有钱）
        print("【场景1: 90岁去世不留余额】")
        print("-" * 40)
        
        # 使用CPF Life计算，确保25年后余额为0
        cpf_life_no_balance = payout_calculator.calculate_cpf_life_payout(
            ra_balance=ra_balance,
            sa_balance=0,
            annual_nominal_rate=0.04,  # 4%年利率
            annual_inflation_rate=0.02,  # 2%通胀率
            payout_years=25,  # 25年领取期
            scheme="level"  # 固定金额
        )
        
        print(f"场景描述: 90岁去世不留余额 (花完所有钱)")
        print(f"每月养老金: {plugin.format_currency(cpf_life_no_balance.monthly_payment)}")
        print(f"总领取金额: {plugin.format_currency(cpf_life_no_balance.total_payments)}")
        print(f"总利息收入: {plugin.format_currency(cpf_life_no_balance.total_interest)}")
        print(f"领取年限: {cpf_life_no_balance.payout_years}年")
        print(f"最终余额: {plugin.format_currency(cpf_life_no_balance.final_balance)}")
        print(f"计算方式: CPF Life (考虑4%年利率，25年领取期，确保余额为0)")
        
        # 场景2: 90岁去世有余额（保守领取）
        print(f"\n【场景2: 90岁去世有余额】")
        print("-" * 40)
        
        # 保守领取：每月领取较少，让账户在90岁时还有余额
        # 假设每月领取RA余额的1/400（比1/300少），这样25年后还有余额
        conservative_monthly = ra_balance / 400  # 比300个月少，更保守
        conservative_total = conservative_monthly * 300  # 25年总领取
        conservative_remaining = ra_balance - conservative_total  # 剩余余额
        
        print(f"场景描述: 90岁去世有余额 (保守领取)")
        print(f"每月养老金: {plugin.format_currency(conservative_monthly)}")
        print(f"总领取金额: {plugin.format_currency(conservative_total)}")
        print(f"总利息收入: {plugin.format_currency(0)} (假设无利息)")
        print(f"领取年限: 25年")
        print(f"最终余额: {plugin.format_currency(conservative_remaining)}")
        print(f"计算方式: 保守领取 (RA余额 ÷ 400个月)")
        
        # 场景3: 90岁去世有余额（考虑利息的保守领取）
        print(f"\n【场景3: 90岁去世有余额 (考虑利息)】")
        print("-" * 40)
        
        # 考虑利息的保守领取：每月领取较少，让账户在90岁时还有余额
        # 使用较低的月支付，让账户在25年后还有余额
        monthly_rate = 0.04 / 12  # 4%年利率转换为月利率
        months = 25 * 12
        
        # 计算一个较低的月支付，使得25年后还有余额
        # 假设每月领取RA余额的1/450（更保守）
        conservative_monthly_with_interest = ra_balance / 450
        
        # 模拟25年的账户变化
        balance = ra_balance
        total_paid = 0
        for month in range(months):
            interest = balance * monthly_rate
            balance = balance + interest - conservative_monthly_with_interest
            total_paid += conservative_monthly_with_interest
            if balance <= 0:
                balance = 0
                break
        
        total_interest_conservative = total_paid - (ra_balance - balance)
        
        print(f"场景描述: 90岁去世有余额 (考虑利息的保守领取)")
        print(f"每月养老金: {plugin.format_currency(conservative_monthly_with_interest)}")
        print(f"总领取金额: {plugin.format_currency(total_paid)}")
        print(f"总利息收入: {plugin.format_currency(total_interest_conservative)}")
        print(f"领取年限: 25年")
        print(f"最终余额: {plugin.format_currency(balance)}")
        print(f"计算方式: 保守领取 (RA余额 ÷ 450个月) + 4%年利率")
        
        # 对比分析
        print(f"\n【三种场景对比】")
        print("-" * 80)
        print(f"{'指标':<15} {'不留余额':<15} {'有余额(保守)':<15} {'有余额(考虑利息)':<20}")
        print("-" * 80)
        print(f"{'每月养老金':<15} {plugin.format_currency(cpf_life_no_balance.monthly_payment):<15} {plugin.format_currency(conservative_monthly):<15} {plugin.format_currency(conservative_monthly_with_interest):<20}")
        print(f"{'总领取金额':<15} {plugin.format_currency(cpf_life_no_balance.total_payments):<15} {plugin.format_currency(conservative_total):<15} {plugin.format_currency(total_paid):<20}")
        print(f"{'最终余额':<15} {plugin.format_currency(cpf_life_no_balance.final_balance):<15} {plugin.format_currency(conservative_remaining):<15} {plugin.format_currency(balance):<20}")
        print(f"{'利息收入':<15} {plugin.format_currency(cpf_life_no_balance.total_interest):<15} {'$0.00':<15} {plugin.format_currency(total_interest_conservative):<20}")
        
        # 人民币对比
        print(f"\n💱 人民币对比:")
        monthly_no_balance_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(cpf_life_no_balance.monthly_payment, plugin.CURRENCY, ""), 
            'CNY'
        )
        monthly_conservative_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(conservative_monthly, plugin.CURRENCY, ""), 
            'CNY'
        )
        monthly_conservative_interest_cny = self.smart_converter.convert_to_local(
            CurrencyAmount(conservative_monthly_with_interest, plugin.CURRENCY, ""), 
            'CNY'
        )
        print(f"  不留余额月养老金: {self.smart_converter.format_amount(monthly_no_balance_cny)}")
        print(f"  有余额(保守)月养老金: {self.smart_converter.format_amount(monthly_conservative_cny)}")
        print(f"  有余额(考虑利息)月养老金: {self.smart_converter.format_amount(monthly_conservative_interest_cny)}")
        
        # 总结
        print(f"\n📝 总结:")
        print(f"• 不留余额方案: 花完所有钱，每月领取{plugin.format_currency(cpf_life_no_balance.monthly_payment)}，90岁去世时余额为0")
        print(f"• 有余额(保守)方案: 保守领取，每月领取{plugin.format_currency(conservative_monthly)}，90岁去世时余额{plugin.format_currency(conservative_remaining)}")
        print(f"• 有余额(考虑利息)方案: 考虑利息的保守领取，每月领取{plugin.format_currency(conservative_monthly_with_interest)}，90岁去世时余额{plugin.format_currency(balance)}")
        print(f"• 建议: 根据个人风险偏好和家庭情况选择合适方案")