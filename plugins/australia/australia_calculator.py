from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class AustraliaPensionCalculator(BasePensionCalculator):
    """澳大利亚退休金计算器（超级年金）"""

    def __init__(self):
        super().__init__("AU", "澳大利亚")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取澳大利亚退休年龄"""
        return {
            "male": 67,      # 超级年金提取年龄
            "female": 67
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取澳大利亚缴费比例"""
        return {
            "employee": 0.105,       # 10.5% 雇主强制缴费
            "civil_servant": 0.105,  # 公务员缴费比例
            "self_employed": 0.105,  # 自雇人士缴费比例
            "farmer": 0.105          # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算澳大利亚超级年金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算超级年金账户余额
        super_balance = self._calculate_super_balance(
            contribution_history, economic_factors
        )

        # 计算月退休金（年金方式）
        monthly_pension = self._calculate_super_pension(
            super_balance, retirement_age, economic_factors
        )

        # 计算总缴费
        total_contribution = sum(record['employer_contribution'] for record in contribution_history)

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
            original_currency="AUD",
            details={
                'super_balance': super_balance,
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

            # 澳大利亚超级年金有缴费上限（2024年约为27,500澳币）
            concessional_cap = 27500

            # 雇主强制缴费（10.5%）
            employer_contribution = min(salary * 0.105, concessional_cap)

            # 个人自愿缴费（可选）
            personal_contribution = 0  # 假设无个人缴费

            # 总缴费
            total_contribution = employer_contribution + personal_contribution

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary,
                'employer_contribution': employer_contribution * 12,
                'personal_contribution': personal_contribution * 12,
                'total_contribution': total_contribution * 12
            })

        return history

    def _calculate_super_balance(self,
                               contribution_history: List[Dict[str, Any]],
                               economic_factors: EconomicFactors) -> float:
        """计算超级年金账户余额"""
        if not contribution_history:
            return 0

        total_balance = 0

        for i, record in enumerate(contribution_history):
            # 计算每笔缴费的未来价值
            years_to_retirement = len(contribution_history) - i - 1
            future_value = self.calculate_future_value(
                record['total_contribution'], years_to_retirement,
                economic_factors.investment_return_rate
            )
            total_balance += future_value

        return total_balance

    def _calculate_super_pension(self,
                               super_balance: float,
                               retirement_age: int,
                               economic_factors: EconomicFactors) -> float:
        """计算超级年金养老金"""
        # 澳大利亚超级年金养老金计算
        # 使用4%提取率（安全提取率）

        withdrawal_rate = 0.04  # 4% 年提取率

        # 年龄调整系数
        if retirement_age < 67:
            age_factor = 0.9
        elif retirement_age > 67:
            age_factor = 1.1
        else:
            age_factor = 1.0

        # 计算年退休金
        annual_pension = super_balance * withdrawal_rate * age_factor
        monthly_pension = annual_pension / 12

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
