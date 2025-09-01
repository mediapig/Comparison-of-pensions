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
            "male": 63,    # 更新为63岁
            "female": 63   # 统一63岁
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
        """计算中国退休金 - 使用精确算法"""
        # 使用精确的中国养老金算法
        init_salary_month = salary_profile.base_salary
        init_avg_month = 10500  # 初始社平月工资（南京2024参考）
        start_age = 30  # 固定30岁开始工作
        retire_age = self.get_retirement_age(person)
        salary_growth = salary_profile.annual_growth_rate
        avg_growth = 0.02
        emp_rate = 0.08
        base_lower = 0.60
        base_upper = 3.00

        # 调用精确算法（63岁退休）
        result = self._calc_china_pension_pure(
            init_salary_month, init_avg_month, start_age, 63,  # 固定63岁退休
            salary_growth, avg_growth, emp_rate, base_lower, base_upper
        )

        # 不再使用22年PMT计算总收益，仅展示个人账户相关数据
        # 总收益基于个人账户口径计算
        total_benefit = result['final_balance']  # 个人账户最终余额作为总收益展示

        # 按照标准公式计算ROI和替代率（使用优化后的数据）
        final_balance = result['final_balance']  # = 员工8%累计（pa_rate=0）
        total_employee_contrib = result['personal_account_employee_sum']  # 同上一行的构成
        total_return = result['total_return']  # = 0 (pa_rate=0)
        roi_pct = final_balance / total_employee_contrib - 1.0 if total_employee_contrib > 0 else 0
        
        # 替代率计算
        last_year_salary = result['last_salary'] * 12  # 年工资
        replacement = (result['total_pension'] * 12.0) / last_year_salary if last_year_salary > 0 else 0

        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            total_employee_contrib, result['total_pension'], 63  # 固定63岁退休
        )

        return PensionResult(
            monthly_pension=result['total_pension'],
            total_contribution=total_employee_contrib,
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi_pct,
            original_currency="CNY",
            details={
                'basic_pension': result['basic_pension'],
                'account_pension': result['account_pension'],
                'personal_account_balance': result['personal_account_balance'],
                'total_employee_contrib': result['total_employee_contrib'],
                'indexed_salary': result['indexed_salary'],
                'last_avg_salary': result['last_avg_salary'],
                'last_salary': result['last_salary'],
                'work_years': result['years'],
                'avg_index': result['avg_index'],
                'jifa_months': result['jifa_months'],
                'replacement_rate': replacement,
                'final_balance': final_balance,
                'total_contrib': total_employee_contrib,
                'total_return': total_return
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

    def _calc_china_pension_pure(self,
                                init_salary_month: float,   # 初始月工资
                                init_avg_month: float = 10500,  # 初始社平月工资（南京2024参考）
                                start_age: int = 30,
                                retire_age: int = 63,
                                salary_growth: float = 0.02,
                                avg_growth: float = 0.02,
                                emp_rate: float = 0.08,
                                base_lower: float = 0.60,   # 缴费基数下限 = 社平*60%
                                base_upper: float = 3.00,   # 缴费基数上限 = 社平*300%
                                pa_rate: float = 0.0        # 个人账户收益率，默认0%
                                ):
        """精确的中国养老金计算算法（按照优化版本）"""
        # 1) 年限与退休年龄
        years = retire_age - start_age  # = 33 (63-30)
        
        # 2) 计发月数：63岁
        JIFA_MONTHS = 170  # 60岁=139，63岁=170
        
        # 初始化
        salary = init_salary_month
        avg = init_avg_month
        personal_account = 0.0
        ratios = []
        total_employee_contrib = 0.0

        # 3) 每年工资 & 社平增长 2%，计算缴费基数
        for year in range(years):
            # 计算缴费基数（社平*0.6~3.0）
            lower = base_lower * avg
            upper = base_upper * avg
            base = max(lower, min(salary, upper))  # clamp(salary_t, 0.60*avg_t, 3.00*avg_t)

            # 4) 个人账户只累"个人 8%"
            employee_contrib_t = base * emp_rate * 12
            personal_account = personal_account * (1 + pa_rate) + employee_contrib_t
            total_employee_contrib += employee_contrib_t

            # 缴费指数
            ratios.append(base / avg)

            # 增长
            salary *= (1 + salary_growth)
            avg *= (1 + avg_growth)

        # 退休当年社平月工资
        last_avg_month = init_avg_month * ((1 + avg_growth) ** years)

        # 5) 基础养老金（月）（指数化平均口径）
        avg_index = sum(ratios) / len(ratios) if ratios else 0
        indexed_month = avg_index * last_avg_month
        basic_monthly = ((indexed_month + last_avg_month) / 2) * (years * 0.01)

        # 6) 个人账户养老金（月）
        account_monthly = personal_account / JIFA_MONTHS  # 63岁 = 170个月

        total_monthly = basic_monthly + account_monthly

        # 个人账户口径（养老部分）
        final_balance = personal_account                        # = 员工8%累计（pa_rate=0）
        personal_account_employee_sum = total_employee_contrib  # 同上一行的构成
        total_return = final_balance - personal_account_employee_sum  # = 0 (pa_rate=0)

        return {
            "basic_pension": basic_monthly,
            "account_pension": account_monthly,
            "total_pension": total_monthly,
            "personal_account_balance": personal_account,
            "total_employee_contrib": total_employee_contrib,
            "personal_account_employee_sum": personal_account_employee_sum,
            "final_balance": final_balance,
            "total_return": total_return,
            "indexed_salary": indexed_month,
            "last_avg_salary": last_avg_month,
            "last_salary": salary,
            "years": years,
            "avg_index": avg_index,
            "jifa_months": JIFA_MONTHS
        }
