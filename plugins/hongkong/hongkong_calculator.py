from typing import Dict, Any, List
import math
from datetime import date
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult, EmploymentType

class HongKongPensionCalculator(BasePensionCalculator):
    """香港退休金计算器（强积金）"""

    def __init__(self):
        super().__init__("HK", "香港")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取香港退休年龄"""
        return {
            "male": 65,      # 强积金提取年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取香港缴费比例"""
        return {
            "employee": 0.05,        # 5% 个人缴费
            "civil_servant": 0.05,   # 公务员缴费比例
            "self_employed": 0.05,   # 自雇人士缴费比例
            "farmer": 0.05           # 农民缴费比例
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算香港强积金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算MPF退休金（使用新的准确逻辑）
        mpf_result = self._calculate_mpf_retirement(contribution_history, economic_factors)

        # 计算月退休金
        monthly_pension = mpf_result['MPF_monthly_pension']

        # 计算总缴费
        total_contribution = mpf_result['total_contrib']

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
            original_currency="HKD",
            details={
                'mpf_balance': mpf_result['MPF_balance'],
                'employee_contrib': mpf_result['employee_contrib'],
                'employer_contrib': mpf_result['employer_contrib'],
                'total_contrib': mpf_result['total_contrib'],
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

            # 将人民币月薪转换为港币
            cny_to_hkd_rate = 1.09  # 1 CNY = 1.09 HKD (2025年参考汇率)
            salary_hkd = salary * cny_to_hkd_rate

            # 香港强积金有缴费上下限（2024年约为7,100-30,000港币）
            min_contribution = 7100
            max_contribution = 30000

            # 个人缴费（5%）
            personal_contribution = min(max(salary_hkd * 0.05, min_contribution), max_contribution)

            # 雇主缴费（5%）
            employer_contribution = min(max(salary_hkd * 0.05, min_contribution), max_contribution)

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

    def _calculate_account_balance(self,
                                 contribution_history: List[Dict[str, Any]],
                                 economic_factors: EconomicFactors) -> float:
        """计算强积金账户余额"""
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

    def _calculate_mpf_retirement(self,
                                contribution_history: List[Dict[str, Any]],
                                economic_factors: EconomicFactors) -> Dict[str, float]:
        """计算香港MPF退休金（按照用户提供的准确逻辑）"""
        if not contribution_history:
            return {'MPF_balance': 0, 'MPF_monthly_pension': 0}

        # MPF参数
        return_rate = 0.05      # 投资回报率 5%
        retire_return = 0.03    # 退休期实际收益率 3%
        retire_years = 20       # 退休领取年数（按用户要求）
        min_income = 7100 * 12  # 入息下限 (年化)
        max_income = 30000 * 12 # 入息上限 (年化)
        er_rate = 0.05          # 雇主供款率 5%
        emp_rate = 0.05         # 员工供款率 5%

        # 初始化
        balances = 0.0
        total_emp, total_er = 0.0, 0.0

                # 逐年累积
        for record in contribution_history:
            # 注意：record['salary'] 是月薪，需要转换为年薪
            # record['salary'] 已经是港币，直接使用
            annual_salary = record['salary'] * 12

            # 入息上下限
            income_for_mpf = max(min(annual_salary, max_income), min_income)

            # 缴费
            emp_contrib = income_for_mpf * emp_rate
            er_contrib = income_for_mpf * er_rate
            total = emp_contrib + er_contrib

            # 累积
            balances = balances * (1 + return_rate) + total
            total_emp += emp_contrib
            total_er += er_contrib

        # 退休时账户余额
        final_balance = balances

        # 折算为退休期月养老金（定期年金）
        i = retire_return / 12
        n = retire_years * 12

        if i > 0:
            monthly_payout = final_balance * i / (1 - (1 + i) ** -n)
        else:
            monthly_payout = final_balance / n

        return {
            "MPF_balance": final_balance,
            "MPF_monthly_pension": monthly_payout,
            "employee_contrib": total_emp,
            "employer_contrib": total_er,
            "total_contrib": total_emp + total_er
        }

    def _calculate_monthly_pension(self,
                                 account_balance: float,
                                 retirement_age: int,
                                 economic_factors: EconomicFactors) -> float:
        """计算月退休金"""
        # 香港强积金可以一次性提取或按年金方式提取
        # 这里假设按年金方式提取，使用4%提取率

        withdrawal_rate = 0.04  # 4% 年提取率
        annual_pension = account_balance * withdrawal_rate
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
