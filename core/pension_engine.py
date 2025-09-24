#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from .base_calculator import BasePensionCalculator
from .models import Person, SalaryProfile, EconomicFactors, PensionResult

class PensionEngine:
    """退休金计算引擎"""

    def __init__(self):
        self.calculators: Dict[str, BasePensionCalculator] = {}
        self.comparison_results: Dict[str, Any] = {}

    def register_calculator(self, calculator: BasePensionCalculator):
        """注册退休金计算器"""
        country_code = getattr(calculator, 'country_code', None) or getattr(calculator, 'COUNTRY_CODE', None)
        country_name = getattr(calculator, 'country_name', None) or getattr(calculator, 'COUNTRY_NAME', None)
        self.calculators[country_code] = calculator
        print(f"已注册 {country_name} ({country_code}) 计算器")

    def get_available_countries(self) -> List[str]:
        """获取可用的国家列表"""
        return list(self.calculators.keys())

    def calculate_all_countries(self,
                              person: Person,
                              salary_profile: SalaryProfile,
                              economic_factors: EconomicFactors) -> Dict[str, PensionResult]:
        """计算所有国家的退休金"""
        results = {}
        for country_code, calculator in self.calculators.items():
            try:
                result = calculator.calculate_pension(person, salary_profile, economic_factors)
                results[country_code] = result
            except Exception as e:
                print(f"计算 {country_code} 退休金时出错: {e}")
                results[country_code] = None
        return results

    def compare_pensions(self,
                        person: Person,
                        salary_profile: SalaryProfile,
                        economic_factors: EconomicFactors) -> pd.DataFrame:
        """对比不同国家的退休金"""
        results = self.calculate_all_countries(person, salary_profile, economic_factors)

        # 导入汇率转换器
        from utils.currency_converter import converter

        comparison_data = []
        for country_code, result in results.items():
            if result:
                # 转换为显示货币
                if result.original_currency != economic_factors.display_currency:
                    result = result.convert_to_currency(economic_factors.display_currency, converter)

                comparison_data.append({
                    'country': country_code,
                    'country_name': self.calculators[country_code].country_name,
                    'monthly_pension': result.monthly_pension,
                    'total_contribution': result.total_contribution,
                    'total_benefit': result.total_benefit,
                    'roi': result.roi,
                    'break_even_age': result.break_even_age,
                    'currency': result.original_currency
                })

        df = pd.DataFrame(comparison_data)
        if not df.empty:
            df = df.sort_values('monthly_pension', ascending=False)

        return df

    def sensitivity_analysis(self,
                           person: Person,
                           salary_profile: SalaryProfile,
                           base_economic_factors: EconomicFactors,
                           parameter: str,
                           values: List[float]) -> pd.DataFrame:
        """敏感性分析"""
        analysis_data = []

        for value in values:
            # 创建新的经济因素对象
            new_factors = EconomicFactors(
                inflation_rate=base_economic_factors.inflation_rate,
                investment_return_rate=base_economic_factors.investment_return_rate,
                social_security_return_rate=base_economic_factors.social_security_return_rate,
                base_currency=base_economic_factors.base_currency,
                display_currency=base_economic_factors.display_currency
            )

            # 设置变化的参数
            if parameter == 'inflation_rate':
                new_factors.inflation_rate = value
            elif parameter == 'investment_return_rate':
                new_factors.investment_return_rate = value
            elif parameter == 'salary_growth':
                salary_profile.annual_growth_rate = value

            # 计算所有国家的结果
            results = self.calculate_all_countries(person, salary_profile, new_factors)

            for country_code, result in results.items():
                if result:
                    analysis_data.append({
                        'parameter': parameter,
                        'value': value,
                        'country': country_code,
                        'monthly_pension': result.monthly_pension,
                        'roi': result.roi
                    })

        return pd.DataFrame(analysis_data)

    def generate_report(self,
                       person: Person,
                       salary_profile: SalaryProfile,
                       economic_factors: EconomicFactors) -> Dict[str, Any]:
        """生成综合报告"""
        # 基础对比
        comparison_df = self.compare_pensions(person, salary_profile, economic_factors)

        # 敏感性分析
        inflation_analysis = self.sensitivity_analysis(
            person, salary_profile, economic_factors, 'inflation_rate',
            [0.01, 0.02, 0.03, 0.04, 0.05]
        )

        investment_analysis = self.sensitivity_analysis(
            person, salary_profile, economic_factors, 'investment_return_rate',
            [0.03, 0.05, 0.07, 0.09, 0.11]
        )

        # 缴费历史（选择一个国家作为示例）
        if self.calculators:
            first_calculator = list(self.calculators.values())[0]
            contribution_history = first_calculator.calculate_contribution_history(
                person, salary_profile, economic_factors
            )
        else:
            contribution_history = []

        return {
            'person_info': {
                'name': person.name,
                'age': person.age,
                'work_years': person.work_years,
                'retirement_age': first_calculator.get_retirement_age(person) if self.calculators else 65
            },
            'comparison': comparison_df.to_dict('records'),
            'sensitivity_analysis': {
                'inflation': inflation_analysis.to_dict('records'),
                'investment_return': investment_analysis.to_dict('records')
            },
            'contribution_history': contribution_history
        }
