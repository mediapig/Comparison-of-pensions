#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
香港个人所得税计算器
"""

from typing import Dict, List

class HongKongTaxCalculator:
    """香港个人所得税计算器"""

    def __init__(self):
        self.country_code = 'HK'
        self.country_name = '香港'
        self.currency = 'HKD'

    def get_tax_brackets(self) -> List[Dict]:
        """获取香港个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 50000, 'rate': 0.02},
            {'min': 50000, 'max': 100000, 'rate': 0.06},
            {'min': 100000, 'max': 150000, 'rate': 0.10},
            {'min': 150000, 'max': 200000, 'rate': 0.14},
            {'min': 200000, 'max': float('inf'), 'rate': 0.17}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算香港个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本免税额（2024年）
        basic_allowance = 132000

        # 强积金缴费扣除
        mpf_deduction = min(annual_income * 0.05, 18000)  # 最大18,000港币

        # 总扣除额
        total_deductions = basic_allowance + mpf_deduction + sum(deductions.values())

        # 应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_allowance': basic_allowance,
                    'mpf_deduction': mpf_deduction,
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
                        'bracket': f"HK${bracket['min']:,.0f}-{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'basic_allowance': basic_allowance,
                'mpf_deduction': mpf_deduction,
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
