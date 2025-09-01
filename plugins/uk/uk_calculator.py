from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class UKPensionCalculator(BasePensionCalculator):
    """英国退休金计算器（国家养老金）"""

    def __init__(self):
        super().__init__("UK", "英国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取英国退休年龄"""
        return {
            "male": 66,      # 国家养老金请领年龄
            "female": 66
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取英国缴费比例"""
        return {
            "employee": 0.12,        # 12% 国民保险缴费
            "civil_servant": 0.12,   # 公务员缴费比例
            "self_employed": 0.12,   # 自雇人士缴费比例
            "farmer": 0.12           # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算英国国家养老金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算国家养老金
        state_pension = self._calculate_state_pension(
            contribution_history, work_years, economic_factors
        )

        # 计算月退休金
        monthly_pension = state_pension

        # 计算总缴费
        total_contribution = sum(record['personal_contribution'] for record in contribution_history)

        # 计算总收益（假设活到85岁）
        life_expectancy = 85
        retirement_years = life_expectancy - retirement_age
        total_benefit = monthly_pension * 12 * retirement_years

        # 计算ROI
        roi = (total_benefit - total_contribution) / total_contribution if total_contribution > 0 else 0

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_contribution, monthly_pension, retirement_age
        )

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="GBP",
            details={
                'state_pension': state_pension,
                'work_years': work_years,
                'retirement_age': retirement_age
            }
        )

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        history = []
        current_age = person.age

        for year in range(work_years):
            age = current_age + year
            salary = salary_profile.get_salary_at_age(age, person.age)

            # 将人民币月薪转换为英镑
            cny_to_gbp_rate = 0.11  # 1 CNY = 0.11 GBP (2025年参考汇率)
            salary_gbp = salary * cny_to_gbp_rate

            # 英国国民保险有缴费上下限（2024年约为12,570-50,270英镑）
            ni_threshold = 12570
            ni_upper_limit = 50270

            # 计算应税收入
            if salary_gbp * 12 <= ni_threshold:
                taxable_income = 0
            elif salary_gbp * 12 <= ni_upper_limit:
                taxable_income = (salary_gbp * 12) - ni_threshold
            else:
                taxable_income = ni_upper_limit - ni_threshold

            # 个人缴费（12%）
            personal_contribution = taxable_income * 0.12

            # 雇主缴费（13.8%）
            employer_contribution = taxable_income * 0.138

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'taxable_income': taxable_income,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_state_pension(self,
                               contribution_history: List[Dict[str, Any]],
                               work_years: int,
                               economic_factors: EconomicFactors) -> float:
        """计算国家养老金"""
        # 英国国家养老金计算
        # 需要35年缴费才能获得全额养老金

        # 基础养老金金额（2024年约为185.15英镑/周）
        full_pension_weekly = 185.15
        full_pension_monthly = full_pension_weekly * 52 / 12

        # 根据缴费年限调整
        required_years = 35
        if work_years >= required_years:
            adjustment_factor = 1.0
        else:
            adjustment_factor = work_years / required_years

        monthly_pension = full_pension_monthly * adjustment_factor

        return monthly_pension

    def _calculate_break_even_age(self,
                                total_contribution: float,
                                monthly_pension: float,
                                retirement_age: int) -> int:
        """计算回本年龄"""
        if monthly_pension <= 0:
            return None

        months_to_break_even = total_contribution / monthly_pension
        years_to_break_even = months_to_break_even / 12

        return retirement_age + int(years_to_break_even)
