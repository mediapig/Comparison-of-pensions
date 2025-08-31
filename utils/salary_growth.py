import numpy as np
from typing import List, Dict, Any
from datetime import date

class SalaryGrowthModel:
    """工资增长模型"""

    @staticmethod
    def linear_growth(base_salary: float,
                     growth_rate: float,
                     years: int) -> List[float]:
        """线性增长模型"""
        salaries = []
        for year in range(years + 1):
            salary = base_salary * (1 + growth_rate * year)
            salaries.append(salary)
        return salaries

    @staticmethod
    def compound_growth(base_salary: float,
                       growth_rate: float,
                       years: int) -> List[float]:
        """复合增长模型（默认）"""
        salaries = []
        for year in range(years + 1):
            salary = base_salary * ((1 + growth_rate) ** year)
            salaries.append(salary)
        return salaries

    @staticmethod
    def stage_growth(base_salary: float,
                    growth_stages: List[Dict[str, Any]]) -> List[float]:
        """分阶段增长模型"""
        salaries = [base_salary]
        current_salary = base_salary

        for stage in growth_stages:
            years = stage['years']
            rate = stage['rate']

            for year in range(years):
                current_salary = current_salary * (1 + rate)
                salaries.append(current_salary)

        return salaries

    @staticmethod
    def inflation_adjusted_growth(base_salary: float,
                                nominal_growth_rate: float,
                                inflation_rate: float,
                                years: int) -> List[float]:
        """考虑通胀的实际工资增长"""
        salaries = []
        for year in range(years + 1):
            nominal_salary = base_salary * ((1 + nominal_growth_rate) ** year)
            real_salary = nominal_salary / ((1 + inflation_rate) ** year)
            salaries.append(real_salary)
        return salaries

    @staticmethod
    def career_peak_growth(base_salary: float,
                          peak_age: int,
                          start_age: int,
                          peak_multiplier: float = 3.0,
                          years: int = 40) -> List[float]:
        """职业生涯峰值增长模型"""
        salaries = []
        for year in range(years + 1):
            age = start_age + year
            years_to_peak = peak_age - start_age

            if age <= peak_age:
                # 上升阶段
                progress = year / years_to_peak
                growth_factor = 1 + (peak_multiplier - 1) * (progress ** 0.5)
            else:
                # 下降阶段
                years_after_peak = age - peak_age
                decline_factor = max(0.7, 1 - (years_after_peak * 0.01))
                growth_factor = peak_multiplier * decline_factor

            salary = base_salary * growth_factor
            salaries.append(salary)

        return salaries

    @staticmethod
    def calculate_average_salary_growth(salary_history: List[float]) -> float:
        """计算平均工资增长率"""
        if len(salary_history) < 2:
            return 0.0

        growth_rates = []
        for i in range(1, len(salary_history)):
            if salary_history[i-1] > 0:
                rate = (salary_history[i] - salary_history[i-1]) / salary_history[i-1]
                growth_rates.append(rate)

        if not growth_rates:
            return 0.0

        return np.mean(growth_rates)
