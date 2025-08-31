from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class TaiwanPensionCalculator(BasePensionCalculator):
    """台湾退休金计算器（劳保年金）"""

    def __init__(self):
        super().__init__("TW", "台湾")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取台湾退休年龄"""
        return {
            "male": 65,      # 劳保年金请领年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取台湾缴费比例"""
        return {
            "employee": 0.20,        # 20% 总缴费比例（个人+雇主+政府）
            "civil_servant": 0.20,   # 公务员缴费比例
            "self_employed": 0.20,   # 自雇人士缴费比例
            "farmer": 0.20           # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算台湾劳保年金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算平均月投保薪资
        avg_insured_salary = self._calculate_average_insured_salary(contribution_history)

        # 计算劳保年金
        monthly_pension = self._calculate_labor_pension(
            avg_insured_salary, work_years, economic_factors
        )

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
            original_currency="TWD",
            details={
                'avg_insured_salary': avg_insured_salary,
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

            # 台湾劳保有投保薪资上下限（2024年约为25,250-45,800新台币）
            min_insured_salary = 25250
            max_insured_salary = 45800
            insured_salary = min(max(salary, min_insured_salary), max_insured_salary)

            # 总缴费（20%）
            total_contribution = insured_salary * 0.20 * 12

            # 个人缴费（约7%）
            personal_contribution = insured_salary * 0.07 * 12

            # 雇主缴费（约13%）
            employer_contribution = insured_salary * 0.13 * 12

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'insured_salary': insured_salary,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_average_insured_salary(self,
                                        contribution_history: List[Dict[str, Any]]) -> float:
        """计算平均月投保薪资"""
        if not contribution_history:
            return 0

        total_insured_salary = sum(record['insured_salary'] for record in contribution_history)
        return total_insured_salary / len(contribution_history)

    def _calculate_labor_pension(self,
                               avg_insured_salary: float,
                               work_years: int,
                               economic_factors: EconomicFactors) -> float:
        """计算劳保年金"""
        # 台湾劳保年金计算公式
        # 月年金 = 平均月投保薪资 × 年资 × 1.55% × 0.65

        # 基础年金
        base_pension = avg_insured_salary * work_years * 0.0155

        # 考虑投资回报的调整系数
        investment_factor = 0.65

        monthly_pension = base_pension * investment_factor

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
