import numpy as np
from typing import List, Dict, Any, Tuple

class InvestmentCalculator:
    """投资回报计算器"""

    @staticmethod
    def calculate_future_value(present_value: float,
                             years: int,
                             annual_rate: float,
                             compounding_frequency: int = 1) -> float:
        """计算未来价值"""
        rate_per_period = annual_rate / compounding_frequency
        periods = years * compounding_frequency
        return present_value * ((1 + rate_per_period) ** periods)

    @staticmethod
    def calculate_present_value(future_value: float,
                              years: int,
                              annual_rate: float,
                              compounding_frequency: int = 1) -> float:
        """计算现值"""
        rate_per_period = annual_rate / compounding_frequency
        periods = years * compounding_frequency
        return future_value / ((1 + rate_per_period) ** periods)


    @staticmethod
    def calculate_regular_contribution_future_value(monthly_contribution: float,
                                                  years: int,
                                                  annual_rate: float) -> float:
        """计算定期缴费的未来价值"""
        monthly_rate = annual_rate / 12
        months = years * 12

        if monthly_rate == 0:
            return monthly_contribution * months

        future_value = monthly_contribution * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
        return future_value

    @staticmethod
    def calculate_required_monthly_contribution(target_amount: float,
                                              years: int,
                                              annual_rate: float) -> float:
        """计算达到目标金额所需的月缴费"""
        monthly_rate = annual_rate / 12
        months = years * 12

        if monthly_rate == 0:
            return target_amount / months

        monthly_contribution = target_amount * monthly_rate / (
            ((1 + monthly_rate) ** months - 1)
        )
        return monthly_contribution


