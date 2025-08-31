from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class USAPensionCalculator(BasePensionCalculator):
    """美国退休金计算器（社会保障金）"""

    def __init__(self):
        super().__init__("US", "美国")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取美国退休年龄"""
        return {
            "male": 67,  # 完全退休年龄
            "female": 67
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取美国缴费比例"""
        return {
            "employee": 0.062,      # 6.2% 社会保障税
            "civil_servant": 0.062,
            "self_employed": 0.124,  # 自雇人士缴纳12.4%
            "farmer": 0.062
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算美国社会保障金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算平均指数化月收入 (AIME)
        aime = self._calculate_aime(contribution_history, economic_factors)

        # 计算主要保险金额 (PIA)
        pia = self._calculate_pia(aime, retirement_age)

        # 月退休金
        monthly_pension = pia

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
            details={
                'aime': aime,
                'pia': pia,
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

            # 美国社会保障税有上限（2024年约为$168,600）
            social_security_cap = 168600

            # 应税工资
            taxable_wage = min(salary, social_security_cap)

            # 个人缴费（6.2%）
            personal_contribution = taxable_wage * 0.062 * 12

            # 雇主缴费（6.2%）
            employer_contribution = taxable_wage * 0.062 * 12

            # 总缴费
            total_contribution = personal_contribution + employer_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'taxable_wage': taxable_wage,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution,
                'total_contribution': total_contribution
            })

        return history

    def _calculate_aime(self,
                       contribution_history: List[Dict[str, Any]],
                       economic_factors: EconomicFactors) -> float:
        """计算平均指数化月收入 (AIME)"""
        if not contribution_history:
            return 0

        # 获取最高的35年收入
        yearly_earnings = []
        for record in contribution_history:
            yearly_earnings.append({
                'year': record['year'],
                'taxable_wage': record['taxable_wage']
            })

        # 按年份排序
        yearly_earnings.sort(key=lambda x: x['year'])

        # 计算指数化收入
        indexed_earnings = []
        for i, earning in enumerate(yearly_earnings):
            # 简化的指数化计算（实际应该使用官方指数）
            years_to_retirement = len(yearly_earnings) - i - 1
            indexed_wage = earning['taxable_wage'] * (1 + economic_factors.inflation_rate) ** years_to_retirement
            indexed_earnings.append(indexed_wage)

        # 取最高的35年（如果不足35年，用0填充）
        while len(indexed_earnings) < 35:
            indexed_earnings.append(0)

        # 排序并取最高的35年
        indexed_earnings.sort(reverse=True)
        top_35_earnings = indexed_earnings[:35]

        # 计算AIME
        total_indexed_earnings = sum(top_35_earnings)
        aime = total_indexed_earnings / (35 * 12)  # 转换为月收入

        return aime

    def _calculate_pia(self, aime: float, retirement_age: int) -> float:
        """计算主要保险金额 (PIA)"""
        # 2024年的PIA计算（简化版）
        # 实际计算更复杂，这里使用近似值

        if aime <= 1174:
            pia = aime * 0.90
        elif aime <= 7078:
            pia = 1174 * 0.90 + (aime - 1174) * 0.32
        else:
            pia = 1174 * 0.90 + (7078 - 1174) * 0.32 + (aime - 7078) * 0.15

        # 如果提前退休，会有减少
        if retirement_age < 67:
            reduction_months = (67 - retirement_age) * 12
            reduction_rate = 0.00556  # 每月减少0.556%
            pia = pia * (1 - reduction_rate * reduction_months)

        return pia

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
