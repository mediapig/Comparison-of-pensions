#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用JSON分析器
为不同国家提供统一的JSON格式输出
"""

from typing import Dict, Any, Optional
from core.models import Person, SalaryProfile, EconomicFactors, PensionResult
from utils.smart_currency_converter import CurrencyAmount


class UniversalJSONAnalyzer:
    """通用JSON分析器"""
    
    def __init__(self):
        self.country_mappings = {
            'SG': {
                'name': '新加坡',
                'code': 'SG',
                'currency': 'SGD',
                'accounts': {
                    'oa': '普通账户_OA',
                    'sa': '特别账户_SA', 
                    'ma': '医疗账户_MA',
                    'ra': '退休账户_RA'
                }
            },
            'CN': {
                'name': '中国',
                'code': 'CN',
                'currency': 'CNY',
                'accounts': {
                    'basic': '基本养老保险',
                    'personal': '个人账户',
                    'pooled': '统筹账户'
                }
            },
            'US': {
                'name': '美国',
                'code': 'US',
                'currency': 'USD',
                'accounts': {
                    'social_security': '社会保障_Social_Security',
                    '401k': '401k账户',
                    'ira': 'IRA账户'
                }
            }
        }
    
    def generate_standard_json(self,
                             country_code: str,
                             person: Person,
                             salary_profile: SalaryProfile,
                             economic_factors: EconomicFactors,
                             pension_result: PensionResult,
                             local_amount: CurrencyAmount,
                             additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        生成标准化的JSON分析结果
        
        Args:
            country_code: 国家代码
            person: 个人信息
            salary_profile: 薪资信息
            economic_factors: 经济因素
            pension_result: 养老金结果
            local_amount: 本地货币金额
            additional_data: 额外的国家特定数据
            
        Returns:
            标准化的JSON数据
        """
        
        country_info = self.country_mappings.get(country_code, {
            'name': '未知国家',
            'code': country_code,
            'currency': 'UNKNOWN',
            'accounts': {}
        })
        
        # 基础结构
        json_data = {
            "国家": country_info['name'],
            "国家代码": country_info['code'],
            "货币": country_info['currency'],
            "分析时间": "2024年",
            "第一年分析": self._generate_first_year_analysis(person, salary_profile, local_amount, additional_data),
            "工作期总计": self._generate_work_period_summary(person, salary_profile, pension_result, additional_data),
            "退休期分析": self._generate_retirement_analysis(pension_result),
            "最终账户余额": self._generate_final_accounts(pension_result, country_info['accounts']),
            "90岁时账户余额": self._generate_terminal_accounts(pension_result, country_info['accounts']),
            "投资回报分析": self._generate_roi_analysis(pension_result),
            "人民币对比": self._generate_cny_comparison(pension_result, country_info['currency'])
        }
        
        return json_data
    
    def _generate_first_year_analysis(self, person: Person, salary_profile: SalaryProfile, 
                                    local_amount: CurrencyAmount, additional_data: Optional[Dict]) -> Dict[str, Any]:
        """生成第一年分析数据"""
        return {
            "年龄": person.age if person.age > 0 else 30,
            "收入情况": {
                "年收入": local_amount.amount,
                "缴费基数": local_amount.amount,  # 各国可自定义
                "上限限制": False  # 各国可自定义
            },
            "社保缴费": additional_data.get('social_security', {}) if additional_data else {},
            "账户分配": additional_data.get('account_allocation', {}) if additional_data else {},
            "税务情况": additional_data.get('tax_situation', {}) if additional_data else {}
        }
    
    def _generate_work_period_summary(self, person: Person, salary_profile: SalaryProfile,
                                    pension_result: PensionResult, additional_data: Optional[Dict]) -> Dict[str, Any]:
        """生成工作期总计数据"""
        work_years = person.work_years if person.work_years > 0 else 35
        start_age = person.age if person.age > 0 else 30
        
        return {
            "工作年限": work_years,
            "年龄范围": f"{start_age}-{start_age + work_years - 1}岁",
            "收入情况": additional_data.get('income_summary', {}) if additional_data else {},
            "社保缴费总计": additional_data.get('social_security_total', {}) if additional_data else {},
            "账户分配总计": additional_data.get('account_allocation_total', {}) if additional_data else {}
        }
    
    def _generate_retirement_analysis(self, pension_result: PensionResult) -> Dict[str, Any]:
        """生成退休期分析数据"""
        return {
            "年龄范围": "65-90岁",  # 各国可自定义
            "退休年限": 25,  # 各国可自定义
            "退休金收入": {
                "月领取金额": pension_result.monthly_pension,
                "年领取金额": pension_result.monthly_pension * 12,
                "退休期总领取": pension_result.total_benefit
            }
        }
    
    def _generate_final_accounts(self, pension_result: PensionResult, account_mapping: Dict[str, str]) -> Dict[str, Any]:
        """生成最终账户余额数据"""
        final_accounts = {}
        
        if hasattr(pension_result, 'details') and pension_result.details and 'cpf_accounts' in pension_result.details:
            accounts = pension_result.details['cpf_accounts']
            for key, value in accounts.items():
                mapped_name = account_mapping.get(key, key)
                final_accounts[mapped_name] = value
            
            # 计算总余额
            final_accounts["总余额"] = sum(accounts.values())
        
        return final_accounts
    
    def _generate_terminal_accounts(self, pension_result: PensionResult, account_mapping: Dict[str, str]) -> Dict[str, Any]:
        """生成90岁时账户余额数据"""
        terminal_accounts = {}
        
        # 从IRR分析结果中获取90岁时的账户余额
        if hasattr(pension_result, 'details') and pension_result.details and 'irr_analysis' in pension_result.details:
            irr_analysis = pension_result.details['irr_analysis']
            if 'terminal_accounts' in irr_analysis:
                accounts = irr_analysis['terminal_accounts']
                for key, value in accounts.items():
                    if key != 'total':  # 跳过total字段
                        mapped_name = account_mapping.get(key, key)
                        terminal_accounts[mapped_name] = value
                
                # 添加总余额
                terminal_accounts["总余额"] = accounts.get('total', 0)
        
        return terminal_accounts
    
    def _generate_roi_analysis(self, pension_result: PensionResult) -> Dict[str, Any]:
        """生成投资回报分析数据"""
        return {
            "简单回报率": pension_result.roi,
            "内部收益率_IRR": pension_result.roi,
            "回本分析": {
                "回本年龄": pension_result.break_even_age if pension_result.break_even_age else None,
                "回本时间": (pension_result.break_even_age - 65) if pension_result.break_even_age else None,
                "能否回本": pension_result.break_even_age is not None
            }
        }
    
    def _generate_cny_comparison(self, pension_result: PensionResult, currency: str) -> Dict[str, Any]:
        """生成人民币对比数据"""
        # 这里需要货币转换，简化处理
        return {
            "退休金收入": {
                "月退休金": pension_result.monthly_pension  # 简化，实际需要转换
            },
            "缴费情况": {
                "总缴费": pension_result.total_contribution  # 简化，实际需要转换
            }
        }