from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class EmploymentType(Enum):
    EMPLOYEE = "employee"          # 企业职工
    CIVIL_SERVANT = "civil_servant"  # 公务员
    SELF_EMPLOYED = "self_employed"  # 自由职业者
    FARMER = "farmer"              # 农民

@dataclass
class Person:
    """个人信息"""
    name: str
    birth_date: date
    gender: Gender
    employment_type: EmploymentType
    start_work_date: date
    retirement_date: Optional[date] = None

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def work_years(self) -> int:
        if self.retirement_date:
            end_date = self.retirement_date
        else:
            end_date = date.today()
        return end_date.year - self.start_work_date.year

@dataclass
class SalaryProfile:
    """工资档案"""
    base_salary: float                    # 基本工资
    annual_growth_rate: float             # 年增长率
    bonus_rate: float = 0.0              # 奖金比例
    social_security_base: Optional[float] = None  # 社保缴费基数

    def get_salary_at_age(self, age: int, start_age: int) -> float:
        """计算指定年龄的工资"""
        years = age - start_age
        return self.base_salary * (1 + self.annual_growth_rate) ** years

@dataclass
class EconomicFactors:
    """经济因素"""
    inflation_rate: float                 # 通胀率
    investment_return_rate: float         # 投资回报率
    social_security_return_rate: float    # 社保基金投资回报率
    base_currency: str = "CNY"           # 基准货币（人民币或美元）
    display_currency: str = "CNY"        # 显示货币

@dataclass
class PensionResult:
    """退休金计算结果"""
    monthly_pension: float               # 月退休金（原始货币）
    total_contribution: float            # 总缴费（原始货币）
    total_benefit: float                 # 总收益（原始货币）
    break_even_age: Optional[int]        # 回本年龄
    roi: float                           # 投资回报率
    original_currency: str               # 原始货币
    details: Dict[str, Any]              # 详细计算过程

    def convert_to_currency(self, target_currency: str, converter) -> 'PensionResult':
        """转换为指定货币"""
        if target_currency == self.original_currency:
            return self

        converted_monthly = converter.convert(self.monthly_pension, self.original_currency, target_currency)
        converted_contribution = converter.convert(self.total_contribution, self.original_currency, target_currency)
        converted_benefit = converter.convert(self.total_benefit, self.original_currency, target_currency)

        return PensionResult(
            monthly_pension=converted_monthly,
            total_contribution=converted_contribution,
            total_benefit=converted_benefit,
            break_even_age=self.break_even_age,
            roi=self.roi,
            original_currency=target_currency,
            details=self.details
        )
