#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人所得税计算器基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

class BaseTaxCalculator(ABC):
    """个人所得税计算器基础类"""
    
    def __init__(self, country_code: str, country_name: str):
        self.country_code = country_code
        self.country_name = country_name
        self.currency = self._get_currency()
    
    @abstractmethod
    def _get_currency(self) -> str:
        """获取货币代码"""
        pass
    
    @abstractmethod
    def calculate_income_tax(self, annual_income: float, deductions: Dict = None) -> Dict:
        """
        计算个人所得税
        
        Args:
            annual_income: 年收入
            deductions: 扣除项 (如社保、专项附加扣除等)
        
        Returns:
            包含税收计算结果的字典
        """
        pass
    
    @abstractmethod
    def get_tax_brackets(self) -> List[Dict]:
        """获取税率表"""
        pass
    
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
