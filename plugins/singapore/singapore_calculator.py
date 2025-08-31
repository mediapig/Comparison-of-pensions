from typing import Dict, Any, List
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class SingaporePensionCalculator(BasePensionCalculator):
    """新加坡中央公积金计算器"""

    def __init__(self):
        super().__init__("SG", "新加坡")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取新加坡退休年龄"""
        return {
            "male": 65,      # CPF提取年龄
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取新加坡缴费比例"""
        return {
            "employee": 0.20,        # 20% 个人缴费
            "civil_servant": 0.20,   # 公务员缴费比例
            "self_employed": 0.20,   # 自雇人士缴费比例
            "farmer": 0.20,          # 农民缴费比例
            "employer": 0.17,        # 雇主缴费比例 17%
            "total": 0.37            # 总缴费比例 37%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡中央公积金"""
        retirement_age = self.get_retirement_age(person)
        work_years = retirement_age - person.age

        if work_years <= 0:
            work_years = person.work_years

        # 计算缴费历史
        contribution_history = self.calculate_contribution_history(
            person, salary_profile, economic_factors
        )

        # 计算CPF账户余额
        cpf_result = self._calculate_cpf_retirement(
            contribution_history, economic_factors
        )

        # 月退休金
        monthly_pension = cpf_result['CPF_LIFE_monthly']

        # 计算总缴费
        total_contribution = sum(record['total_contribution'] for record in contribution_history)

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
            original_currency="SGD",
            details={
                'oa_balance': cpf_result['OA'],
                'sa_balance': cpf_result['SA'],
                'ma_balance': cpf_result['MA'],
                'ra_balance': cpf_result['RA'],
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

            # 新加坡CPF参数（2025年）
            # 注意：salary是人民币，需要转换为新币
            # 假设汇率：1 CNY = 0.19 SGD (2025年参考汇率)
            cny_to_sgd = 0.19
            salary_sgd = salary * cny_to_sgd

                        # 计算缴费基数 - 使用实际工资，但不超过上限
            ow_ceiling = 7400        # 月度OW顶 (SGD)
            aw_ceiling = 102000      # 年度AW顶 (SGD)
            annual_limit = 37740     # 年度总缴费限额 (SGD)

            # 缴费基数 = min(实际工资, 月度上限)
            ow_base = min(salary_sgd, ow_ceiling)
            annual_salary = min(ow_base * 12, aw_ceiling)

            # 计算总缴费 - 37% (员工20% + 雇主17%)
            total_contribution = annual_salary * 0.37
            total_contribution = min(total_contribution, annual_limit)

            # 分配到三个账户（55岁以下比例）
            oa_contribution = total_contribution * 0.62  # 62% 到OA
            sa_contribution = total_contribution * 0.16  # 16% 到SA
            ma_contribution = total_contribution * 0.22  # 22% 到MA

            # 个人缴费（20%）
            personal_contribution = annual_salary * 0.20

            # 雇主缴费（17%）
            employer_contribution = annual_salary * 0.17

            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary_cny': salary,
                'salary_sgd': salary_sgd,
                'annual_salary': annual_salary,
                'ow_base': ow_base,
                'total_contribution': total_contribution,
                'oa_contribution': oa_contribution,
                'sa_contribution': sa_contribution,
                'ma_contribution': ma_contribution,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution
            })

        return history

    def _calculate_cpf_retirement(self,
                                contribution_history: List[Dict[str, Any]],
                                economic_factors: EconomicFactors) -> Dict[str, float]:
        """计算CPF退休金（按照用户提供的正确算法）"""
        if not contribution_history:
            return {'OA': 0, 'SA': 0, 'MA': 0, 'RA': 0, 'CPF_LIFE_monthly': 0}

        # CPF参数（2025年）
        return_oa = 0.025      # OA 利率 2.5%
        return_sa = 0.04       # SA 利率 4%
        return_ma = 0.04       # MA 利率 4%
        brs = 137000           # Basic Retirement Sum (2025)
        frs = 205800           # Full Retirement Sum (2025)
        ers = 308700           # Enhanced Retirement Sum (2025)
        retire_return = 0.03   # 退休后实际回报率
        retire_years = 20      # 退休领取年数（按用户要求）

        # 初始化账户余额
        oa, sa, ma = 0.0, 0.0, 0.0

        # ===== 累积 OA / SA / MA =====
        for record in contribution_history:
            # 获取当年缴费
            c_oa = record['oa_contribution']
            c_sa = record['sa_contribution']
            c_ma = record['ma_contribution']

            # 复利累积：先计算利息，再加上新缴费
            oa = oa * (1 + return_oa) + c_oa
            sa = sa * (1 + return_sa) + c_sa
            ma = ma * (1 + return_ma) + c_ma

        # ===== 55岁时转入 RA =====
        ra_balance = oa + sa
        if ra_balance >= ers:
            ra = ers
            tier = "ERS"
        elif ra_balance >= frs:
            ra = frs
            tier = "FRS"
        elif ra_balance >= brs:
            ra = brs
            tier = "BRS"
        else:
            ra = ra_balance
            tier = "Below BRS"

        # ===== CPF LIFE 终身年金折算（不是定期年金）=====
        # 使用终身年金公式：PMT = PV * r，其中r是月利率
        monthly_rate = retire_return / 12
        monthly_payout = ra * monthly_rate

        return {
            "OA": oa,
            "SA": sa,
            "MA": ma,
            "RA": ra,
            "CPF_LIFE_monthly": monthly_payout,
            "tier": tier
        }

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
