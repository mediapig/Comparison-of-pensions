#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加拿大个人所得税计算器
"""

from typing import Dict, List

class CanadaTaxCalculator:
    """加拿大个人所得税计算器"""

    def __init__(self):
        self.country_code = 'CA'
        self.country_name = '加拿大'
        self.currency = 'CAD'

    def get_tax_brackets(self) -> List[Dict]:
        """获取加拿大联邦个税税率表 (2024年)"""
        return [
            {'min': 0, 'max': 55867, 'rate': 0.15},
            {'min': 55867, 'max': 111733, 'rate': 0.205},
            {'min': 111733, 'max': 173205, 'rate': 0.26},
            {'min': 173205, 'max': 246752, 'rate': 0.29},
            {'min': 246752, 'max': float('inf'), 'rate': 0.33}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """计算加拿大联邦个人所得税"""
        if deductions is None:
            deductions = {}

        # 基本免税额（2024年）
        basic_personal_amount = 15000

        # CPP和EI扣除
        cpp_deduction = min(annual_income * 0.0595, 3754)  # CPP最大缴费
        ei_deduction = min(annual_income * 0.0166, 1002)   # EI最大缴费

        # 总扣除额
        total_deductions = basic_personal_amount + cpp_deduction + ei_deduction + sum(deductions.values())

        # 应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_personal_amount': basic_personal_amount,
                    'cpp_deduction': cpp_deduction,
                    'ei_deduction': ei_deduction,
                    'other_deductions': sum(deductions.values()),
                    'tax_brackets': []
                }
            }

        # 计算联邦税
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
            'total_deductions': total_deductions,
            'breakdown': {
                'basic_personal_amount': basic_personal_amount,
                'cpp_deduction': cpp_deduction,
                'ei_deduction': ei_deduction,
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
