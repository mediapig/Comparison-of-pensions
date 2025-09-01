from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class CanadaPensionCalculator(BasePensionCalculator):
    """加拿大退休金计算器（CPP+OAS）"""

    def __init__(self):
        super().__init__("CA", "加拿大")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取加拿大退休年龄"""
        return {
            "male": 65,      # CPP和OAS请领年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取加拿大缴费比例"""
        return {
            "employee": 0.0595,      # 5.95% CPP缴费
            "civil_servant": 0.0595, # 公务员缴费比例
            "self_employed": 0.119,  # 自雇人士缴纳11.9%
            "farmer": 0.0595         # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算加拿大退休金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算CPP
        cpp_pension = self._calculate_cpp_pension(
            contribution_history, economic_factors
        )

        # 计算OAS
        oas_pension = self._calculate_oas_pension(
            work_years, economic_factors
        )

        # 总月退休金
        monthly_pension = cpp_pension + oas_pension

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
            original_currency="CAD",
            details={
                'cpp_pension': cpp_pension,
                'oas_pension': oas_pension,
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

            # 将人民币月薪转换为加币
            cny_to_cad_rate = 0.19  # 1 CNY = 0.19 CAD (2025年参考汇率)
            salary_cad = salary * cny_to_cad_rate

            # 加拿大CPP有缴费上限（2024年约为66,600加币）
            cpp_ceiling = 66600

            # 应税工资
            taxable_wage = min(salary_cad * 12, cpp_ceiling)

            # 个人缴费（5.95%）
            personal_contribution = taxable_wage * 0.0595

            # 雇主缴费（5.95%）
            employer_contribution = taxable_wage * 0.0595

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

    def _calculate_cpp_pension(self,
                             contribution_history: List[Dict[str, Any]],
                             economic_factors: EconomicFactors) -> float:
        """计算CPP养老金"""
        if not contribution_history:
            return 0

        # 计算平均年收入
        total_taxable_wage = sum(record['taxable_wage'] for record in contribution_history)
        avg_annual_wage = total_taxable_wage / len(contribution_history)

        # CPP计算公式（简化版）
        # 月CPP = 平均年收入 × 25% × 缴费年限 / 40

        cpp_factor = 0.25  # 25% 替代率
        required_years = 40  # 需要40年缴费

        monthly_cpp = (avg_annual_wage * cpp_factor * len(contribution_history) / required_years) / 12

        return monthly_cpp

    def _calculate_oas_pension(self,
                              work_years: int,
                              economic_factors: EconomicFactors) -> float:
        """计算OAS养老金"""
        # OAS是基础养老金，需要40年居住才能获得全额

        # 全额OAS（2024年约为707.68加币/月）
        full_oas_monthly = 707.68

        # 根据居住年限调整
        required_years = 40
        if work_years >= required_years:
            adjustment_factor = 1.0
        else:
            adjustment_factor = work_years / required_years

        monthly_oas = full_oas_monthly * adjustment_factor

        return monthly_oas

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
