#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版基础插件类 - 更清晰的职责分离
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import date
from enum import Enum

from .models import Person, SalaryProfile, EconomicFactors, PensionResult

class SocialSecurityType(Enum):
    """社保类型枚举"""
    PENSION = "pension"           # 养老金
    MEDICAL = "medical"          # 医疗保险
    UNEMPLOYMENT = "unemployment" # 失业保险
    DISABILITY = "disability"     # 残疾保险
    MATERNITY = "maternity"      # 生育保险
    WORK_INJURY = "work_injury"  # 工伤保险

@dataclass
class SocialSecurityResult:
    """社保计算结果"""
    employee_contribution: float    # 员工缴费
    employer_contribution: float     # 雇主缴费
    total_contribution: float       # 总缴费
    coverage_type: SocialSecurityType # 保险类型
    details: Dict[str, Any]         # 详细信息

@dataclass
class PluginConfig:
    """插件配置"""
    country_code: str
    country_name: str
    currency: str
    retirement_ages: Dict[str, int]
    tax_year: int
    supported_social_security_types: List[SocialSecurityType]  # 支持的社保类型

class BaseCountryPlugin(ABC):
    """国家插件基类 - 增强版"""

    COUNTRY_CODE: str = ""
    COUNTRY_NAME: str = ""
    CURRENCY: str = ""

    def __init__(self):
        self.config = self._load_config()

    @abstractmethod
    def _load_config(self) -> PluginConfig:
        """加载插件配置"""
        pass

    # ==================== 养老金计算 ====================
    @abstractmethod
    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算退休金"""
        pass

    # ==================== 税务计算 ====================
    @abstractmethod
    def calculate_tax(self,
                     annual_income: float,
                     deductions: Optional[Dict[str, float]] = None,
                     **kwargs) -> Dict[str, float]:
        """计算个人所得税"""
        pass

    # ==================== 社保计算 ====================
    @abstractmethod
    def calculate_social_security(self,
                                monthly_salary: float,
                                years: int,
                                **kwargs) -> Dict[str, float]:
        """计算社保缴费（兼容旧接口）"""
        pass

    def calculate_pension_contribution(self,
                                     monthly_salary: float,
                                     years: int,
                                     **kwargs) -> SocialSecurityResult:
        """计算养老金缴费"""
        # 默认实现，子类可以重写
        result = self.calculate_social_security(monthly_salary, years, **kwargs)
        return SocialSecurityResult(
            employee_contribution=result.get('monthly_employee', 0),
            employer_contribution=result.get('monthly_employer', 0),
            total_contribution=result.get('monthly_employee', 0) + result.get('monthly_employer', 0),
            coverage_type=SocialSecurityType.PENSION,
            details=result
        )

    def calculate_medical_contribution(self,
                                     monthly_salary: float,
                                     years: int,
                                     **kwargs) -> Optional[SocialSecurityResult]:
        """计算医疗保险缴费（可选）"""
        # 默认返回None，表示该国不支持医疗保险
        return None

    def calculate_unemployment_contribution(self,
                                          monthly_salary: float,
                                          years: int,
                                          **kwargs) -> Optional[SocialSecurityResult]:
        """计算失业保险缴费（可选）"""
        # 默认返回None，表示该国不支持失业保险
        return None

    def get_supported_social_security_types(self) -> List[SocialSecurityType]:
        """获取支持的社保类型"""
        return self.config.supported_social_security_types

    def has_medical_insurance(self) -> bool:
        """是否有医疗保险"""
        return SocialSecurityType.MEDICAL in self.get_supported_social_security_types()

    def has_unemployment_insurance(self) -> bool:
        """是否有失业保险"""
        return SocialSecurityType.UNEMPLOYMENT in self.get_supported_social_security_types()

    # ==================== 其他方法 ====================
    @abstractmethod
    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        pass

    def get_tax_brackets(self) -> List[Dict[str, float]]:
        """获取税率表"""
        return []

    def get_contribution_rates(self) -> Dict[str, float]:
        """获取社保缴费率"""
        return {}

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
            'GBP': '£',
            'NOK': 'kr'
        }

        symbol = currency_symbols.get(self.CURRENCY, self.CURRENCY)
        return f"{symbol}{amount:,.2f}"

    def get_country_info(self) -> Dict[str, Any]:
        """获取国家信息"""
        return {
            'country_code': self.COUNTRY_CODE,
            'country_name': self.COUNTRY_NAME,
            'currency': self.CURRENCY,
            'retirement_age': self.get_retirement_age(Person("", date(1985, 1, 1), None, None, date(2010, 1, 1))),
            'supported_social_security_types': [t.value for t in self.get_supported_social_security_types()],
            'has_medical_insurance': self.has_medical_insurance(),
            'has_unemployment_insurance': self.has_unemployment_insurance()
        }