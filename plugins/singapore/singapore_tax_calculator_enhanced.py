#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡个人所得税计算器 - 增强版
基于2024-2025年最新税务政策，包含CPF减免、捐赠扣除等复杂规则
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class EmploymentCash:
    """就业现金收入"""
    monthly_wages: float = 0.0      # 月薪
    bonuses: float = 0.0            # 奖金
    allowances: float = 0.0          # 津贴
    director_fees: float = 0.0      # 董事费


@dataclass
class CPFInfo:
    """CPF信息"""
    cash_topup_SA_RA: float = 0.0           # 现金补SA/RA（自己）
    cash_topup_family_SA_RA: float = 0.0    # 现金补SA/RA（家属）
    vc_medisave: float = 0.0               # 自愿补Medisave
    ma_balance: float = 0.0                # MA账户余额
    bhs: float = 75500.0                   # BHS上限


@dataclass
class TaxInputs:
    """税务计算输入"""
    employment_cash: EmploymentCash
    employment_expenses: float = 0.0        # 就业相关费用
    trade_business_net: float = 0.0        # 自雇净收入
    rental_net: float = 0.0                # 租金净收入
    other_taxable_income: float = 0.0      # 其他应税收入
    approved_donations: float = 0.0        # 核准捐赠
    other_reliefs: float = 0.0             # 其他个人减免
    cpf: CPFInfo = None
    is_tax_resident: bool = True           # 是否为税务居民

    def __post_init__(self):
        if self.cpf is None:
            self.cpf = CPFInfo()


@dataclass
class TaxConfig:
    """税务配置"""
    donation_multiplier: float = 2.5       # 捐赠倍数
    overall_relief_cap: float = 80000.0    # 总减免封顶
    rstr_self_cap: float = 8000.0          # RSTR自己上限
    rstr_family_cap: float = 8000.0         # RSTR家属上限
    vc_ma_cap: float = 8000.0              # VC-MA上限
    nonresident_employment_flat: float = 0.15  # 非居民就业收入税率
    resident_brackets: List[Tuple[float, float]] = None  # 居民税率表

    def __post_init__(self):
        if self.resident_brackets is None:
            # 2024年新加坡居民税率表
            self.resident_brackets = [
                (20000, 0.0),      # 0-20,000: 0%
                (30000, 0.02),     # 20,001-30,000: 2%
                (40000, 0.035),    # 30,001-40,000: 3.5%
                (80000, 0.07),     # 40,001-80,000: 7%
                (120000, 0.115),   # 80,001-120,000: 11.5%
                (160000, 0.15),    # 120,001-160,000: 15%
                (200000, 0.18),    # 160,001-200,000: 18%
                (240000, 0.19),    # 200,001-240,000: 19%
                (280000, 0.195),   # 240,001-280,000: 19.5%
                (320000, 0.20),    # 280,001-320,000: 20%
                (500000, 0.22),    # 320,001-500,000: 22%
                (1000000, 0.23),  # 500,001-1,000,000: 23%
                (float('inf'), 0.24)  # 1,000,001+: 24%
            ]


class SingaporeTaxCalculatorEnhanced:
    """新加坡个人所得税计算器 - 增强版"""

    def __init__(self):
        self.country_code = 'SG'
        self.country_name = '新加坡'
        self.currency = 'SGD'

    def round2(self, x: float) -> float:
        """四舍五入到分"""
        return round(x + 1e-12, 2)

    def calc_cpf_reliefs(self, cpf: CPFInfo, config: TaxConfig) -> float:
        """计算CPF相关减免"""
        relief = 0.0

        # 1) 现金补 SA/RA (RSTR 自己)
        own_topup_cap = config.rstr_self_cap
        own_topup_relief = min(cpf.cash_topup_SA_RA, own_topup_cap)

        # 2) 给家属 SA/RA 的现金补（家庭顶额）
        family_topup_cap = config.rstr_family_cap
        family_topup_relief = min(cpf.cash_topup_family_SA_RA, family_topup_cap)

        # 3) VC-MA（自愿补 Medisave）
        # 需同时满足：不超过政策VC-MA上限 && 不超过BHS允许的空间
        vc_ma_cap = config.vc_ma_cap
        bhs_room = max(0.0, cpf.bhs - cpf.ma_balance)
        vc_ma_relief = min(cpf.vc_medisave, vc_ma_cap, bhs_room)

        relief += own_topup_relief + family_topup_relief + vc_ma_relief
        return relief

    def compute_progressive_tax(self, chargeable_income: float, brackets: List[Tuple[float, float]]) -> float:
        """计算累进税"""
        tax = 0.0
        lower = 0.0
        for upper, rate in brackets:
            slab = min(chargeable_income, upper) - lower
            if slab > 0:
                tax += slab * rate
            if chargeable_income <= upper:
                break
            lower = upper
        return tax

    def calc_tax(self, inputs: TaxInputs, config: TaxConfig = None) -> Dict:
        """
        计算新加坡个人所得税
        
        Args:
            inputs: 税务计算输入
            config: 税务配置
            
        Returns:
            税务计算结果
        """
        if config is None:
            config = TaxConfig()

        # =============== 1) 就业收入的"计税口径" ==================
        # 现金收入：工资/奖金/津贴/董事费（你收到的现金）
        gross_employment_cash = (
            inputs.employment_cash.monthly_wages +
            inputs.employment_cash.bonuses +
            inputs.employment_cash.allowances +
            inputs.employment_cash.director_fees
        )

        # 雇主CPF不计税；雇员强制CPF不额外抵税（不从就业收入中扣）
        # employment_expenses 可按 IRAS 规则扣除
        net_employment_income = max(0.0, gross_employment_cash - inputs.employment_expenses)

        # =============== 2) 其他来源的应税净所得 ===================
        # 例如 自雇/租金/其他收入已为"净额"
        other_statutory = (
            inputs.trade_business_net +
            inputs.rental_net +
            inputs.other_taxable_income
        )

        # =============== 3) Assessable Income（扣除捐赠前）==========
        assessable_before_donation = net_employment_income + other_statutory

        # =============== 4) 捐赠扣除（通常 IPC*2.5） ===============
        donation_deduction = inputs.approved_donations * config.donation_multiplier
        assessable_after_donation = max(0.0, assessable_before_donation - donation_deduction)

        # =============== 5) 个人减免（含 CPF 相关的"可扣税" ）=======
        # 5.1 计算 CPF 相关可扣税：RSTR/VC-MA（注意BHS/FRS/年度限额）
        cpf_relief = self.calc_cpf_reliefs(inputs.cpf, config)

        # 5.2 加总其他个人减免（配偶/子女/残障/课程费/NS等外部给值）
        total_reliefs = cpf_relief + inputs.other_reliefs

        # 5.3 总减免封顶
        total_reliefs_capped = min(total_reliefs, config.overall_relief_cap)

        # =============== 6) Chargeable Income（应纳税所得额）========
        chargeable_income = max(0.0, assessable_after_donation - total_reliefs_capped)

        # =============== 7) 计算应纳税额 ===========================
        if inputs.is_tax_resident:
            tax_resident = self.compute_progressive_tax(chargeable_income, config.resident_brackets)
            tax_payable = tax_resident
        else:
            # 非居民：就业现金收入部分按 15% 或 居民累进税孰高（仅示意）
            resident_like = self.compute_progressive_tax(chargeable_income, config.resident_brackets)
            flat_15 = gross_employment_cash * config.nonresident_employment_flat
            tax_payable = max(resident_like, flat_15)

        return {
            "gross_employment_cash": self.round2(gross_employment_cash),
            "net_employment_income": self.round2(net_employment_income),
            "assessable_before_donation": self.round2(assessable_before_donation),
            "donation_deduction": self.round2(donation_deduction),
            "assessable_after_donation": self.round2(assessable_after_donation),
            "cpf_relief": self.round2(cpf_relief),
            "other_reliefs": self.round2(inputs.other_reliefs),
            "total_reliefs_capped": self.round2(total_reliefs_capped),
            "chargeable_income": self.round2(chargeable_income),
            "tax_payable": self.round2(tax_payable),
            "effective_rate": self.round2((tax_payable / gross_employment_cash * 100) if gross_employment_cash > 0 else 0),
            "net_income": self.round2(gross_employment_cash - tax_payable)
        }

    def calculate_simple_tax(self, 
                           annual_income: float, 
                           cpf_contribution: float = 0,
                           other_reliefs: float = 0,
                           donations: float = 0) -> Dict:
        """
        简化的税务计算（用于兼容现有接口）
        
        Args:
            annual_income: 年收入
            cpf_contribution: CPF缴费（用于计算CPF减免）
            other_reliefs: 其他减免
            donations: 捐赠金额
            
        Returns:
            税务计算结果
        """
        # 创建简化的输入
        inputs = TaxInputs(
            employment_cash=EmploymentCash(monthly_wages=annual_income),
            other_reliefs=other_reliefs,
            approved_donations=donations,
            cpf=CPFInfo(
                cash_topup_SA_RA=cpf_contribution,  # 假设CPF缴费作为RSTR
                ma_balance=0,  # 假设MA余额为0
                bhs=75500
            )
        )

        return self.calc_tax(inputs)

    def get_tax_brackets(self) -> List[Dict]:
        """获取税率表"""
        brackets = []
        config = TaxConfig()
        lower = 0
        for upper, rate in config.resident_brackets:
            brackets.append({
                'min': lower,
                'max': upper if upper != float('inf') else None,
                'rate': rate,
                'description': f"{lower:,} - {upper:,}" if upper != float('inf') else f"{lower:,}+"
            })
            lower = upper
        return brackets

    def get_relief_info(self) -> Dict:
        """获取减免信息"""
        config = TaxConfig()
        return {
            'donation_multiplier': config.donation_multiplier,
            'overall_relief_cap': config.overall_relief_cap,
            'rstr_self_cap': config.rstr_self_cap,
            'rstr_family_cap': config.rstr_family_cap,
            'vc_ma_cap': config.vc_ma_cap,
            'bhs': 75500,
            'frs': 198800
        }

    def calculate_effective_tax_rate(self, annual_income: float, deductions: Dict = None) -> float:
        """计算有效税率"""
        if deductions is None:
            deductions = {}
        
        result = self.calculate_simple_tax(
            annual_income=annual_income,
            cpf_contribution=deductions.get('cpf_contribution', 0),
            other_reliefs=deductions.get('other_reliefs', 0),
            donations=deductions.get('donations', 0)
        )
        
        return result['effective_rate']

    def calculate_net_income(self, annual_income: float, deductions: Dict = None) -> float:
        """计算税后净收入"""
        if deductions is None:
            deductions = {}
        
        result = self.calculate_simple_tax(
            annual_income=annual_income,
            cpf_contribution=deductions.get('cpf_contribution', 0),
            other_reliefs=deductions.get('other_reliefs', 0),
            donations=deductions.get('donations', 0)
        )
        
        return result['net_income']

    def get_tax_summary(self, annual_income: float, deductions: Dict = None) -> Dict:
        """获取税收汇总信息"""
        if deductions is None:
            deductions = {}
        
        result = self.calculate_simple_tax(
            annual_income=annual_income,
            cpf_contribution=deductions.get('cpf_contribution', 0),
            other_reliefs=deductions.get('other_reliefs', 0),
            donations=deductions.get('donations', 0)
        )

        return {
            'country_code': self.country_code,
            'country_name': self.country_name,
            'currency': self.currency,
            'annual_income': annual_income,
            'total_tax': result['tax_payable'],
            'net_income': result['net_income'],
            'effective_tax_rate': result['effective_rate'],
            'monthly_net_income': result['net_income'] / 12,
            'details': result
        }