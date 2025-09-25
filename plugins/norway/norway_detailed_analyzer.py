#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
挪威详细分析器
参考中国和新加坡的输出格式，提供完整的JSON格式分析输出
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from utils.smart_currency_converter import SmartCurrencyConverter, CurrencyAmount

class NorwayDetailedAnalyzer:
    """挪威详细分析器"""

    def __init__(self):
        self.currency_converter = SmartCurrencyConverter()

    def print_detailed_analysis(self,
                              person,
                              salary_profile,
                              economic_factors,
                              pension_result) -> None:
        """打印详细分析结果"""
        analysis_json = self._generate_analysis_json(person, salary_profile, economic_factors, pension_result)
        print(json.dumps(analysis_json, ensure_ascii=False, indent=2))

    def _generate_analysis_json(self,
                              person,
                              salary_profile,
                              economic_factors,
                              pension_result) -> Dict[str, Any]:
        """生成详细分析JSON"""

        # 获取详细信息
        details = pension_result.details
        national_pension = details.get('national_pension', {})
        occupational_pension = details.get('occupational_pension', {})
        individual_pension = details.get('individual_pension', {})

        # 计算工作年限和退休年限
        work_years = details.get('work_years', 37)
        retirement_age = details.get('retirement_age', 67)
        retirement_years = 90 - retirement_age  # 假设活到90岁

        # 计算人民币对比
        monthly_pension_cny = self.currency_converter.convert_to_local(
            CurrencyAmount(pension_result.monthly_pension, 'NOK', f"{pension_result.monthly_pension} NOK"), "CNY"
        ).amount

        total_contribution_cny = self.currency_converter.convert_to_local(
            CurrencyAmount(pension_result.total_contribution, 'NOK', f"{pension_result.total_contribution} NOK"), "CNY"
        ).amount

        return {
            "基础信息": {
                "国家": "挪威",
                "货币": "NOK",
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "姓名": person.name,
                "年龄": person.age,
                "工作年限": f"{person.age}-{retirement_age-1}岁",
                "退休年龄": retirement_age,
                "退休年限": retirement_years
            },

            "收入信息": {
                "月收入": self._format_decimals(salary_profile.monthly_salary),
                "年收入": self._format_decimals(salary_profile.monthly_salary * 12),
                "年收入_人民币": self._format_decimals(
                    self.currency_converter.convert_to_local(
                        CurrencyAmount(salary_profile.monthly_salary * 12, 'NOK', f"{salary_profile.monthly_salary * 12} NOK"), "CNY"
                    ).amount
                ),
                "年薪上限限制": salary_profile.monthly_salary * 12 > national_pension.get('income_cap', 0)
            },

            "国家养老金缴费": {
                "缴费基数": self._format_decimals(national_pension.get('capped_salary', 0)),
                "收入上限": self._format_decimals(national_pension.get('income_cap', 0)),
                "社保缴费率": {
                    "员工缴费率": "8.2%",
                    "雇主缴费率": "14.1%"
                },
                "年度社保缴费": {
                    "员工缴费": self._format_decimals(national_pension.get('annual_employee_ss_contribution', 0)),
                    "雇主缴费": self._format_decimals(national_pension.get('annual_employer_ss_contribution', 0)),
                    "总缴费": self._format_decimals(national_pension.get('annual_total_ss_contribution', 0))
                },
                "终身社保缴费": self._format_decimals(national_pension.get('total_ss_contribution', 0)),
                "养老金计提": {
                    "计提率": "18.1%",
                    "年度计提": self._format_decimals(national_pension.get('annual_pension_accrual', 0)),
                    "终身计提": self._format_decimals(national_pension.get('total_pension_accrual', 0))
                }
            },

            "职业养老金缴费": {
                "员工缴费率": f"{occupational_pension.get('employee_rate', 0)*100:.1f}% (自愿)",
                "雇主缴费率": {
                    "1G-7.1G区间": f"{occupational_pension.get('employer_rate_1_7_1g', 0)*100:.1f}%",
                    "7.1G-12G区间": f"{occupational_pension.get('employer_rate_7_1g_12g', 0)*100:.1f}%"
                },
                "缴费基数": {
                    "1G-7.1G区间": self._format_decimals(occupational_pension.get('segment_1g_7_1g', 0)),
                    "7.1G-12G区间": self._format_decimals(occupational_pension.get('segment_7_1g_12g', 0))
                },
                "年度缴费": {
                    "员工缴费": self._format_decimals(occupational_pension.get('annual_employee_contribution', 0)),
                    "雇主缴费": self._format_decimals(occupational_pension.get('annual_employer_contribution', 0)),
                    "总缴费": self._format_decimals(occupational_pension.get('annual_total_contribution', 0))
                },
                "终身缴费": self._format_decimals(occupational_pension.get('total_contribution', 0)),
                "最终余额": self._format_decimals(occupational_pension.get('total_balance', 0))
            },

            "个人养老金缴费": {
                "年度缴费": self._format_decimals(individual_pension.get('annual_contribution', 0)),
                "终身缴费": self._format_decimals(individual_pension.get('total_contribution', 0)),
                "最终余额": self._format_decimals(individual_pension.get('total_balance', 0)),
                "年缴费上限": self._format_decimals(individual_pension.get('annual_limit', 0)),
                "说明": "个人养老金(IPS)为自愿缴费，享有税收优惠"
            },

            "投资收益": {
                "国家养老金": {
                    "调整方式": "随工资指数/G指数调整",
                    "说明": "名义账户，不按市场回报计算"
                },
                "职业养老金": {
                    "投资回报率": "5.0%",
                    "增值": self._format_decimals(
                        occupational_pension.get('total_balance', 0) - occupational_pension.get('total_contribution', 0)
                    )
                },
                "个人养老金": {
                    "投资回报率": "4.0%",
                    "增值": self._format_decimals(
                        individual_pension.get('total_balance', 0) - individual_pension.get('total_contribution', 0)
                    )
                },
                "通胀率": f"{economic_factors.inflation_rate*100:.1f}%"
            },

            "退休金计算": {
                "国家养老金": {
                    "月领取金额": self._format_decimals(national_pension.get('monthly_pension', 0)),
                    "年领取金额": self._format_decimals(national_pension.get('annual_pension', 0)),
                    "退休期总领取": self._format_decimals(national_pension.get('annual_pension', 0) * retirement_years)
                },
                "职业养老金": {
                    "月领取金额": self._format_decimals(occupational_pension.get('monthly_pension', 0)),
                    "年领取金额": self._format_decimals(occupational_pension.get('annual_pension', 0)),
                    "退休期总领取": self._format_decimals(occupational_pension.get('annual_pension', 0) * retirement_years)
                },
                "个人养老金": {
                    "月领取金额": self._format_decimals(individual_pension.get('monthly_pension', 0)),
                    "年领取金额": self._format_decimals(individual_pension.get('annual_pension', 0)),
                    "退休期总领取": self._format_decimals(individual_pension.get('annual_pension', 0) * retirement_years)
                },
                "总退休金": {
                    "月领取金额": self._format_decimals(pension_result.monthly_pension),
                    "年领取金额": self._format_decimals(pension_result.monthly_pension * 12),
                    "退休期总领取": self._format_decimals(pension_result.total_benefit)
                }
            },

            "工作期总计": {
                "总工作年限": work_years,
                "总收入": self._format_decimals(salary_profile.monthly_salary * 12 * work_years),
                "国家养老金": {
                    "社保缴费": self._format_decimals(national_pension.get('total_ss_contribution', 0)),
                    "养老金计提": self._format_decimals(national_pension.get('total_pension_accrual', 0))
                },
                "职业养老金缴费": self._format_decimals(occupational_pension.get('total_contribution', 0)),
                "个人养老金缴费": self._format_decimals(individual_pension.get('total_contribution', 0)),
                "总缴费": self._format_decimals(pension_result.total_contribution),
                "缴费占比": f"{(pension_result.total_contribution / (salary_profile.monthly_salary * 12 * work_years) * 100):.1f}%"
            },

            "退休期分析": {
                "年龄范围": f"{retirement_age}-90岁",
                "退休年限": retirement_years,
                "退休金收入": {
                    "月领取金额": self._format_decimals(pension_result.monthly_pension),
                    "年领取金额": self._format_decimals(pension_result.monthly_pension * 12),
                    "退休期总领取": self._format_decimals(pension_result.total_benefit)
                }
            },

            "投资回报分析": {
                "总投入": self._format_decimals(pension_result.total_contribution),
                "总产出": self._format_decimals(pension_result.total_benefit),
                "净收益": self._format_decimals(pension_result.total_benefit - pension_result.total_contribution),
                "投资回报率": f"{pension_result.roi:.1f}%",
                "回本年龄": pension_result.break_even_age if pension_result.break_even_age else "无法回本",
                "回本时间": f"{pension_result.break_even_age - retirement_age}年" if pension_result.break_even_age else "无法回本",
                "替代率": f"{(pension_result.monthly_pension * 12 / (salary_profile.monthly_salary * 12) * 100):.1f}%"
            },

            "三支柱详细分析": {
                "国家养老金": {
                    "制度名称": "Folketrygden",
                    "覆盖范围": "所有在挪威合法居住和工作的居民",
                    "社保缴费": "员工8.2% + 雇主14.1% (进入公共统筹)",
                    "养老金计提": "18.1% × 可计提收入 (封顶7.1G)",
                    "G基础额": "NOK 118,620 (2024年)",
                    "收入上限": f"NOK {national_pension.get('income_cap', 0):,.0f}",
                    "特点": "名义账户制，随工资指数/G指数调整"
                },
                "职业养老金": {
                    "制度名称": "Occupational Pension (OTP)",
                    "覆盖范围": "所有受雇于正规雇主的劳动者",
                    "最低缴费": "雇主必须至少按工资的2%缴纳",
                    "分段缴费": "1G-7.1G区间5%，7.1G-12G区间18.1%",
                    "员工缴费": "自愿缴费，通常3%",
                    "常见方案": "缴费型(Defined Contribution)计划",
                    "特点": "补充国家养老金，按G分段计算"
                },
                "个人养老金": {
                    "制度名称": "Individual Pension Savings (IPS)",
                    "覆盖范围": "自愿的个人储蓄计划",
                    "年缴费上限": "NOK 15,000",
                    "税收优惠": "可抵税",
                    "特点": "个人可额外储蓄，享有税收优惠"
                }
            },

            "退休年龄灵活性": {
                "提前退休": "62岁 (月金额减少)",
                "正常退休": "67岁 (标准月金额)",
                "延迟退休": "75岁 (月金额增加)",
                "说明": "退休金随领取年龄调整，越早领取月金额越少，越晚领取月金额越高"
            },

            "人民币对比": {
                "月退休金": self._format_decimals(monthly_pension_cny),
                "年退休金": self._format_decimals(monthly_pension_cny * 12),
                "总缴费": self._format_decimals(total_contribution_cny),
                "说明": "基于当前汇率转换，仅供参考"
            },

            "风险提示": {
                "政策风险": "养老金政策可能随政府政策调整而变化",
                "投资风险": "职业养老金和个人养老金存在投资风险",
                "长寿风险": "预期寿命延长可能影响养老金可持续性",
                "通胀风险": "通胀可能影响养老金实际购买力",
                "汇率风险": "人民币对比基于当前汇率，存在波动风险"
            }
        }

    def _format_decimals(self, value: float, decimals: int = 2) -> str:
        """格式化小数显示"""
        if value is None:
            return "0.00"
        return f"{value:,.{decimals}f}"
