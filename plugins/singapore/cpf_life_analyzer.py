#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新加坡CPF LIFE综合分析器
提供详细的退休金分析和可视化功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

from .cpf_life_optimized import CPFLifeOptimizedCalculator, CPFLifeResult


@dataclass
class AnalysisConfig:
    """分析配置"""
    start_age: int = 65
    horizon_age: int = 100
    death_ages: List[int] = None
    risk_scenarios: List[float] = None  # 利率风险情景
    inflation_scenarios: List[float] = None  # 通胀情景
    
    def __post_init__(self):
        if self.death_ages is None:
            self.death_ages = [70, 75, 80, 85, 90, 95, 100]
        if self.risk_scenarios is None:
            self.risk_scenarios = [0.02, 0.03, 0.04, 0.05, 0.06]
        if self.inflation_scenarios is None:
            self.inflation_scenarios = [0.01, 0.02, 0.03]


class CPFLifeAnalyzer:
    """CPF LIFE综合分析器"""
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.calculator = CPFLifeOptimizedCalculator()
        
    def comprehensive_analysis(self, RA65: float, 
                             include_sensitivity: bool = True,
                             include_scenarios: bool = True) -> Dict:
        """
        综合分析
        
        Args:
            RA65: 65岁时RA余额
            include_sensitivity: 是否包含敏感性分析
            include_scenarios: 是否包含情景分析
            
        Returns:
            综合分析结果
        """
        results = {
            'basic_analysis': self._basic_plan_analysis(RA65),
            'timestamp': datetime.now().isoformat(),
            'ra65_balance': RA65
        }
        
        if include_sensitivity:
            results['sensitivity_analysis'] = self._sensitivity_analysis(RA65)
            
        if include_scenarios:
            results['scenario_analysis'] = self._scenario_analysis(RA65)
            
        # 添加推荐
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _basic_plan_analysis(self, RA65: float) -> Dict:
        """基础计划分析"""
        # 比较所有计划
        plan_results = self.calculator.compare_plans(RA65, 
                                                    self.config.start_age, 
                                                    self.config.horizon_age)
        
        # 遗赠分析
        bequest_analysis = {}
        for plan in plan_results.keys():
            bequest_analysis[plan] = self.calculator.analyze_bequest_scenarios(
                RA65, plan, self.config.death_ages)
        
        # 最优计划推荐
        optimal_analysis = self.calculator.calculate_optimal_plan(RA65)
        
        return {
            'plan_comparison': plan_results,
            'bequest_analysis': bequest_analysis,
            'optimal_plan': optimal_analysis,
            'summary_table': self._create_summary_table(plan_results)
        }
    
    def _sensitivity_analysis(self, RA65: float) -> Dict:
        """敏感性分析"""
        sensitivity_results = {}
        
        # 利率敏感性
        rate_sensitivity = {}
        for rate in self.config.risk_scenarios:
            self.calculator.set_parameters(r_prem=rate, r_ra=rate)
            results = self.calculator.compare_plans(RA65, 
                                                  self.config.start_age, 
                                                  self.config.horizon_age)
            rate_sensitivity[rate] = {
                plan: {
                    'monthly_income': result.monthly_schedule[0] if result.monthly_schedule else 0,
                    'total_payout': result.total_payout,
                    'final_balance': result.final_balance
                }
                for plan, result in results.items()
            }
        
        # 通胀敏感性（仅对escalating计划）
        inflation_sensitivity = {}
        for inflation in self.config.inflation_scenarios:
            self.calculator.set_parameters(g_esc=inflation)
            result = self.calculator.cpf_life_simulate(RA65, "escalating", 
                                                     self.config.start_age, 
                                                     self.config.horizon_age)
            inflation_sensitivity[inflation] = {
                'monthly_income': result.monthly_schedule[0] if result.monthly_schedule else 0,
                'total_payout': result.total_payout,
                'final_balance': result.final_balance
            }
        
        # 重置参数
        self.calculator.set_parameters()
        
        return {
            'rate_sensitivity': rate_sensitivity,
            'inflation_sensitivity': inflation_sensitivity,
            'sensitivity_summary': self._calculate_sensitivity_summary(rate_sensitivity, inflation_sensitivity)
        }
    
    def _scenario_analysis(self, RA65: float) -> Dict:
        """情景分析"""
        scenarios = {
            'conservative': {'r_prem': 0.03, 'r_ra': 0.03, 'g_esc': 0.015},
            'moderate': {'r_prem': 0.04, 'r_ra': 0.04, 'g_esc': 0.02},
            'optimistic': {'r_prem': 0.05, 'r_ra': 0.05, 'g_esc': 0.025}
        }
        
        scenario_results = {}
        for scenario_name, params in scenarios.items():
            self.calculator.set_parameters(**params)
            results = self.calculator.compare_plans(RA65, 
                                                  self.config.start_age, 
                                                  self.config.horizon_age)
            scenario_results[scenario_name] = results
            
        # 重置参数
        self.calculator.set_parameters()
        
        return {
            'scenarios': scenario_results,
            'scenario_comparison': self._create_scenario_comparison_table(scenario_results)
        }
    
    def _create_summary_table(self, plan_results: Dict[str, CPFLifeResult]) -> List[Dict]:
        """创建汇总表"""
        summary_data = []
        for plan, result in plan_results.items():
            summary_data.append({
                'plan': plan,
                'initial_monthly': result.monthly_schedule[0] if result.monthly_schedule else 0,
                'total_payout': result.total_payout,
                'final_balance': result.final_balance,
                'bequest_at_80': result.snapshots.get('age_80', 0) or 0,
                'payout_efficiency': result.total_payout / result.monthly_schedule[0] if result.monthly_schedule and result.monthly_schedule[0] > 0 else 0
            })
        return summary_data
    
    def _calculate_sensitivity_summary(self, rate_sensitivity: Dict, 
                                     inflation_sensitivity: Dict) -> Dict:
        """计算敏感性汇总"""
        # 利率敏感性汇总
        rate_summary = {}
        for plan in ['standard', 'escalating', 'basic']:
            monthly_incomes = [data[plan]['monthly_income'] 
                             for data in rate_sensitivity.values()]
            rate_summary[plan] = {
                'min_monthly': min(monthly_incomes),
                'max_monthly': max(monthly_incomes),
                'range': max(monthly_incomes) - min(monthly_incomes),
                'volatility': np.std(monthly_incomes) / np.mean(monthly_incomes) if np.mean(monthly_incomes) > 0 else 0
            }
        
        # 通胀敏感性汇总
        inflation_monthly = [data['monthly_income'] for data in inflation_sensitivity.values()]
        inflation_summary = {
            'min_monthly': min(inflation_monthly),
            'max_monthly': max(inflation_monthly),
            'range': max(inflation_monthly) - min(inflation_monthly),
            'volatility': np.std(inflation_monthly) / np.mean(inflation_monthly) if np.mean(inflation_monthly) > 0 else 0
        }
        
        return {
            'rate_sensitivity': rate_summary,
            'inflation_sensitivity': inflation_summary
        }
    
    def _create_scenario_comparison_table(self, scenario_results: Dict) -> Dict:
        """创建情景对比表"""
        comparison = {}
        for scenario_name, plan_results in scenario_results.items():
            comparison[scenario_name] = {}
            for plan, result in plan_results.items():
                comparison[scenario_name][plan] = {
                    'monthly_income': result.monthly_schedule[0] if result.monthly_schedule else 0,
                    'total_payout': result.total_payout,
                    'final_balance': result.final_balance
                }
        return comparison
    
    def _generate_recommendations(self, analysis_results: Dict) -> Dict:
        """生成推荐建议"""
        basic_analysis = analysis_results['basic_analysis']
        optimal_plan = basic_analysis['optimal_plan']['optimal_plan']
        
        recommendations = {
            'primary_recommendation': {
                'plan': optimal_plan,
                'reason': f"基于当前参数，{optimal_plan}计划在综合评分中表现最佳"
            },
            'alternative_options': [],
            'risk_considerations': [],
            'action_items': []
        }
        
        # 添加备选方案
        plan_scores = basic_analysis['optimal_plan']['scores']
        sorted_plans = sorted(plan_scores.items(), key=lambda x: x[1], reverse=True)
        
        for plan, score in sorted_plans[1:]:  # 跳过最优计划
            recommendations['alternative_options'].append({
                'plan': plan,
                'score': score,
                'reason': f"备选方案，评分: {score:.2f}"
            })
        
        # 添加风险考虑
        if 'sensitivity_analysis' in analysis_results:
            sensitivity = analysis_results['sensitivity_analysis']['sensitivity_summary']
            
            # 找出最稳定的计划
            rate_volatility = {plan: data['volatility'] 
                             for plan, data in sensitivity['rate_sensitivity'].items()}
            most_stable = min(rate_volatility, key=rate_volatility.get)
            
            recommendations['risk_considerations'].append({
                'consideration': f"{most_stable}计划对利率变化最不敏感",
                'volatility': rate_volatility[most_stable]
            })
        
        # 添加行动建议
        recommendations['action_items'] = [
            "定期审查CPF LIFE计划选择",
            "考虑个人健康状况和家族寿命",
            "评估对遗赠的需求",
            "关注CPF政策变化"
        ]
        
        return recommendations
    
    def generate_detailed_report(self, RA65: float, 
                               output_format: str = 'json') -> str:
        """
        生成详细报告
        
        Args:
            RA65: 65岁时RA余额
            output_format: 输出格式 ('json', 'text')
            
        Returns:
            报告内容
        """
        analysis = self.comprehensive_analysis(RA65)
        
        if output_format == 'json':
            return json.dumps(analysis, indent=2, ensure_ascii=False, default=str)
        else:
            return self._format_text_report(analysis)
    
    def _format_text_report(self, analysis: Dict) -> str:
        """格式化文本报告"""
        report = []
        report.append("=" * 60)
        report.append("新加坡CPF LIFE综合分析报告")
        report.append("=" * 60)
        report.append(f"分析时间: {analysis['timestamp']}")
        report.append(f"RA65余额: ${analysis['ra65_balance']:,.2f}")
        report.append("")
        
        # 基础分析
        basic = analysis['basic_analysis']
        report.append("1. 计划对比分析")
        report.append("-" * 30)
        
        for plan_data in basic['summary_table']:
            report.append(f"{plan_data['plan'].upper()}计划:")
            report.append(f"  初始月收入: ${plan_data['initial_monthly']:,.2f}")
            report.append(f"  总领取金额: ${plan_data['total_payout']:,.2f}")
            report.append(f"  最终余额: ${plan_data['final_balance']:,.2f}")
            report.append(f"  80岁遗赠: ${plan_data['bequest_at_80']:,.2f}")
            report.append("")
        
        # 推荐
        recommendations = analysis['recommendations']
        report.append("2. 推荐建议")
        report.append("-" * 30)
        report.append(f"主要推荐: {recommendations['primary_recommendation']['plan']}计划")
        report.append(f"推荐理由: {recommendations['primary_recommendation']['reason']}")
        report.append("")
        
        report.append("备选方案:")
        for alt in recommendations['alternative_options']:
            report.append(f"  - {alt['plan']}计划: {alt['reason']}")
        report.append("")
        
        report.append("风险考虑:")
        for risk in recommendations['risk_considerations']:
            report.append(f"  - {risk['consideration']}")
        report.append("")
        
        report.append("行动建议:")
        for action in recommendations['action_items']:
            report.append(f"  - {action}")
        
        return "\n".join(report)
    
    def export_analysis_data(self, RA65: float, 
                           filename: str = None) -> str:
        """
        导出分析数据到CSV
        
        Args:
            RA65: 65岁时RA余额
            filename: 文件名
            
        Returns:
            文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cpf_life_analysis_{timestamp}.csv"
        
        analysis = self.comprehensive_analysis(RA65)
        
        # 创建DataFrame
        data = []
        for plan_data in analysis['basic_analysis']['summary_table']:
            data.append({
                'Plan': plan_data['plan'],
                'Initial_Monthly_Income': plan_data['initial_monthly'],
                'Total_Payout': plan_data['total_payout'],
                'Final_Balance': plan_data['final_balance'],
                'Bequest_at_80': plan_data['bequest_at_80'],
                'Payout_Efficiency': plan_data['payout_efficiency']
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
        return filename


# 便捷函数
def quick_analysis(RA65: float, config: AnalysisConfig = None) -> Dict:
    """
    快速分析
    
    Args:
        RA65: 65岁时RA余额
        config: 分析配置
        
    Returns:
        分析结果
    """
    analyzer = CPFLifeAnalyzer(config)
    return analyzer.comprehensive_analysis(RA65)


def generate_report(RA65: float, output_format: str = 'text') -> str:
    """
    生成报告
    
    Args:
        RA65: 65岁时RA余额
        output_format: 输出格式
        
    Returns:
        报告内容
    """
    analyzer = CPFLifeAnalyzer()
    return analyzer.generate_detailed_report(RA65, output_format)