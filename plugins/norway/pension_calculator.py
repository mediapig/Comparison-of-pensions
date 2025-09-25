#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威退休金计算器
基于挪威Folketrygden系统
"""

import math
from typing import Dict, List, Optional
from datetime import date

from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class NorwayPensionCalculator:
    """挪威退休金计算器"""

    def __init__(self):
        self.country_code = 'NO'
        self.country_name = '挪威'
        self.currency = 'NOK'

        # 挪威养老金系统参数 (基于2024年政策)
        self.pension_parameters = {
            # 国家养老金 (Folketrygden)
            'national_employee_rate': 0.082,     # 员工缴费率 8.2%
            'national_employer_rate': 0.141,     # 雇主缴费率 14.1%
            'national_total_rate': 0.223,       # 总缴费率 22.3%
            'accrual_rate': 0.181,              # 养老金积累率 18.1%
            'g_basic_amount': 118620,            # G基础额 (2024年)
            'income_cap_multiplier': 7.1,       # 收入上限倍数 (G的7.1倍)
            'minimum_pension': 200000,           # 最低养老金 (年)
            'maximum_pension': 1200000,          # 最高养老金 (年)
            'retirement_age': 67,                # 退休年龄
            'early_retirement_age': 62,          # 提前退休年龄
            'late_retirement_age': 75,           # 延迟退休年龄

            # 职业养老金 (OTP)
            'otp_minimum_employer_rate': 0.02,   # 雇主最低缴费率 2%
            'otp_default_employer_rate': 0.05,   # 默认雇主缴费率 5%
            'otp_default_employee_rate': 0.03,   # 默认员工缴费率 3%

            # 个人养老金 (IPS)
            'ips_annual_limit': 15000,           # 年缴费上限 NOK 15,000
            'ips_default_contribution': 0        # 默认不缴费
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """
        计算挪威退休金

        Args:
            person: 个人信息
            salary_profile: 工资档案
            economic_factors: 经济因素

        Returns:
            退休金计算结果
        """
        # 计算工作年限
        work_years = person.work_years
        if work_years <= 0:
            # 默认从30岁工作到67岁退休，共37年
            work_years = 67 - person.age if person.age < 67 else 37

        # 计算退休年龄
        retirement_age = self.pension_parameters['retirement_age']

        # 计算平均工资 (考虑工资增长)
        avg_salary = self._calculate_average_salary(salary_profile, work_years)

        # 计算三支柱养老金
        national_pension = self._calculate_national_pension(
            salary_profile, work_years, economic_factors
        )

        occupational_pension = self._calculate_occupational_pension(
            salary_profile, work_years, economic_factors
        )

        individual_pension = self._calculate_individual_pension(
            salary_profile, work_years, economic_factors
        )

        # 计算总缴费 (社保缴费 + 职业养老金缴费 + 个人养老金缴费)
        total_contribution = (national_pension['total_ss_contribution'] +
                            occupational_pension['total_contribution'] +
                            individual_pension['total_contribution'])

        # 计算总月退休金
        monthly_pension = (national_pension['monthly_pension'] +
                         occupational_pension['monthly_pension'] +
                         individual_pension['monthly_pension'])

        # 计算总收益
        total_benefit = self._calculate_total_benefit(
            monthly_pension, person.age, retirement_age, economic_factors
        )

        # 计算ROI
        roi = self._calculate_roi(total_contribution, total_benefit, work_years)

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_contribution, monthly_pension, economic_factors
        )

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            retirement_account_balance=occupational_pension.get('total_balance', 0) + individual_pension.get('total_balance', 0),
            original_currency=self.currency,
            details={
                'work_years': work_years,
                'average_salary': avg_salary,
                'retirement_age': retirement_age,
                'pension_parameters': self.pension_parameters.copy(),
                'national_pension': national_pension,
                'occupational_pension': occupational_pension,
                'individual_pension': individual_pension
            }
        )

    def _calculate_average_salary(self, salary_profile: SalaryProfile, work_years: int) -> float:
        """计算平均工资"""
        if work_years <= 1:
            return salary_profile.monthly_salary * 12

        # 考虑工资增长的平均工资
        total_salary = 0
        for year in range(work_years):
            year_salary = salary_profile.monthly_salary * 12 * (1 + salary_profile.annual_growth_rate) ** year
            total_salary += year_salary

        return total_salary / work_years

    def _calculate_total_contribution(self,
                                     salary_profile: SalaryProfile,
                                     work_years: int,
                                     economic_factors: EconomicFactors) -> float:
        """计算总缴费"""
        total_contribution = 0

        for year in range(work_years):
            # 计算该年度的年工资
            year_salary = salary_profile.monthly_salary * 12 * (1 + salary_profile.annual_growth_rate) ** year

            # 计算该年度的缴费 (员工+雇主)
            year_contribution = year_salary * self.pension_parameters['total_rate']

            # 考虑通胀调整
            inflation_adjusted = year_contribution * (1 + economic_factors.inflation_rate) ** (work_years - year)
            total_contribution += inflation_adjusted

        return total_contribution

    def _calculate_monthly_pension(self,
                                 avg_salary: float,
                                 work_years: int,
                                 economic_factors: EconomicFactors) -> float:
        """计算月退休金"""
        # 挪威养老金计算公式: 平均工资 × 积累率 × 工作年限
        annual_pension = avg_salary * self.pension_parameters['accrual_rate'] * work_years

        # 应用最低和最高限制
        annual_pension = max(
            self.pension_parameters['minimum_pension'],
            min(annual_pension, self.pension_parameters['maximum_pension'])
        )

        # 转换为月退休金
        monthly_pension = annual_pension / 12

        return monthly_pension

    def _calculate_total_benefit(self,
                               monthly_pension: float,
                               current_age: int,
                               retirement_age: int,
                               economic_factors: EconomicFactors) -> float:
        """计算总收益"""
        # 假设平均寿命为85岁
        life_expectancy = 85
        pension_years = life_expectancy - retirement_age

        if pension_years <= 0:
            return 0

        # 计算总收益 (考虑通胀)
        total_benefit = 0
        for year in range(pension_years):
            year_benefit = monthly_pension * 12 * (1 - economic_factors.inflation_rate) ** year
            total_benefit += year_benefit

        return total_benefit

    def _calculate_roi(self, total_contribution: float, total_benefit: float, work_years: int) -> float:
        """计算投资回报率"""
        if total_contribution <= 0:
            return 0

        # 简单ROI计算: (总收益 - 总缴费) / 总缴费 * 100
        roi = (total_benefit - total_contribution) / total_contribution * 100
        return roi

    def _calculate_break_even_age(self,
                                total_contribution: float,
                                monthly_pension: float,
                                economic_factors: EconomicFactors) -> Optional[int]:
        """计算回本年龄"""
        if monthly_pension <= 0:
            return None

        # 计算回本需要的年数
        annual_pension = monthly_pension * 12

        # 考虑通胀调整
        years_to_break_even = 0
        accumulated_benefit = 0

        while accumulated_benefit < total_contribution and years_to_break_even < 50:
            year_benefit = annual_pension * (1 - economic_factors.inflation_rate) ** years_to_break_even
            accumulated_benefit += year_benefit
            years_to_break_even += 1

        if accumulated_benefit >= total_contribution:
            return self.pension_parameters['retirement_age'] + years_to_break_even

        return None

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict]:
        """计算缴费历史"""
        history = []
        work_years = person.work_years

        for year in range(work_years):
            # 计算该年度的工资
            year_salary = salary_profile.monthly_salary * 12 * (1 + salary_profile.annual_growth_rate) ** year

            # 计算该年度的缴费
            employee_contribution = year_salary * self.pension_parameters['employee_rate']
            employer_contribution = year_salary * self.pension_parameters['employer_rate']
            total_contribution = employee_contribution + employer_contribution

            history.append({
                'year': year + 1,
                'annual_salary': year_salary,
                'employee_contribution': employee_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_national_pension(self,
                                  salary_profile: SalaryProfile,
                                  work_years: int,
                                  economic_factors: EconomicFactors) -> Dict:
        """计算国家养老金 (Folketrygden)"""
        # 计算收入上限 (7.1G)
        income_cap = self.pension_parameters['g_basic_amount'] * self.pension_parameters['income_cap_multiplier']

        # 计算年度工资
        annual_salary = salary_profile.monthly_salary * 12
        capped_salary = min(annual_salary, income_cap)

        # 1. 社保缴费 (进入公共统筹，不是个人账户)
        annual_employee_ss_contribution = annual_salary * self.pension_parameters['national_employee_rate']  # 8.2%
        annual_employer_ss_contribution = annual_salary * self.pension_parameters['national_employer_rate']  # 14.1%
        annual_total_ss_contribution = annual_employee_ss_contribution + annual_employer_ss_contribution

        # 2. 养老金计提 (基于18.1%的积累率，进入名义账户)
        # 工资增长设置为0
        wage_index_growth = 0.0
        total_pension_accrual = 0
        
        for year in range(work_years):
            # 每年工资不变
            year_salary = annual_salary
            year_capped_salary = min(year_salary, income_cap)
            year_accrual = year_capped_salary * self.pension_parameters['accrual_rate']
            total_pension_accrual += year_accrual

        # 3. 计算退休金 (基于累积额和分配系数)
        # 67岁退休的分配系数约为21年 (预期寿命调整)
        distribution_factor = 21  # 67岁退休，预期寿命约88岁
        annual_pension = total_pension_accrual / distribution_factor

        # 应用最低和最高限制
        annual_pension = max(
            self.pension_parameters['minimum_pension'],
            min(annual_pension, self.pension_parameters['maximum_pension'])
        )
        monthly_pension = annual_pension / 12

        return {
            'name': '国家养老金 (Folketrygden)',
            'annual_employee_ss_contribution': annual_employee_ss_contribution,  # 社保缴费
            'annual_employer_ss_contribution': annual_employer_ss_contribution,  # 社保缴费
            'annual_total_ss_contribution': annual_total_ss_contribution,        # 社保缴费
            'total_ss_contribution': annual_total_ss_contribution * work_years,  # 终身社保缴费
            'annual_pension_accrual': annual_salary * self.pension_parameters['accrual_rate'],  # 年度养老金计提
            'total_pension_accrual': total_pension_accrual,                      # 终身养老金计提
            'monthly_pension': monthly_pension,
            'annual_pension': annual_pension,
            'income_cap': income_cap,
            'capped_salary': capped_salary,
            'distribution_factor': distribution_factor
        }

    def _calculate_occupational_pension(self,
                                      salary_profile: SalaryProfile,
                                      work_years: int,
                                      economic_factors: EconomicFactors) -> Dict:
        """计算职业养老金 (OTP)"""
        annual_salary = salary_profile.monthly_salary * 12
        g_amount = self.pension_parameters['g_basic_amount']

        # 按G分段计算缴费基数
        # 1G = 118,620 NOK, 7.1G = 842,202 NOK, 12G = 1,423,440 NOK
        segment_1g_7_1g = min(annual_salary, 7.1 * g_amount) - g_amount  # 1G-7.1G区间
        segment_7_1g_12g = max(0, min(annual_salary, 12 * g_amount) - 7.1 * g_amount)  # 7.1G-12G区间

        # 分段缴费率 (示例计划)
        # 1G-7.1G区间：雇主5%
        # 7.1G-12G区间：雇主18.1%
        # 员工缴费归入IPS，不在此计算
        employer_rate_1_7_1g = 0.05
        employer_rate_7_1g_12g = 0.181

        # 计算年度缴费 (仅雇主缴费)
        annual_employer_contribution = (segment_1g_7_1g * employer_rate_1_7_1g +
                                      segment_7_1g_12g * employer_rate_7_1g_12g)
        annual_total_contribution = annual_employer_contribution

        # 计算终身缴费
        total_contribution = annual_total_contribution * work_years

        # 计算投资收益 (使用更保守的5%年化回报)
        investment_return = 0.05
        # 使用年金终值公式：FV = PMT × [((1+r)^n - 1) / r]
        # 其中PMT是年度缴费，r是投资回报率，n是年数
        if investment_return > 0:
            total_balance = annual_total_contribution * (((1 + investment_return) ** work_years - 1) / investment_return)
        else:
            total_balance = annual_total_contribution * work_years

        # 计算月退休金 (4%提取规则)
        monthly_pension = (total_balance * 0.04) / 12

        return {
            'name': '职业养老金 (OTP)',
            'employer_rate_1_7_1g': employer_rate_1_7_1g,
            'employer_rate_7_1g_12g': employer_rate_7_1g_12g,
            'segment_1g_7_1g': segment_1g_7_1g,
            'segment_7_1g_12g': segment_7_1g_12g,
            'annual_employer_contribution': annual_employer_contribution,
            'annual_total_contribution': annual_total_contribution,
            'total_contribution': total_contribution,
            'total_balance': total_balance,
            'monthly_pension': monthly_pension,
            'annual_pension': monthly_pension * 12
        }

    def _calculate_individual_pension(self,
                                    salary_profile: SalaryProfile,
                                    work_years: int,
                                    economic_factors: EconomicFactors) -> Dict:
        """计算个人养老金 (IPS)"""
        # 员工自愿缴费3% (从OTP移到这里)
        annual_salary = salary_profile.monthly_salary * 12
        employee_contribution_rate = 0.03  # 员工自愿缴费3%
        annual_contribution = annual_salary * employee_contribution_rate
        total_contribution = annual_contribution * work_years

        # 如果有缴费，计算投资收益 (使用保守的4%年化回报)
        if annual_contribution > 0:
            investment_return = 0.04  # 更保守的回报率
            # 使用年金终值公式
            if investment_return > 0:
                total_balance = annual_contribution * (((1 + investment_return) ** work_years - 1) / investment_return)
            else:
                total_balance = annual_contribution * work_years

            # 计算月退休金 (4%提取规则)
            monthly_pension = (total_balance * 0.04) / 12
        else:
            total_balance = 0
            monthly_pension = 0

        return {
            'name': '个人养老金 (IPS)',
            'employee_contribution_rate': employee_contribution_rate,
            'annual_contribution': annual_contribution,
            'total_contribution': total_contribution,
            'total_balance': total_balance,
            'monthly_pension': monthly_pension,
            'annual_pension': monthly_pension * 12,
            'annual_limit': self.pension_parameters['ips_annual_limit']
        }