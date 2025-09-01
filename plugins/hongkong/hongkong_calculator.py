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

        # 使用MPF账户的投资收益计算
        total_return = mpf_result['total_return']
        roi = mpf_result['roi_pct']

        # 计算总收益（假设活到85岁）
        life_expectancy = 85
        retirement_years = life_expectancy - retirement_age
        total_benefit = monthly_pension * 12 * retirement_years

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
                'total_return': total_return,
                'roi_pct': roi,
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

            # 香港强积金参数
            min_income = 7100.0  # HK$/月
            max_income = 30000.0  # HK$/月
            emp_rate = 0.05  # 雇员 5%
            er_rate = 0.05   # 雇主 5%
            
            # 工资上下限约束
            income = max(min_income, min(salary_hkd, max_income))
            
            # 个人缴费（月薪低于下限时不缴费）
            emp_contrib = income * emp_rate if salary_hkd >= min_income else 0.0
            
            # 雇主缴费（总是缴费）
            er_contrib = income * er_rate
            
            # 总缴费
            total_contribution = emp_contrib + er_contrib

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary': salary_hkd,  # 保存港币月薪
                'personal_contribution': emp_contrib * 12,
                'employer_contribution': er_contrib * 12,
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
            return {'MPF_balance': 0, 'MPF_monthly_pension': 0, 'employee_contrib': 0, 'employer_contrib': 0, 'total_contrib': 0}

        # MPF参数
        annual_return = 0.04      # 投资年化收益率 4%
        wage_growth = 0.02        # 工资年增长 2%
        retire_return = 0.03      # 退休期折现率 3%
        retire_years = 20         # 退休后领取年限
        min_income = 7100.0       # HK$/月
        max_income = 30000.0      # HK$/月
        emp_rate = 0.05           # 雇员 5%
        er_rate = 0.05            # 雇主 5%
        start_age = 30            # 开始工作年龄
        retire_age = 65           # 退休年龄

        # 初始化
        balance = 0.0
        total_contrib = 0.0
        
        # 获取初始月薪
        initial_salary = contribution_history[0]['salary']
        current_salary = initial_salary
        
        # 计算工作年数
        years = retire_age - start_age     # 30→65 应为 35
        months = years * 12
        for year_idx in range(years):
            for month in range(12):
                # 员工缴费：工资 < min_income → 0；否则按 min(工资, max_income)
                emp_base = min(current_salary, max_income) if current_salary >= min_income else 0.0
                
                # 雇主缴费：始终按 min(工资, max_income)（不抬高到 min_income）
                er_base = min(current_salary, max_income)
                
                emp = emp_base * emp_rate
                er = er_base * er_rate
                contrib = emp + er
                
                # 账户余额按月复利增长
                balance = balance * (1 + annual_return/12.0) + contrib
                total_contrib += contrib
            
            # 工资年增长在年末做
            current_salary *= (1 + wage_growth)
        
        final_balance = balance
        
        # 计算累计个人和雇主缴费（用于统计）
        total_emp_contrib = 0.0
        total_er_contrib = 0.0
        salary = initial_salary
        
        for year_idx in range(years):
            for month in range(12):
                # 员工缴费基数
                emp_base = min(salary, max_income) if salary >= min_income else 0.0
                # 雇主缴费基数
                er_base = min(salary, max_income)
                
                emp = emp_base * emp_rate
                er = er_base * er_rate
                total_emp_contrib += emp
                total_er_contrib += er
            # 工资年增长在年末做
            salary *= (1 + wage_growth)
        
        # 计算收益
        total_return = final_balance - total_contrib
        roi_pct = final_balance / total_contrib - 1.0 if total_contrib > 0 else 0.0
        
        # 年金换算月养老金
        i = retire_return / 12.0
        n = retire_years * 12
        monthly_pension = (final_balance * i / (1 - (1 + i) ** -n)) if i > 0 else final_balance / n
        
        return {
            "MPF_balance": final_balance,
            "MPF_monthly_pension": monthly_pension,
            "employee_contrib": total_emp_contrib,
            "employer_contrib": total_er_contrib,
            "total_contrib": total_contrib,
            "total_return": total_return,
            "roi_pct": roi_pct
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
