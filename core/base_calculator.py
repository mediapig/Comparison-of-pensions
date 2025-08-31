from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .models import Person, SalaryProfile, EconomicFactors, PensionResult

class BasePensionCalculator(ABC):
    """退休金计算器抽象基类"""

    def __init__(self, country_code: str, country_name: str):
        self.country_code = country_code
        self.country_name = country_name
        self.retirement_ages = self._get_retirement_ages()
        self.contribution_rates = self._get_contribution_rates()

    @abstractmethod
    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取不同性别的退休年龄"""
        pass

    @abstractmethod
    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取缴费比例"""
        pass

    @abstractmethod
    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算退休金"""
        pass

    @abstractmethod
    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史"""
        pass

    def get_retirement_age(self, person: Person) -> int:
        """获取退休年龄"""
        gender_key = "male" if person.gender.value == "male" else "female"
        return self.retirement_ages.get(gender_key, 65)

    def get_contribution_rate(self, employment_type: str) -> float:
        """获取缴费比例"""
        return self.contribution_rates.get(employment_type, 0.08)

    def calculate_inflation_adjusted_amount(self,
                                         amount: float,
                                         years: int,
                                         inflation_rate: float) -> float:
        """计算通胀调整后的金额"""
        return amount / ((1 + inflation_rate) ** years)

    def calculate_future_value(self,
                             present_value: float,
                             years: int,
                             rate: float) -> float:
        """计算未来价值"""
        return present_value * ((1 + rate) ** years)

    def calculate_present_value(self,
                              future_value: float,
                              years: int,
                              rate: float) -> float:
        """计算现值"""
        return future_value / ((1 + rate) ** years)
