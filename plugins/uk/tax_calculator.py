#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
英国个人所得税计算器
"""

from typing import Dict, List

class UKTaxCalculator:
    """英国个人所得税计算器"""

    def __init__(self):
        self.country_code = 'UK'
        self.country_name = '英国'
        self.currency = 'GBP'

    def get_tax_brackets(self) -> List[Dict]:
        """获取英国个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 12570, 'rate': 0.0},      # 个人免税额
            {'min': 12570, 'max': 50270, 'rate': 0.20},  # 基础税率
            {'min': 50270, 'max': 125140, 'rate': 0.40}, # 高税率
            {'min': 125140, 'max': float('inf'), 'rate': 0.45}  # 附加税率
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算英国个人所得税"""
        if deductions is None:
            deductions = {}

        # 个人免税额（2024年）
        personal_allowance = 12570

        # 国家保险缴费扣除
        ni_deduction = min(annual_income * 0.12, 4524)  # 最大4,524英镑

        # 总扣除额
        total_deductions = personal_allowance + ni_deduction + sum(deductions.values())

        # 应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'personal_allowance': personal_allowance,
                    'ni_deduction': ni_deduction,
                    'other_deductions': sum(deductions.values()),
                    'tax_brackets': []
                }
            }

        # 计算个税
        tax_brackets = self.get_tax_brackets()
        total_tax = 0
        bracket_details = []

        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                taxable_in_bracket = min(taxable_income - bracket['min'],
                                       bracket['max'] - bracket['min'])
                if taxable_in_bracket > 0:
                    bracket_tax = taxable_in_bracket * bracket['rate']
                    total_tax += bracket_tax

                    bracket_details.append({
                        'bracket': f"£{bracket['min']:,.0f}-{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'personal_allowance': personal_allowance,
                'ni_deduction': ni_deduction,
                'other_deductions': sum(deductions.values()),
                'tax_brackets': bracket_details
            }
        }

    def calculate_effective_tax_rate(self, annual_income: float, deductions: Dict = None) -> float:
        """计算有效税率"""
        tax_result = self.calculate_income_tax(annual_income, deductions)
        total_tax = tax_result.get('total_tax', 0)
        return (total_tax / annual_income * 100) if annual_income > 0 else 0

    def calculate_net_income(self, annual_income: float, deductions: Dict = None) -> float:
        """计算税后净收入"""
        tax_result = self.calculate_income_tax(annual_income, deductions)
        total_tax = tax_result.get('total_tax', 0)
        return annual_income - total_tax
