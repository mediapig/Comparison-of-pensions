#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚个人所得税计算器
"""

from typing import Dict, List

class AustraliaTaxCalculator:
    """澳大利亚个人所得税计算器"""

    def __init__(self):
        self.country_code = 'AU'
        self.country_name = '澳大利亚'
        self.currency = 'AUD'

    def get_tax_brackets(self) -> List[Dict]:
        """获取澳大利亚个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 18200, 'rate': 0.0},
            {'min': 18200, 'max': 45000, 'rate': 0.19},
            {'min': 45000, 'max': 120000, 'rate': 0.325},
            {'min': 120000, 'max': 180000, 'rate': 0.37},
            {'min': 180000, 'max': float('inf'), 'rate': 0.45}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算澳大利亚个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本免税额
        tax_free_threshold = 18200

        # 应纳税所得额
        taxable_income = max(0, annual_income - tax_free_threshold - sum(deductions.values()))

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': tax_free_threshold + sum(deductions.values()),
                'breakdown': {
                    'tax_free_threshold': tax_free_threshold,
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
                        'bracket': f"${bracket['min']:,.0f}-${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': tax_free_threshold + sum(deductions.values()),
            'breakdown': {
                'tax_free_threshold': tax_free_threshold,
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
