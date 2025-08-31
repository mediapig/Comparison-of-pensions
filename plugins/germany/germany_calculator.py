from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class GermanyPensionCalculator(BasePensionCalculator):
    """德国退休金计算器（俾斯麦模式）"""

    def __init__(self):
        super().__init__("DE", "德国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取德国退休年龄"""
        return {
            "male": 67,      # 2029年后统一为67岁
            "female": 67
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取德国缴费比例"""
        return {
            "employee": 0.093,       # 9.3% 个人缴费
            "civil_servant": 0.093,  # 公务员缴费比例
            "self_employed": 0.186,  # 自雇人士缴纳18.6%
            "farmer": 0.093,         # 农民缴费比例
            "employer": 0.093,       # 雇主缴费比例 9.3%
            "total": 0.186           # 总缴费比例 18.6%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算德国退休金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算退休金点数
        pension_points = self._calculate_pension_points(
            contribution_history, economic_factors
        )

        # 计算月退休金
        monthly_pension = self._calculate_monthly_pension(
            pension_points, retirement_age, economic_factors
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
            original_currency="EUR",
            details={
                'pension_points': pension_points,
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

            # 德国有缴费上限（2024年约为87,600欧元）
            contribution_ceiling = 87600
            taxable_salary = min(salary * 12, contribution_ceiling)

            # 个人缴费（9.3%）
            personal_contribution = taxable_salary * 0.093

            # 雇主缴费（9.3%）
            employer_contribution = taxable_salary * 0.093

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'taxable_salary': taxable_salary,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_pension_points(self,
                                contribution_history: List[Dict[str, Any]],
                                economic_factors: EconomicFactors) -> float:
        """计算退休金点数"""
        if not contribution_history:
            return 0

        total_points = 0

        for record in contribution_history:
            # 德国退休金点数计算
            # 点数 = (个人缴费 / 基准缴费) * 1.0

            # 基准缴费（假设为平均工资的9.3%）
            base_contribution = 50000 * 0.093  # 假设平均工资5万欧元

            if base_contribution > 0:
                points = (record['personal_contribution'] / base_contribution)
                total_points += points

        return total_points

    def _calculate_monthly_pension(self,
                                 pension_points: float,
                                 retirement_age: int,
                                 economic_factors: EconomicFactors) -> float:
        """计算月退休金"""
        # 德国退休金计算公式
        # 月退休金 = 退休金点数 × 退休金点数价值 × 退休年龄调整系数

        # 退休金点数价值（2024年约为37.60欧元）
        point_value = 37.60

        # 退休年龄调整系数
        if retirement_age < 67:
            # 提前退休减少
            reduction_months = (67 - retirement_age) * 12
            reduction_rate = 0.003  # 每月减少0.3%
            age_factor = 1 - (reduction_rate * reduction_months)
        elif retirement_age > 67:
            # 延迟退休增加
            bonus_months = (retirement_age - 67) * 12
            bonus_rate = 0.005  # 每月增加0.5%
            age_factor = 1 + (bonus_rate * bonus_months)
        else:
            age_factor = 1.0

        # 计算月退休金
        monthly_pension = pension_points * point_value * age_factor

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
