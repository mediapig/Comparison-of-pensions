#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础插件类 - 所有国家插件的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import date

from .models import Person, SalaryProfile, EconomicFactors, PensionResult, Gender, EmploymentType

@dataclass
class PluginConfig:
    """插件配置"""
    country_code: str
    country_name: str
    currency: str
    retirement_ages: Dict[str, int]
    tax_year: int

class BaseCountryPlugin(ABC):
    """国家插件基类"""

    COUNTRY_CODE: str = ""
    COUNTRY_NAME: str = ""
    CURRENCY: str = ""

    def __init__(self):
        self.config = self._load_config()

    @abstractmethod
    def _load_config(self) -> PluginConfig:
        """加载插件配置"""
        pass

    def create_person(self, start_age: int = 30) -> Person:
        """创建Person对象 - 每个插件可以根据自己的退休年龄调整"""
        current_year = date.today().year
        return Person(
            name=f"{self.COUNTRY_NAME}用户",
            birth_date=date(current_year - start_age, 1, 1),
            gender=Gender.MALE,
            employment_type=EmploymentType.EMPLOYEE,
            start_work_date=date(current_year, 1, 1)
        )

    @abstractmethod
    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算退休金"""
        pass

    @abstractmethod
    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算个人所得税"""
        pass

    @abstractmethod
    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算社保缴费"""
        pass

    @abstractmethod
    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        pass

    def format_currency(self, amount: float) -> str:
        """格式化货币显示"""
        currency_symbols = {
            'CNY': '¥',
            'USD': '$',
            'SGD': 'S$',
            'CAD': 'C$',
            'AUD': 'A$',
            'HKD': 'HK$',
            'TWD': 'NT$',
            'JPY': '¥',
            'GBP': '£'
        }

        symbol = currency_symbols.get(self.CURRENCY, self.CURRENCY)
        return f"{symbol}{amount:,.2f}"

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """货币转换（简化版本）"""
        # 简化的汇率表 (2024年汇率，人民币为基准)
        exchange_rates = {
            'CNY': 1.0,      # 人民币
            'USD': 0.14,     # 美元
            'SGD': 0.19,     # 新加坡元
            'CAD': 0.19,     # 加拿大元
            'AUD': 0.21,     # 澳大利亚元
            'HKD': 1.08,     # 港币
            'TWD': 4.4,      # 台币
            'JPY': 20.5,     # 日元
            'GBP': 0.11,     # 英镑
        }

        if from_currency == to_currency:
            return amount

        # 先转换为人民币，再转换为目标货币
        cny_amount = amount / exchange_rates.get(from_currency, 1.0)
        return cny_amount * exchange_rates.get(to_currency, 1.0)
