#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美国税收计算器
基于2024年最新税收政策
"""

from typing import Dict, List

class USATaxCalculator:
    """美国税收计算器"""

    def __init__(self):
        self.country_code = 'US'
        self.country_name = '美国'
        self.currency = 'USD'
        self.standard_deduction = 14600  # 2024年单身标准扣除额

    def get_tax_brackets(self) -> List[Dict]:
        """获取美国联邦税率表 (2024年)"""
        return [
            {'min': 0, 'max': 11000, 'rate': 0.10},
            {'min': 11000, 'max': 44725, 'rate': 0.12},
            {'min': 44725, 'max': 95375, 'rate': 0.22},
            {'min': 95375, 'max': 182050, 'rate': 0.24},
            {'min': 182050, 'max': 231250, 'rate': 0.32},
            {'min': 231250, 'max': 578125, 'rate': 0.35},
            {'min': 578125, 'max': float('inf'), 'rate': 0.37}
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算美国联邦所得税

        Args:
            annual_income: 年收入
            deductions: 扣除项字典

        Returns:
            税收计算结果字典
        """
        if deductions is None:
            deductions = {}

        # 计算总扣除额
        total_deductions = self.standard_deduction + sum(deductions.values())

        # 计算应纳税所得额
        taxable_income = annual_income - total_deductions

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'standard_deduction': self.standard_deduction,
                    'itemized_deductions': deductions.copy(),
                    'tax_brackets': []
                }
            }

        # 计算联邦税
        tax_brackets = self.get_tax_brackets()
        total_tax = 0
        bracket_details = []

        for bracket in tax_brackets:
            if taxable_income > bracket['min']:
                # 计算该档位的应纳税所得额
                bracket_taxable = min(taxable_income - bracket['min'],
                                    bracket['max'] - bracket['min'])

                if bracket_taxable > 0:
                    # 计算该档位的税额
                    bracket_tax = bracket_taxable * bracket['rate']
                    total_tax += bracket_tax

                    bracket_details.append({
                        'bracket': f"${bracket['min']:,.0f}-${bracket['max']:,.0f}",
                        'rate': f"{bracket['rate']:.1%}",
                        'taxable_amount': bracket_taxable,
                        'tax_amount': bracket_tax
                    })

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'standard_deduction': self.standard_deduction,
                'itemized_deductions': deductions.copy(),
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
