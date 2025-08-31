from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class JapanPensionCalculator(BasePensionCalculator):
    """日本退休金计算器（国民年金+厚生年金）"""

    def __init__(self):
        super().__init__("JP", "日本")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取日本退休年龄"""
        return {
            "male": 65,      # 厚生年金请领年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取日本缴费比例"""
        return {
            "employee": 0.0915,      # 9.15% 厚生年金缴费
            "civil_servant": 0.0915, # 公务员缴费比例
            "self_employed": 0.0165, # 国民年金缴费（月额）
            "farmer": 0.0165,        # 农民缴费比例
            "employer": 0.0915,      # 雇主缴费比例 9.15%
            "total": 0.183           # 总缴费比例 18.3%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算日本退休金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算国民年金
        national_pension = self._calculate_national_pension(work_years)

        # 计算厚生年金
        employee_pension = self._calculate_employee_pension(
            contribution_history, economic_factors
        )

        # 总月退休金
        monthly_pension = national_pension + employee_pension

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
            original_currency="JPY",
            details={
                'national_pension': national_pension,
                'employee_pension': employee_pension,
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

            # 日本厚生年金有缴费上下限（2024年约为98,000-650,000日元）
            min_contribution = 98000
            max_contribution = 650000

            # 个人缴费（9.15%）
            personal_contribution = min(max(salary * 0.0915, min_contribution * 0.0915),
                                      max_contribution * 0.0915)

            # 雇主缴费（9.15%）
            employer_contribution = personal_contribution

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'personal_contribution': personal_contribution * 12,
                'employer_contribution': employer_contribution * 12,
                'total_contribution': total_contribution * 12
            })

        return history

    def _calculate_national_pension(self, work_years: int) -> float:
        """计算国民年金"""
        # 国民年金定额部分（2024年约为65,000日元/月）
        base_amount = 65000

        # 根据缴费年限调整
        if work_years >= 40:
            adjustment_factor = 1.0
        else:
            adjustment_factor = work_years / 40

        monthly_pension = base_amount * adjustment_factor

        return monthly_pension

    def _calculate_employee_pension(self,
                                  contribution_history: List[Dict[str, Any]],
                                  economic_factors: EconomicFactors) -> float:
        """计算厚生年金"""
        if not contribution_history:
            return 0

        # 计算平均月收入
        total_salary = sum(record['salary'] for record in contribution_history)
        avg_monthly_salary = total_salary / len(contribution_history)

        # 厚生年金计算公式
        # 月年金 = 平均月收入 × 缴费年限 × 0.005481

        monthly_pension = avg_monthly_salary * len(contribution_history) * 0.005481

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
