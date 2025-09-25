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
            work_years = 1

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
        
        # 计算总缴费
        total_contribution = (national_pension['total_contribution'] + 
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
        # 计算收入上限
        income_cap = self.pension_parameters['g_basic_amount'] * self.pension_parameters['income_cap_multiplier']
        
        # 计算年度缴费
        annual_salary = salary_profile.monthly_salary * 12
        capped_salary = min(annual_salary, income_cap)
        
        # 计算年度缴费
        annual_employee_contribution = capped_salary * self.pension_parameters['national_employee_rate']
        annual_employer_contribution = capped_salary * self.pension_parameters['national_employer_rate']
        annual_total_contribution = annual_employee_contribution + annual_employer_contribution
        
        # 计算终身缴费
        total_contribution = annual_total_contribution * work_years
        
        # 计算养老金积累 (基于18.1%的积累率)
        annual_pension_accrual = capped_salary * self.pension_parameters['accrual_rate']
        total_pension_accrual = annual_pension_accrual * work_years
        
        # 计算月退休金 (简化计算)
        monthly_pension = total_pension_accrual / 12 / 20  # 假设20年退休期
        
        # 应用最低和最高限制
        annual_pension = monthly_pension * 12
        annual_pension = max(
            self.pension_parameters['minimum_pension'],
            min(annual_pension, self.pension_parameters['maximum_pension'])
        )
        monthly_pension = annual_pension / 12
        
        return {
            'name': '国家养老金 (Folketrygden)',
            'annual_employee_contribution': annual_employee_contribution,
            'annual_employer_contribution': annual_employer_contribution,
            'annual_total_contribution': annual_total_contribution,
            'total_contribution': total_contribution,
            'monthly_pension': monthly_pension,
            'annual_pension': annual_pension,
            'income_cap': income_cap,
            'capped_salary': capped_salary
        }

    def _calculate_occupational_pension(self, 
                                      salary_profile: SalaryProfile, 
                                      work_years: int,
                                      economic_factors: EconomicFactors) -> Dict:
        """计算职业养老金 (OTP)"""
        annual_salary = salary_profile.monthly_salary * 12
        
        # 使用默认缴费率
        employee_rate = self.pension_parameters['otp_default_employee_rate']
        employer_rate = self.pension_parameters['otp_default_employer_rate']
        
        # 计算年度缴费
        annual_employee_contribution = annual_salary * employee_rate
        annual_employer_contribution = annual_salary * employer_rate
        annual_total_contribution = annual_employee_contribution + annual_employer_contribution
        
        # 计算终身缴费
        total_contribution = annual_total_contribution * work_years
        
        # 计算投资收益 (假设7%年化回报)
        investment_return = 0.07
        total_balance = 0
        for year in range(work_years):
            year_contribution = annual_total_contribution * (1 + salary_profile.annual_growth_rate) ** year
            total_balance = (total_balance + year_contribution) * (1 + investment_return)
        
        # 计算月退休金 (4%提取规则)
        monthly_pension = (total_balance * 0.04) / 12
        
        return {
            'name': '职业养老金 (OTP)',
            'employee_rate': employee_rate,
            'employer_rate': employer_rate,
            'annual_employee_contribution': annual_employee_contribution,
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
        # 默认不缴费，但提供计算框架
        annual_contribution = self.pension_parameters['ips_default_contribution']
        total_contribution = annual_contribution * work_years
        
        # 如果有缴费，计算投资收益
        if annual_contribution > 0:
            investment_return = 0.07
            total_balance = 0
            for year in range(work_years):
                year_contribution = annual_contribution * (1 + salary_profile.annual_growth_rate) ** year
                total_balance = (total_balance + year_contribution) * (1 + investment_return)
            
            # 计算月退休金 (4%提取规则)
            monthly_pension = (total_balance * 0.04) / 12
        else:
            total_balance = 0
            monthly_pension = 0
        
        return {
            'name': '个人养老金 (IPS)',
            'annual_contribution': annual_contribution,
            'total_contribution': total_contribution,
            'total_balance': total_balance,
            'monthly_pension': monthly_pension,
            'annual_pension': monthly_pension * 12,
            'annual_limit': self.pension_parameters['ips_annual_limit']
        }