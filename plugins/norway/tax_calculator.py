#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威个人所得税计算器
基于2024年挪威税收政策
"""

from typing import Dict, List

class NorwayTaxCalculator:
    """挪威个人所得税计算器"""

    def __init__(self):
        self.country_code = 'NO'
        self.country_name = '挪威'
        self.currency = 'NOK'
        
        # 2024年基本免税额
        self.basic_deduction = 70000  # 70,000 NOK
        
        # 挪威采用平税制，但有基本免税额
        self.municipal_tax_rate = 0.22  # 市政税 22%
        self.national_tax_rate = 0.22   # 国家税 22%
        self.total_tax_rate = 0.44      # 总税率 44%
        
        # 特殊扣除项
        self.special_deductions = {
            'social_security': 0,      # 社保扣除
            'pension': 0,             # 养老金缴费
            'interest': 0,            # 利息支出
            'other': 0                # 其他扣除
        }

    def get_tax_brackets(self) -> List[Dict]:
        """获取挪威税率表 (2024年)"""
        # 挪威采用平税制，但有基本免税额
        return [
            {
                'min': 0, 
                'max': self.basic_deduction, 
                'rate': 0.0, 
                'description': '基本免税额'
            },
            {
                'min': self.basic_deduction, 
                'max': float('inf'), 
                'rate': self.total_tax_rate, 
                'description': '标准税率'
            }
        ]

    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算挪威个人所得税
        
        Args:
            annual_income: 年收入 (NOK)
            deductions: 扣除项字典
            
        Returns:
            税收计算结果字典
        """
        if deductions is None:
            deductions = {}

        # 更新扣除项
        for key, value in deductions.items():
            if key in self.special_deductions:
                self.special_deductions[key] = value

        # 计算总扣除额
        total_deductions = self.basic_deduction + sum(self.special_deductions.values())

        # 计算应纳税所得额
        taxable_income = max(0, annual_income - total_deductions)

        if taxable_income <= 0:
            return {
                'total_tax': 0,
                'taxable_income': 0,
                'total_deductions': total_deductions,
                'breakdown': {
                    'basic_deduction': self.basic_deduction,
                    'special_deductions': self.special_deductions.copy(),
                    'tax_details': []
                }
            }

        # 计算税收 (平税制)
        total_tax = taxable_income * self.total_tax_rate
        
        # 分解税收
        municipal_tax = taxable_income * self.municipal_tax_rate
        national_tax = taxable_income * self.national_tax_rate

        tax_details = [
            {
                'type': '市政税',
                'rate': f"{self.municipal_tax_rate:.1%}",
                'taxable_amount': taxable_income,
                'tax_amount': municipal_tax
            },
            {
                'type': '国家税',
                'rate': f"{self.national_tax_rate:.1%}",
                'taxable_amount': taxable_income,
                'tax_amount': national_tax
            }
        ]

        return {
            'total_tax': total_tax,
            'taxable_income': taxable_income,
            'total_deductions': total_deductions,
            'breakdown': {
                'basic_deduction': self.basic_deduction,
                'special_deductions': self.special_deductions.copy(),
                'tax_details': tax_details
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

    def get_tax_summary(self, annual_income: float, deductions: Dict = None) -> Dict:
        """获取税收汇总信息"""
        tax_result = self.calculate_income_tax(annual_income, deductions)

        return {
            'country_code': self.country_code,
            'country_name': self.country_name,
            'currency': self.currency,
            'annual_income': annual_income,
            'total_tax': tax_result.get('total_tax', 0),
            'net_income': self.calculate_net_income(annual_income, deductions),
            'effective_tax_rate': self.calculate_effective_tax_rate(annual_income, deductions),
            'monthly_net_income': self.calculate_net_income(annual_income, deductions) / 12,
            'details': tax_result
        }

    def set_social_security_deduction(self, amount: float):
        """设置社保扣除金额"""
        self.special_deductions['social_security'] = amount

    def set_pension_deduction(self, amount: float):
        """设置养老金缴费扣除金额"""
        self.special_deductions['pension'] = amount

    def set_interest_deduction(self, amount: float):
        """设置利息支出扣除金额"""
        self.special_deductions['interest'] = amount

    def set_other_deduction(self, amount: float):
        """设置其他扣除金额"""
        self.special_deductions['other'] = amount

    def calculate_social_security_contribution(self, monthly_salary: float) -> Dict:
        """计算社保缴费金额"""
        # 挪威社保缴费基数上下限
        social_base_min = 50000 / 12   # 月度下限
        social_base_max = 1000000 / 12 # 月度上限
        
        # 计算缴费基数
        contribution_base = max(social_base_min, min(monthly_salary, social_base_max))
        
        # 社保缴费比例（个人部分）
        pension_rate = 0.08      # 养老金 8%
        
        # 计算社保缴费
        pension_contribution = contribution_base * pension_rate
        
        return {
            'contribution_base': contribution_base,
            'pension': pension_contribution,
            'total': pension_contribution
        }

    def calculate_employer_contributions(self, monthly_salary: float) -> Dict:
        """计算雇主缴费"""
        # 雇主缴费比例
        employer_pension_rate = 0.14  # 雇主养老金缴费 14%
        
        # 计算雇主缴费
        employer_pension = monthly_salary * employer_pension_rate
        
        return {
            'pension': employer_pension,
            'total': employer_pension
        }