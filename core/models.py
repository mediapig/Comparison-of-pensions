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
    currency: str = "CNY"                 # 货币单位

@dataclass
class PensionResult:
    """退休金计算结果"""
    monthly_pension: float               # 月退休金
    total_contribution: float            # 总缴费
    total_benefit: float                 # 总收益
    break_even_age: Optional[int]        # 回本年龄
    roi: float                           # 投资回报率
    details: Dict[str, Any]              # 详细计算过程
