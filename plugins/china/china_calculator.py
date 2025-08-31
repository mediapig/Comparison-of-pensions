from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class ChinaPensionCalculator(BasePensionCalculator):
    """中国退休金计算器"""

    def __init__(self):
        super().__init__("CN", "中国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取中国退休年龄"""
        return {
            "male": 60,
            "female": 55
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取中国缴费比例"""
        return {
            "employee": 0.08,        # 个人缴费比例 8%
            "civil_servant": 0.08,   # 公务员个人缴费比例 8%
            "self_employed": 0.20,   # 自由职业者缴费比例 20%
            "farmer": 0.10,          # 农民缴费比例 10%
            "employer": 0.16,        # 单位缴费比例 16%
            "total": 0.24            # 总缴费比例 24%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算中国退休金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            # 已经退休
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算个人账户养老金
        personal_account_pension = self._calculate_personal_account_pension(
            contribution_history, economic_factors
        )

        # 计算基础养老金
        basic_pension = self._calculate_basic_pension(
            person, salary_profile, work_years, economic_factors
        )

        # 总月退休金
        monthly_pension = personal_account_pension + basic_pension

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
            original_currency="CNY",
            details={
                'personal_account_pension': personal_account_pension,
                'basic_pension': basic_pension,
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

            # 社保缴费基数（通常有上下限）
            # 2024年北京社保缴费基数下限：5869元，上限：31884元
            social_base = min(max(salary, 5869), 31884)

            # 个人缴费 8%
            personal_contribution = social_base * 0.08 * 12

            # 单位缴费 16%
            employer_contribution = social_base * 0.16 * 12

            # 个人账户计入（个人缴费8% + 单位缴费的8%）
            personal_account_contribution = personal_contribution + (employer_contribution * 0.5)

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'social_base': social_base,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'personal_account_contribution': personal_account_contribution
            })

        return history

    def _calculate_personal_account_pension(self,
                                          contribution_history: List[Dict[str, Any]],
                                          economic_factors: EconomicFactors) -> float:
        """计算个人账户养老金"""
        total_contribution = sum(record['personal_account_contribution'] for record in contribution_history)

        # 考虑投资回报
        avg_years = len(contribution_history) / 2
        future_value = self.calculate_future_value(
            total_contribution, avg_years, economic_factors.social_security_return_rate
        )

        # 个人账户养老金 = 账户余额 / 计发月数
        # 根据退休年龄确定计发月数
        # 60岁退休：139个月，55岁退休：170个月，50岁退休：195个月
        retirement_age = 60  # 假设男性60岁退休
        if retirement_age == 60:
            months = 139
        elif retirement_age == 55:
            months = 170
        elif retirement_age == 50:
            months = 195
        else:
            months = 139  # 默认值

        return future_value / months

    def _calculate_basic_pension(self,
                               person: Person,
                               salary_profile: SalaryProfile,
                               work_years: int,
                               economic_factors: EconomicFactors) -> float:
        """计算基础养老金"""
        # 基础养老金 = (全省上年度在岗职工月平均工资 + 本人指数化月平均缴费工资) / 2 × 缴费年限 × 1%

        # 假设全省平均工资
        avg_social_salary = 8000  # 这个值应该根据实际情况调整

        # 计算本人指数化月平均缴费工资
        total_indexed_salary = 0
        for year in range(work_years):
            age = person.age + year
            salary = salary_profile.get_salary_at_age(age, person.age)
            # 简化计算，假设指数为1
            total_indexed_salary += salary

        avg_indexed_salary = total_indexed_salary / work_years

        # 基础养老金
        basic_pension = (avg_social_salary + avg_indexed_salary) / 2 * work_years * 0.01

        return basic_pension

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
