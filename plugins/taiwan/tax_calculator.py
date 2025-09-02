#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾个人所得税计算器
"""

from typing import Dict, List

class TaiwanTaxCalculator:
    """台湾个人所得税计算器"""

    def __init__(self):
        self.country_code = 'TW'
        self.country_name = '台湾'
        self.currency = 'TWD'

    def get_tax_brackets(self) -> List[Dict]:
        """获取台湾个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 560000, 'rate': 0.05},
            {'min': 560000, 'max': 1260000, 'rate': 0.12},
            {'min': 1260000, 'max': 2520000, 'rate': 0.20},
            {'min': 2520000, 'max': 4720000, 'rate': 0.30},
            {'min': 4720000, 'max': float('inf'), 'rate': 0.40}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算台湾个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本免税额（2024年）
        basic_deduction = 92000

        # 劳保缴费扣除
        labor_insurance_deduction = min(annual_income * 0.02, 24000)  # 最大24,000台币

        # 总扣除额
        total_deductions = basic_deduction + labor_insurance_deduction + sum(deductions.values())

        # 应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_deduction': basic_deduction,
                    'labor_insurance_deduction': labor_insurance_deduction,
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
                        'bracket': f"NT${bracket['min']:,.0f}-{bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': taxable_in_bracket,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'basic_deduction': basic_deduction,
                'labor_insurance_deduction': labor_insurance_deduction,
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
