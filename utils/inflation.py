import numpy as np
from typing import List, Tuple

class InflationCalculator:
    """通胀计算器"""

    @staticmethod
    def calculate_inflation_adjusted_amount(amount: float,
                                         years: int,
                                         inflation_rate: float) -> float:
        """计算通胀调整后的金额"""
        return amount / ((1 + inflation_rate) ** years)

    @staticmethod
    def calculate_future_value_with_inflation(amount: float,
                                            years: int,
                                            inflation_rate: float) -> float:
        """计算考虑通胀的未来价值"""
        return amount * ((1 - inflation_rate) ** years)

    @staticmethod
    def calculate_real_return_rate(nominal_rate: float,
                                 inflation_rate: float) -> float:
        """计算实际回报率（名义回报率 - 通胀率）"""
        return (1 + nominal_rate) / (1 + inflation_rate) - 1

    @staticmethod
    def generate_inflation_scenarios(base_amount: float,
                                   years: int,
                                   inflation_scenarios: List[float]) -> List[Tuple[float, List[float]]]:
        """生成不同通胀率下的金额变化"""
        results = []
        for inflation_rate in inflation_scenarios:
            amounts = []
            for year in range(years + 1):
                adjusted_amount = InflationCalculator.calculate_inflation_adjusted_amount(
                    base_amount, year, inflation_rate
                )
                amounts.append(adjusted_amount)
            results.append((inflation_rate, amounts))
        return results

    @staticmethod
    def calculate_purchasing_power_loss(amount: float,
                                      inflation_rate: float,
                                      years: int) -> float:
        """计算购买力损失"""
        future_value = amount * ((1 + inflation_rate) ** years)
        purchasing_power_loss = future_value - amount
        return purchasing_power_loss
