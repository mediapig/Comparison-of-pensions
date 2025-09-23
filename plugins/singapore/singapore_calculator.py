from typing import Dict, Any, List
from core.base_calculator import BasePensionCalculator
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult

class SingaporePensionCalculator(BasePensionCalculator):
    """新加坡中央公积金计算器 - 修正版"""

    def __init__(self):
        super().__init__("SG", "新加坡")

    def _get_retirement_ages(self) -> Dict[str, int]:
        """获取新加坡退休年龄"""
        return {
            "male": 65,
            "female": 65
        }

    def _get_contribution_rates(self) -> Dict[str, float]:
        """获取新加坡缴费比例"""
        return {
            "employee": 0.20,        # 20% 个人缴费
            "employer": 0.17,        # 17% 雇主缴费
            "total": 0.37            # 总缴费比例 37%
        }

    def calculate_pension(self,
                         person: Person,
                         salary_profile: SalaryProfile,
                         economic_factors: EconomicFactors) -> PensionResult:
        """计算新加坡中央公积金 - 使用正确的CPF模型"""
        
        # 获取月薪（系统输入的是月薪）
        monthly_salary = salary_profile.monthly_salary
        
        # 计算年薪
        annual_salary = monthly_salary * 12
        
        # 使用简化的CPF模型
        result = self._cpf_model(annual_salary, 30, 35)  # 30岁开始，工作35年到65岁
        
        # 计算总收益（假设活到90岁）
        life_expectancy = 90
        retirement_age = 65
        retirement_years = life_expectancy - retirement_age
        total_benefit = result['monthly_payout'] * 12 * retirement_years
        
        # 计算ROI
        total_cpf_value = result['total_payout'] + result['OA_remaining'] + result['MA_remaining']
        roi = (total_cpf_value / result['cpf_contrib'] - 1) * 100
        
        # 计算回本年龄
        break_even_age = self._calculate_break_even_age(
            result['cpf_contrib'], result['monthly_payout'], retirement_age
        )

        return PensionResult(
            monthly_pension=result['monthly_payout'],
            total_contribution=result['cpf_contrib'],
            total_benefit=total_benefit,
            break_even_age=break_even_age,
            roi=roi,
            original_currency="SGD",
            details={
                'ra_at_65': result['RA_at_65'],
                'oa_remaining': result['OA_remaining'],
                'ma_remaining': result['MA_remaining'],
                'total_cpf_value': total_cpf_value,
                'annual_salary': annual_salary,
                'monthly_salary': monthly_salary
            }
        )

    def _cpf_model(self, income, start_age, work_years):
        """简化的CPF模型 - 基于我们之前验证的正确逻辑"""
        # === 工作期 ===
        cpf_contrib = 0
        OA = 0
        SA = 0
        MA = 0
        
        for age in range(start_age, start_age + work_years):
            base = min(income, 102000)   # 年薪上限
            contrib = base * 0.37        # 总缴费
            cpf_contrib += contrib
            # 按比例分配 OA, SA, MA
            OA += base * 0.23
            SA += base * 0.06
            MA += base * 0.08
        
        # === 55岁时，转入RA ===
        RA = 0
        if start_age + work_years >= 55:
            # 假设SA全部转入RA，OA部分转入RA
            RA = SA + OA * 0.5  # 假设OA的一半转入RA
            OA_remaining = OA * 0.5  # OA剩余部分
            
            # 55–65岁利息累积
            for i in range(10):
                RA *= 1.04   # 年息4%
                OA_remaining *= 1.025  # OA年息2.5%
                MA *= 1.04  # MA年息4%
        
        # === 65岁开始领取 ===
        payout_per_month = RA / 180  # 假设15年领取期
        total_payout = payout_per_month * 12 * 25  # 25年退休期
        
        return {
            'RA_at_65': RA,
            'monthly_payout': payout_per_month,
            'total_payout': total_payout,
            'cpf_contrib': cpf_contrib,
            'OA_remaining': OA_remaining,
            'MA_remaining': MA
        }

    def calculate_contribution_history(self,
                                    person: Person,
                                    salary_profile: SalaryProfile,
                                    economic_factors: EconomicFactors) -> List[Dict[str, Any]]:
        """计算缴费历史 - 简化版本"""
        monthly_salary = salary_profile.monthly_salary
        annual_salary = monthly_salary * 12
        
        # 使用简化的CPF模型
        result = self._cpf_model(annual_salary, 30, 35)
        
        # 返回简化的历史记录
        history = []
        for year in range(35):  # 30-64岁，35年
            age = 30 + year
            base = min(annual_salary, 102000)
            
            # 计算当年缴费
            total_contribution = base * 0.37
            personal_contribution = base * 0.20
            employer_contribution = base * 0.17
            
            history.append({
                'age': age,
                'year': person.start_work_date.year + year,
                'salary_sgd': annual_salary,
                'annual_salary': base,
                'total_contribution': total_contribution,
                'personal_contribution': personal_contribution,
                'employer_contribution': employer_contribution
            })
        
        return history

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

    def calculate_tax(self, annual_income: float) -> Dict[str, Any]:
        """计算新加坡个人所得税 - 使用累进税率"""
        # 新加坡个人所得税累进税率
        if annual_income <= 20000:
            tax = 0
        elif annual_income <= 30000:
            tax = (annual_income - 20000) * 0.02
        elif annual_income <= 40000:
            tax = 200 + (annual_income - 30000) * 0.035
        elif annual_income <= 80000:
            tax = 550 + (annual_income - 40000) * 0.07
        elif annual_income <= 120000:
            tax = 3350 + (annual_income - 80000) * 0.115
        elif annual_income <= 160000:
            tax = 7950 + (annual_income - 120000) * 0.15
        elif annual_income <= 200000:
            tax = 13950 + (annual_income - 160000) * 0.18
        elif annual_income <= 240000:
            tax = 21150 + (annual_income - 200000) * 0.19
        elif annual_income <= 280000:
            tax = 28750 + (annual_income - 240000) * 0.195
        elif annual_income <= 320000:
            tax = 36550 + (annual_income - 280000) * 0.20
        else:
            tax = 44550 + (annual_income - 320000) * 0.22

        effective_rate = (tax / annual_income * 100) if annual_income > 0 else 0
        net_income = annual_income - tax

        return {
            'total_tax': tax,
            'effective_rate': effective_rate,
            'net_income': net_income
        }

    def calculate_social_security(self, monthly_salary: float, work_years: int) -> Dict[str, Any]:
        """计算新加坡CPF社保缴费"""
        annual_salary = monthly_salary * 12
        base = min(annual_salary, 102000)  # 年薪上限
        
        # 计算月缴费
        monthly_employee = base * 0.20 / 12
        monthly_employer = base * 0.17 / 12
        
        # 计算终身总缴费
        total_lifetime = (monthly_employee + monthly_employer) * 12 * work_years
        
        return {
            'monthly_employee': monthly_employee,
            'monthly_employer': monthly_employer,
            'total_lifetime': total_lifetime
        }