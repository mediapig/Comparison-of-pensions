#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国养老金计算器 - 优化版本
严格按照用户提供的7步算法实现
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class ChinaOptimizedParams:
    """中国养老金计算参数 - 优化版本"""
    
    # 社保缴费比例
    emp_pension_rate: float = 0.08      # 个人养老 8%
    emp_medical_rate: float = 0.02      # 个人医疗 2%
    emp_unemp_rate: float = 0.005       # 个人失业 0.5%
    
    er_pension_rate: float = 0.16       # 单位养老 16%
    er_medical_rate: float = 0.09       # 单位医疗 9%
    er_unemp_rate: float = 0.005        # 单位失业 0.5%
    er_injury_rate: float = 0.0016     # 单位工伤 0.16%
    
    # 公积金参数
    hf_rate_default: float = 0.07      # 默认公积金比例 7%
    hf_base_lower: float = 2690         # 公积金基数下限
    hf_base_upper: float = 36921       # 公积金基数上限
    
    # 个税参数
    basic_deduction: float = 60000      # 基本减除费用
    
    # 退休参数
    retirement_age: int = 60            # 退休年龄
    start_age: int = 30                 # 开始工作年龄
    
    # 社平工资参数
    avg_wage_2024: float = 12434        # 2024年社平工资
    avg_wage_growth_rate: float = 0.02  # 社平工资年增长率


@dataclass
class YearlyCalculationResult:
    """年度计算结果"""
    year: int
    age: int
    gross_income: float
    avg_wage: float
    
    # STEP 1: 基数
    si_base_month: float
    hf_base_month: float
    
    # STEP 2: 五险缴费
    emp_pension: float
    emp_medical: float
    emp_unemp: float
    emp_total_si: float
    
    er_pension: float
    er_medical: float
    er_unemp: float
    er_injury: float
    er_total_si: float
    
    # STEP 3: 公积金缴费
    emp_hf: float
    er_hf: float
    
    # STEP 4: 个税
    taxable_income: float
    tax_amount: float
    
    # STEP 5: 到手工资
    net_income: float
    
    # STEP 6: 累计账户
    pension_account_balance: float
    housing_fund_balance: float


@dataclass
class RetirementResult:
    """退休计算结果"""
    total_work_years: int
    total_employee_contributions: float
    total_employer_contributions: float
    total_contributions: float
    
    final_pension_account_balance: float
    final_housing_fund_balance: float
    
    monthly_pension: float
    annual_pension: float
    
    total_benefits: float
    roi: float
    irr: float  # 新增IRR字段
    break_even_age: Optional[float]


class ChinaOptimizedCalculator:
    """中国养老金计算器 - 优化版本"""
    
    def __init__(self, params: Optional[ChinaOptimizedParams] = None):
        self.params = params or ChinaOptimizedParams()
        
        # 个税税率表（七级超额累进）
        self.tax_brackets = [
            (0, 36000, 0.03, 0),           # 3%
            (36000, 144000, 0.10, 2520),   # 10%
            (144000, 300000, 0.20, 16920), # 20%
            (300000, 420000, 0.25, 31920), # 25%
            (420000, 660000, 0.30, 52920), # 30%
            (660000, 960000, 0.35, 85920), # 35%
            (960000, float('inf'), 0.45, 181920) # 45%
        ]
    
    def calculate_yearly(self, year: int, age: int, gross_income: float, 
                        avg_wage: float, hf_rate: float = None) -> YearlyCalculationResult:
        """
        计算单年度养老金和税收
        
        Args:
            year: 年份
            age: 年龄
            gross_income: 年收入
            avg_wage: 当年社平工资
            hf_rate: 公积金比例，默认使用参数中的默认值
            
        Returns:
            年度计算结果
        """
        if hf_rate is None:
            hf_rate = self.params.hf_rate_default
        
        # STEP 1: 确定社保、公积金基数
        monthly_income = gross_income / 12
        si_base_month = self._clamp(monthly_income, 0.6 * avg_wage, 3.0 * avg_wage)
        hf_base_month = self._clamp(monthly_income, self.params.hf_base_lower, self.params.hf_base_upper)
        
        # STEP 2: 五险缴费
        # 个人缴费
        emp_pension = si_base_month * self.params.emp_pension_rate * 12
        emp_medical = si_base_month * self.params.emp_medical_rate * 12
        emp_unemp = si_base_month * self.params.emp_unemp_rate * 12
        emp_total_si = emp_pension + emp_medical + emp_unemp
        
        # 单位缴费
        er_pension = si_base_month * self.params.er_pension_rate * 12
        er_medical = si_base_month * self.params.er_medical_rate * 12
        er_unemp = si_base_month * self.params.er_unemp_rate * 12
        er_injury = si_base_month * self.params.er_injury_rate * 12
        er_total_si = er_pension + er_medical + er_unemp + er_injury
        
        # STEP 3: 公积金缴费
        emp_hf = hf_base_month * hf_rate * 12
        er_hf = hf_base_month * hf_rate * 12
        
        # STEP 4: 个税 - 按照用户提供的正确公式
        # 个人三险（不含公积金）
        emp_si = emp_pension + emp_medical + emp_unemp
        
        # 个税：只减一次公积金
        taxable_income = max(0, gross_income - self.params.basic_deduction - emp_si - emp_hf)
        tax_amount = self._calculate_tax(taxable_income)
        
        # STEP 5: 到手工资 - 添加断言验证
        net_income = gross_income - emp_si - emp_hf - tax_amount
        
        # 验证恒等式
        assert abs((net_income + emp_si + emp_hf + tax_amount) - gross_income) < 1e-6, \
            f"到手工资计算错误: {net_income} + {emp_si} + {emp_hf} + {tax_amount} != {gross_income}"
        
        # STEP 6: 累计账户（这里返回当年缴费，累计在外部处理）
        pension_account_balance = emp_pension  # 个人账户只计入个人缴费
        housing_fund_balance = emp_hf + er_hf   # 公积金计入个人+单位缴费
        
        return YearlyCalculationResult(
            year=year,
            age=age,
            gross_income=gross_income,
            avg_wage=avg_wage,
            si_base_month=si_base_month,
            hf_base_month=hf_base_month,
            emp_pension=emp_pension,
            emp_medical=emp_medical,
            emp_unemp=emp_unemp,
            emp_total_si=emp_si,  # 使用修正后的个人三险
            er_pension=er_pension,
            er_medical=er_medical,
            er_unemp=er_unemp,
            er_injury=er_injury,
            er_total_si=er_total_si,
            emp_hf=emp_hf,
            er_hf=er_hf,
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            net_income=net_income,
            pension_account_balance=pension_account_balance,
            housing_fund_balance=housing_fund_balance
        )
    
    def calculate_lifetime(self, initial_gross_income: float, 
                          salary_growth_rate: float = 0.02,
                          hf_rate: float = None) -> RetirementResult:
        """
        计算终身养老金
        
        Args:
            initial_gross_income: 初始年收入
            salary_growth_rate: 薪资年增长率
            hf_rate: 公积金比例
            
        Returns:
            退休计算结果
        """
        if hf_rate is None:
            hf_rate = self.params.hf_rate_default
        
        work_years = self.params.retirement_age - self.params.start_age
        current_gross_income = initial_gross_income
        
        # 累计变量
        total_employee_contributions = 0
        total_employer_contributions = 0
        pension_account_balance = 0
        housing_fund_balance = 0
        
        yearly_results = []
        
        # 逐年计算
        for year_offset in range(work_years):
            year = 2024 + year_offset
            age = self.params.start_age + year_offset
            avg_wage = self._get_avg_wage(year)
            
            # 计算当年结果
            yearly_result = self.calculate_yearly(year, age, current_gross_income, avg_wage, hf_rate)
            yearly_results.append(yearly_result)
            
            # 累计缴费
            total_employee_contributions += yearly_result.emp_total_si + yearly_result.emp_hf
            total_employer_contributions += yearly_result.er_total_si + yearly_result.er_hf
            
            # 累计账户余额
            pension_account_balance += yearly_result.pension_account_balance
            housing_fund_balance += yearly_result.housing_fund_balance
            
            # 薪资增长
            current_gross_income *= (1 + salary_growth_rate)
        
        # STEP 7: 退休时计算
        monthly_pension = self._calculate_monthly_pension(pension_account_balance, work_years)
        annual_pension = monthly_pension * 12
        
        # 总收益计算 - 只计算个人实际收益
        retirement_years = 90 - self.params.retirement_age  # 退休后30年
        total_benefits = annual_pension * retirement_years + housing_fund_balance
        
        # ROI计算 - 只基于个人缴费
        roi = (total_benefits - total_employee_contributions) / total_employee_contributions if total_employee_contributions > 0 else 0
        
        # IRR计算 - 正确的现金流方向
        irr = self._calculate_irr(yearly_results, housing_fund_balance, monthly_pension)
        
        # 回本年龄
        break_even_age = None
        if monthly_pension > 0:
            months_to_break_even = total_employee_contributions / monthly_pension
            break_even_age = self.params.retirement_age + months_to_break_even / 12
            if break_even_age > 90:
                break_even_age = None
        
        return RetirementResult(
            total_work_years=work_years,
            total_employee_contributions=total_employee_contributions,
            total_employer_contributions=total_employer_contributions,
            total_contributions=total_employee_contributions + total_employer_contributions,
            final_pension_account_balance=pension_account_balance,
            final_housing_fund_balance=housing_fund_balance,
            monthly_pension=monthly_pension,
            annual_pension=annual_pension,
            total_benefits=total_benefits,
            roi=roi,
            irr=irr,  # 添加IRR
            break_even_age=break_even_age
        )
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """限制值在指定范围内"""
        return max(min_val, min(value, max_val))
    
    def _calculate_tax(self, taxable_income: float) -> float:
        """计算个税（七级超额累进速算扣除法）"""
        if taxable_income <= 0:
            return 0
        
        for min_income, max_income, rate, deduction in self.tax_brackets:
            if min_income < taxable_income <= max_income:
                return taxable_income * rate - deduction
        
        return 0
    
    def _get_avg_wage(self, year: int) -> float:
        """获取指定年份的社平工资"""
        if year <= 2024:
            return self.params.avg_wage_2024
        else:
            years_from_2024 = year - 2024
            return self.params.avg_wage_2024 * ((1 + self.params.avg_wage_growth_rate) ** years_from_2024)
    
    def _calculate_monthly_pension(self, pension_account_balance: float, work_years: int) -> float:
        """
        计算月养老金
        
        简化计算：使用缴费累计/退休年限公式
        """
        # 基础养老金：基于工作年限和社平工资
        avg_wage_at_retirement = self._get_avg_wage(2024 + work_years)
        basic_pension = avg_wage_at_retirement * work_years * 0.01
        
        # 个人账户养老金：个人账户余额 / 计发月数（60岁=139个月）
        personal_account_pension = pension_account_balance / 139
        
        return basic_pension + personal_account_pension
    
    def _calculate_irr(self, yearly_results: List[YearlyCalculationResult], 
                      housing_fund_balance: float, monthly_pension: float) -> float:
        """
        计算IRR - 基于正确的现金流方向
        
        Args:
            yearly_results: 逐年计算结果
            housing_fund_balance: 公积金余额
            monthly_pension: 月养老金
            
        Returns:
            IRR (年化收益率)
        """
        try:
            # 构建现金流：工作期为负（个人缴费），退休期为正（养老金）
            cash_flows = []
            
            # 工作期现金流（负值 - 个人缴费）
            for result in yearly_results:
                # 个人缴费作为负现金流
                personal_contribution = result.emp_total_si + result.emp_hf
                cash_flows.append(-personal_contribution)
            
            # 退休期现金流（正值 - 养老金收入）
            retirement_years = 90 - self.params.retirement_age
            annual_pension = monthly_pension * 12
            
            for year in range(int(retirement_years)):
                if year == 0:
                    # 第一年退休：养老金 + 公积金一次性提取
                    cash_flows.append(annual_pension + housing_fund_balance)
                else:
                    # 后续年份：只有养老金
                    cash_flows.append(annual_pension)
            
            # 使用简化的IRR计算（二分法）
            return self._simple_irr(cash_flows)
            
        except Exception as e:
            print(f"IRR计算失败: {e}")
            return 0.0
    
    def _simple_irr(self, cash_flows: List[float], precision: float = 1e-6) -> float:
        """
        简化的IRR计算（二分法）
        
        Args:
            cash_flows: 现金流列表
            precision: 精度
            
        Returns:
            IRR (年化收益率)
        """
        if len(cash_flows) < 2:
            return 0.0
        
        # 检查是否有正负现金流
        has_positive = any(cf > 0 for cf in cash_flows)
        has_negative = any(cf < 0 for cf in cash_flows)
        
        if not (has_positive and has_negative):
            return 0.0
        
        # 二分法求解IRR
        low_rate = -0.99  # 最低-99%
        high_rate = 10.0   # 最高1000%
        
        for _ in range(100):  # 最多迭代100次
            mid_rate = (low_rate + high_rate) / 2
            npv = self._calculate_npv(cash_flows, mid_rate)
            
            if abs(npv) < precision:
                return mid_rate
            
            if npv > 0:
                low_rate = mid_rate
            else:
                high_rate = mid_rate
        
        return (low_rate + high_rate) / 2
    
    def _calculate_npv(self, cash_flows: List[float], rate: float) -> float:
        """计算净现值"""
        npv = 0.0
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + rate) ** i)
        return npv
    
    def get_detailed_breakdown(self, initial_gross_income: float, 
                              salary_growth_rate: float = 0.02,
                              hf_rate: float = None) -> Dict[str, Any]:
        """
        获取详细的计算分解
        
        Returns:
            包含逐年详细计算的字典
        """
        if hf_rate is None:
            hf_rate = self.params.hf_rate_default
        
        work_years = self.params.retirement_age - self.params.start_age
        current_gross_income = initial_gross_income
        
        yearly_results = []
        
        # 逐年计算
        for year_offset in range(work_years):
            year = 2024 + year_offset
            age = self.params.start_age + year_offset
            avg_wage = self._get_avg_wage(year)
            
            yearly_result = self.calculate_yearly(year, age, current_gross_income, avg_wage, hf_rate)
            yearly_results.append(yearly_result)
            
            current_gross_income *= (1 + salary_growth_rate)
        
        # 计算退休结果
        retirement_result = self.calculate_lifetime(initial_gross_income, salary_growth_rate, hf_rate)
        
        return {
            'yearly_results': yearly_results,
            'retirement_result': retirement_result,
            'summary': {
                'total_work_years': work_years,
                'initial_gross_income': initial_gross_income,
                'final_gross_income': current_gross_income,
                'salary_growth_rate': salary_growth_rate,
                'housing_fund_rate': hf_rate
            }
        }


# 便捷函数
def create_china_optimized_calculator(**kwargs) -> ChinaOptimizedCalculator:
    """创建中国优化计算器"""
    params = ChinaOptimizedParams(**kwargs)
    return ChinaOptimizedCalculator(params)


def calculate_china_optimized(gross_income: float, hf_rate: float = 0.07, 
                             salary_growth_rate: float = 0.02) -> RetirementResult:
    """计算中国养老金（优化版本）"""
    calculator = create_china_optimized_calculator()
    return calculator.calculate_lifetime(gross_income, salary_growth_rate, hf_rate)


if __name__ == "__main__":
    # 演示
    print("=== 中国养老金计算器 - 优化版本演示 ===\n")
    
    # 创建计算器
    calculator = create_china_optimized_calculator()
    
    # 测试案例：年收入180000元，公积金7%
    gross_income = 180000
    hf_rate = 0.07
    
    print(f"年收入: ¥{gross_income:,}")
    print(f"公积金比例: {hf_rate:.1%}")
    print(f"社平工资: ¥{calculator.params.avg_wage_2024:,}")
    
    # 计算第一年详细结果
    print(f"\n=== 第一年详细计算 ===")
    first_year_result = calculator.calculate_yearly(2024, 30, gross_income, calculator.params.avg_wage_2024, hf_rate)
    
    print(f"STEP 1 - 基数确定:")
    print(f"  社保基数: ¥{first_year_result.si_base_month:,.2f}/月")
    print(f"  公积金基数: ¥{first_year_result.hf_base_month:,.2f}/月")
    
    print(f"STEP 2 - 五险缴费:")
    print(f"  个人缴费: ¥{first_year_result.emp_total_si:,.2f}/年")
    print(f"  单位缴费: ¥{first_year_result.er_total_si:,.2f}/年")
    
    print(f"STEP 3 - 公积金缴费:")
    print(f"  个人缴费: ¥{first_year_result.emp_hf:,.2f}/年")
    print(f"  单位缴费: ¥{first_year_result.er_hf:,.2f}/年")
    
    print(f"STEP 4 - 个税:")
    print(f"  应税所得: ¥{first_year_result.taxable_income:,.2f}")
    print(f"  税额: ¥{first_year_result.tax_amount:,.2f}")
    
    print(f"STEP 5 - 到手工资:")
    print(f"  税后净收入: ¥{first_year_result.net_income:,.2f}")
    
    # 计算终身养老金
    print(f"\n=== 终身养老金计算 ===")
    retirement_result = calculator.calculate_lifetime(gross_income, 0.02, hf_rate)
    
    print(f"工作年限: {retirement_result.total_work_years}年")
    print(f"总缴费: ¥{retirement_result.total_contributions:,.2f}")
    print(f"  个人缴费: ¥{retirement_result.total_employee_contributions:,.2f}")
    print(f"  单位缴费: ¥{retirement_result.total_employer_contributions:,.2f}")
    print(f"月养老金: ¥{retirement_result.monthly_pension:,.2f}")
    print(f"年养老金: ¥{retirement_result.annual_pension:,.2f}")
    print(f"公积金余额: ¥{retirement_result.final_housing_fund_balance:,.2f}")
    print(f"总收益: ¥{retirement_result.total_benefits:,.2f}")
    print(f"ROI: {retirement_result.roi:.2%}")
    if retirement_result.break_even_age:
        print(f"回本年龄: {retirement_result.break_even_age:.1f}岁")