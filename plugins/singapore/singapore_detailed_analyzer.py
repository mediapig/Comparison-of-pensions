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
        tax_result = plugin.calculate_tax(annual_income)
        print(f"\n应税收入: {plugin.format_currency(taxable_income)}")
        print(f"所得税 (累进税率): {plugin.format_currency(tax_result.get('total_tax', 0))}")
        print(f"实际到手收入: {plugin.format_currency(tax_result.get('net_income', annual_income))}")

        # 显示35年工作期总计
        print(f"\n=== 35年工作期总计 (30-64岁) ===")
        total_salary = 0
        total_cpf_employee = 0
        total_cpf_employer = 0
        total_cpf_OA = 0
        total_cpf_SA = 0
        total_cpf_MA = 0
        total_tax = 0
        
        for year in range(35):
            salary = annual_income * (1.03 ** year)  # 3%年增长
            year_base = min(salary, 102000)
            total_salary += salary
            total_cpf_employee += year_base * 0.20
            total_cpf_employer += year_base * 0.17
            total_cpf_OA += year_base * 0.23
            total_cpf_SA += year_base * 0.06
            total_cpf_MA += year_base * 0.08
            total_tax += plugin.calculate_tax(salary).get('total_tax', 0)
        
        print(f"总收入: {plugin.format_currency(total_salary)}")
        print(f"总CPF缴费 (雇员): {plugin.format_currency(total_cpf_employee)}")
        print(f"总CPF缴费 (雇主): {plugin.format_currency(total_cpf_employer)}")
        print(f"总CPF缴费 (合计): {plugin.format_currency(total_cpf_employee + total_cpf_employer)}")
        
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