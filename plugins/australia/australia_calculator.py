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
            "employee": 0.00,        # 0% 员工自愿缴费（默认）
            "civil_servant": 0.12,   # 12% 公务员缴费比例
            "self_employed": 0.12,   # 12% 自雇人士缴费比例
            "farmer": 0.12,          # 12% 农民缴费比例
            "employer": 0.12,        # 12% 雇主强制缴费比例 (2025年起)
            "total": 0.12            # 12% 总缴费比例（主要是雇主缴费）
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算澳大利亚超级年金"""
        # 固定从30岁开始工作，一直缴纳到退休
        start_work_age = 30
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - start_work_age

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

        # 计算总缴费（按你补丁的逻辑）
        total_contribution = sum(record['total_contribution'] for record in contribution_history)
        total_employer = sum(record['employer_contribution'] for record in contribution_history)
        total_employee = sum(record['personal_contribution'] for record in contribution_history)

        # 计算总收益（按预期寿命计算领取期）
        life_expectancy = 85  # 澳大利亚平均预期寿命
        retire_years = life_expectancy - retirement_age
        total_benefit = monthly_pension * 12 * retire_years

        # 计算ROI（按照你提供的公式）
        final_balance = super_balance
        total_contrib = total_contribution
        total_return = final_balance - total_contrib
        roi_pct = final_balance / total_contrib - 1.0 if total_contrib > 0 else 0

        # 计算替代率（按照你提供的公式）
        initial_monthly_salary = salary_profile.base_salary
        initial_annual_salary_aud = initial_monthly_salary * 0.21 * 12  # 初始年薪
        growth = salary_profile.annual_growth_rate  # 使用实际的年增长率
        years = work_years
        last_year_salary = initial_annual_salary_aud * ((1 + growth) ** (years - 1)) if growth > 0 else initial_annual_salary_aud  # 最后一年年薪
        replacement = (monthly_pension * 12.0) / last_year_salary if last_year_salary > 0 else 0

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_contribution, monthly_pension, retirement_age
        )

        return PensionResult(
            monthly_pension=monthly_pension,
            total_contribution=total_contribution,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi_pct,
            original_currency="AUD",
            details={
                'super_balance': super_balance,
                'final_balance': final_balance,
                'total_contrib': total_contrib,
                'work_years': work_years,
                'retirement_age': retirement_age,
                'replacement_rate': replacement,
                'total_employer': total_employer,
                'total_employee': total_employee,
                'total_return': total_return,
                'last_year_salary': last_year_salary
            }
        )

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史"""
        # 固定从30岁开始工作，一直缴纳到退休
        start_work_age = 30
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - start_work_age

        history = []
        
        # 将人民币月薪转换为澳币，然后应用年增长率
        cny_to_aud_rate = 0.21  # 1 CNY = 0.21 AUD (2025年参考汇率)
        initial_monthly_salary = salary_profile.base_salary
        initial_annual_salary_aud = initial_monthly_salary * cny_to_aud_rate * 12  # 初始年薪

        # 澳大利亚超级年金参数（2025年）
        er_rate = 0.12      # 雇主 SG 供款率 (2025 起 12%)
        emp_rate = 0.00     # 员工自愿税前供款率
        concessional_cap = 30000  # 税前供款年度上限 (2025)
        growth = salary_profile.annual_growth_rate  # 使用实际的年增长率

        for year in range(work_years):
            age = start_work_age + year

            # 逐年增长：S_t = salary_aud * ((1 + growth) ** t)
            S_t = initial_annual_salary_aud * ((1 + growth) ** year)

            # 雇主强制缴费
            contrib_er = S_t * er_rate
            contrib_emp = S_t * emp_rate
            gross = min(contrib_er + contrib_emp, concessional_cap)

            # 细分雇主/员工（cap 后优先保留雇主，如超过cap则截断在cap，员工记为剩余）
            if gross <= contrib_er:
                er_eff, emp_eff = gross, 0.0
            else:
                er_eff, emp_eff = contrib_er, gross - contrib_er

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': S_t,
                'annual_salary': S_t,
                'employer_contribution': er_eff,
                'personal_contribution': emp_eff,
                'total_contribution': gross
            })

        return history

    def _calculate_super_balance(self,
                               contribution_history: List[Dict[str, Any]],
                               economic_factors: EconomicFactors) -> float:
        """计算超级年金账户余额（完全按照参考函数逻辑）"""
        if not contribution_history:
            return 0

        # 完全按照参考函数的逻辑
        FV = 0.0
        return_rate = 0.05  # 投资年化回报 5%

        for record in contribution_history:
            # 每年的缴费
            gross = record['total_contribution']

            # 期末记息：FV = FV * (1 + return_rate) + gross
            FV = FV * (1 + return_rate) + gross

        return FV

    def _calculate_super_pension(self,
                               super_balance: float,
                               retirement_age: int,
                               economic_factors: EconomicFactors) -> float:
        """计算超级年金养老金（使用准确的澳大利亚模型）"""
        # 使用你提供的澳大利亚超级年金养老金计算逻辑
        # 年金折算（必须用同一 FV/参数）

        FV = super_balance
        retire_return = 0.03  # 退休期实际收益率 3%
        life_expectancy = 85  # 澳大利亚平均预期寿命
        retire_years = life_expectancy - retirement_age  # 退休领取年数

        # 年金折算公式: monthly_pmt = FV * i / (1 - (1 + i) ** (-n))
        i = retire_return / 12.0  # 月利率
        n = retire_years * 12     # 月数

        if i > 0 and n > 0:
            monthly_pmt = FV * i / (1 - (1 + i) ** (-n))
        else:
            monthly_pmt = FV / n

        return monthly_pmt

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
