#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
税收管理器
统一管理所有国家的税收计算器
"""

from plugins.china.china_tax_calculator import ChinaTaxCalculator
from plugins.usa.usa_tax_calculator import USATaxCalculator
from plugins.singapore.singapore_tax_calculator import SingaporeTaxCalculator
from typing import Dict, List

class TaxManager:
    """税收管理器"""

    def __init__(self):
        self.tax_calculators = {}
        self._init_tax_calculators()

    def _init_tax_calculators(self):
        """初始化所有税收计算器"""
        self.tax_calculators = {
            'CN': ChinaTaxCalculator(),
            'US': USATaxCalculator(),
            'SG': SingaporeTaxCalculator(),
            # 可以继续添加其他国家的税收计算器
        }

    def get_tax_calculator(self, country_code: str):
        """获取指定国家的税收计算器"""
        return self.tax_calculators.get(country_code.upper())

    def get_available_countries(self):
        """获取可用的国家列表"""
        return list(self.tax_calculators.keys())

    def calculate_country_tax(self, country_code: str, annual_income: float,
                             deductions: Dict = None) -> Dict:
        """计算指定国家的个人所得税"""
        calculator = self.get_tax_calculator(country_code)
        if calculator:
            return calculator.get_tax_summary(annual_income, deductions)
        else:
            return {
                'error': f'不支持的国家代码: {country_code}',
                'country_code': country_code,
                'annual_income': annual_income
            }

    def calculate_multiple_countries_tax(self, country_codes: List[str],
                                       annual_income: float, deductions: Dict = None) -> List[Dict]:
        """计算多个国家的个人所得税对比"""
        results = []

        for country_code in country_codes:
            result = self.calculate_country_tax(country_code, annual_income, deductions)
            results.append(result)

        return results

    def calculate_net_income_comparison(self, country_codes: List[str],
                                      annual_income: float, deductions: Dict = None) -> Dict:
        """计算多个国家的税后净收入对比"""
        tax_results = self.calculate_multiple_countries_tax(country_codes, annual_income, deductions)

        comparison = {
            'annual_income': annual_income,
            'countries': tax_results,
            'summary': {
                'highest_net_income': max(tax_results, key=lambda x: x.get('net_income', 0)),
                'lowest_net_income': min(tax_results, key=lambda x: x.get('net_income', 0)),
                'average_net_income': sum(r.get('net_income', 0) for r in tax_results) / len(tax_results)
            }
        }

        return comparison

    def calculate_with_social_security(self, country_code: str, annual_income: float,
                                     social_security_amount: float, other_deductions: Dict = None) -> Dict:
        """计算包含社保扣除的个税"""
        calculator = self.get_tax_calculator(country_code)
        if not calculator:
            return {'error': f'不支持的国家代码: {country_code}'}

        if other_deductions is None:
            other_deductions = {}

        # 添加社保扣除
        if country_code == 'CN':
            calculator.set_social_security_deduction(social_security_amount)
            deductions = other_deductions
        elif country_code == 'US':
            # 美国社保不能从个税中扣除，但401K可以
            deductions = other_deductions
        else:
            deductions = other_deductions

        return calculator.get_tax_summary(annual_income, deductions)

    def get_tax_brackets(self, country_code: str) -> List[Dict]:
        """获取指定国家的税率表"""
        calculator = self.get_tax_calculator(country_code)
        if calculator:
            return calculator.get_tax_brackets()
        return []

    def format_tax_summary(self, tax_summary: Dict) -> str:
        """格式化税收汇总信息"""
        if 'error' in tax_summary:
            return f"❌ {tax_summary['error']}"

        country_name = tax_summary.get('country_name', 'Unknown')
        currency = tax_summary.get('currency', '')
        annual_income = tax_summary.get('annual_income', 0)
        total_tax = tax_summary.get('total_tax', 0)
        net_income = tax_summary.get('net_income', 0)
        effective_tax_rate = tax_summary.get('effective_tax_rate', 0)
        monthly_net_income = tax_summary.get('monthly_net_income', 0)

        summary = f"""
🏛️  {country_name} 税收汇总
💰 年收入: {currency}{annual_income:,.2f}
💸 总税额: {currency}{total_tax:,.2f}
💵 税后净收入: {currency}{net_income:,.2f}
📊 有效税率: {effective_tax_rate:.1f}%
💳 月净收入: {currency}{monthly_net_income:,.2f}
"""
        return summary
