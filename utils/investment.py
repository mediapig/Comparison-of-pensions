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
    def calculate_compound_annual_growth_rate(beginning_value: float,
                                            ending_value: float,
                                            years: int) -> float:
        """计算复合年增长率 (CAGR)"""
        if beginning_value <= 0 or years <= 0:
            return 0.0
        return (ending_value / beginning_value) ** (1 / years) - 1

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

    @staticmethod
    def calculate_portfolio_volatility(returns: List[float]) -> float:
        """计算投资组合波动率"""
        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        squared_deviations = [(r - mean_return) ** 2 for r in returns]
        variance = np.mean(squared_deviations)
        volatility = np.sqrt(variance)

        return volatility

    @staticmethod
    def calculate_sharpe_ratio(returns: List[float],
                              risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if not returns:
            return 0.0

        mean_return = np.mean(returns)
        volatility = InvestmentCalculator.calculate_portfolio_volatility(returns)

        if volatility == 0:
            return 0.0

        excess_return = mean_return - risk_free_rate
        sharpe_ratio = excess_return / volatility

        return sharpe_ratio

    @staticmethod
    def monte_carlo_simulation(initial_investment: float,
                              monthly_contribution: float,
                              years: int,
                              mean_return: float,
                              volatility: float,
                              simulations: int = 1000) -> Dict[str, Any]:
        """蒙特卡洛模拟投资结果"""
        results = []

        for _ in range(simulations):
            portfolio_value = initial_investment

            for month in range(years * 12):
                # 生成随机月度回报
                monthly_return = np.random.normal(mean_return / 12, volatility / np.sqrt(12))
                portfolio_value = portfolio_value * (1 + monthly_return) + monthly_contribution

            results.append(portfolio_value)

        # 计算统计信息
        mean_result = np.mean(results)
        median_result = np.median(results)
        std_result = np.std(results)

        # 计算分位数
        percentiles = [5, 25, 50, 75, 95]
        percentile_values = np.percentile(results, percentiles)

        return {
            'mean': mean_result,
            'median': median_result,
            'std': std_result,
            'percentiles': dict(zip(percentiles, percentile_values)),
            'all_results': results
        }

    @staticmethod
    def calculate_sequence_of_returns_risk(returns: List[float],
                                         withdrawal_rate: float = 0.04) -> Dict[str, Any]:
        """计算序列回报风险"""
        if len(returns) < 2:
            return {'risk_score': 0, 'worst_case': 0, 'best_case': 0}

        # 计算所有可能的回报序列
        portfolio_values = []
        initial_value = 1000000  # 假设初始投资100万

        for i in range(len(returns)):
            portfolio_value = initial_value
            for j in range(i, len(returns)):
                portfolio_value = portfolio_value * (1 + returns[j]) - (initial_value * withdrawal_rate)
                if portfolio_value <= 0:
                    break
            portfolio_values.append(portfolio_value)

        worst_case = min(portfolio_values)
        best_case = max(portfolio_values)

        # 计算风险评分（0-100，越高越危险）
        risk_score = max(0, min(100, (initial_value - worst_case) / initial_value * 100))

        return {
            'risk_score': risk_score,
            'worst_case': worst_case,
            'best_case': best_case,
            'portfolio_values': portfolio_values
        }
