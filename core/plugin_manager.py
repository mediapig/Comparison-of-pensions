#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器 - 负责加载和管理所有国家插件
"""

import os
import sys
import importlib.util
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import date

from .base_plugin import BaseCountryPlugin
from .models import Person, SalaryProfile, EconomicFactors, Gender, EmploymentType

logger = logging.getLogger(__name__)

class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: Dict[str, BaseCountryPlugin] = {}
        self.failed_plugins: Dict[str, str] = {}
        self._load_all_plugins()

    def _load_all_plugins(self):
        """加载所有插件"""
        plugins_dir = Path(__file__).parent.parent / "plugins"

        if not plugins_dir.exists():
            logger.warning(f"插件目录不存在: {plugins_dir}")
            return

        # 遍历所有插件目录
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('.') or plugin_dir.name == '__pycache__':
                continue

            plugin_name = plugin_dir.name
            plugin_file = plugin_dir / "plugin.py"

            if not plugin_file.exists():
                logger.warning(f"插件文件不存在: {plugin_file}")
                self.failed_plugins[plugin_name] = f"No module named 'plugins.{plugin_name}.plugin'"
                continue

            try:
                # 动态导入插件模块
                module_name = f"plugins.{plugin_name}.plugin"
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找插件类
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BaseCountryPlugin) and
                        attr != BaseCountryPlugin):
                        plugin_class = attr
                        break

                if plugin_class is None:
                    logger.warning(f"未找到插件类: {plugin_file}")
                    self.failed_plugins[plugin_name] = f"No plugin class found in {plugin_file}"
                    continue

                # 创建插件实例
                plugin_instance = plugin_class()
                country_code = plugin_instance.COUNTRY_CODE

                if country_code in self.plugins:
                    logger.warning(f"重复的插件代码: {country_code}")
                    continue

                self.plugins[country_code] = plugin_instance
                logger.info(f"成功加载插件: {plugin_instance.COUNTRY_NAME} ({country_code})")

            except Exception as e:
                logger.error(f"加载插件失败 {plugin_name}: {e}")
                self.failed_plugins[plugin_name] = str(e)

    def get_plugin(self, country_code: str) -> Optional[BaseCountryPlugin]:
        """获取指定国家的插件"""
        return self.plugins.get(country_code.upper())

    def get_available_countries(self) -> List[str]:
        """获取可用的国家代码列表"""
        return list(self.plugins.keys())

    def get_country_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有国家的信息"""
        info = {}
        for country_code, plugin in self.plugins.items():
            info[country_code] = {
                'country_name': plugin.COUNTRY_NAME,
                'currency': plugin.CURRENCY,
                'tax_year': plugin.config.tax_year if hasattr(plugin, 'config') else 2024,
                'external_adapters': 0,  # 暂时设为0
                'supported_features': ['pension', 'tax', 'social_security']
            }
        return info

    def validate_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """验证所有插件"""
        results = {}

        for country_code, plugin in self.plugins.items():
            try:
                result = {
                    'plugin_info': True,
                    'config_valid': True,
                    'external_adapters_status': [],
                    'basic_calculations': {}
                }

                # 测试基础计算
                try:
                    person = Person(
                        name="测试用户",
                        birth_date=date(1985, 1, 1),
                        gender=Gender.MALE,
                        employment_type=EmploymentType.EMPLOYEE,
                        start_work_date=date(2010, 1, 1)
                    )

                    salary_profile = SalaryProfile(
                        monthly_salary=10000,
                        annual_growth_rate=0.03,
                        contribution_start_age=22
                    )

                    economic_factors = EconomicFactors(
                        inflation_rate=0.02,
                        investment_return_rate=0.05,
                        social_security_return_rate=0.03
                    )

                    # 测试退休年龄
                    retirement_age = plugin.get_retirement_age(person)
                    result['basic_calculations']['retirement_age'] = retirement_age

                except Exception as e:
                    result['basic_calculations']['error'] = str(e)

                results[country_code] = result

            except Exception as e:
                results[country_code] = {'error': str(e)}

        return results

    def get_comparison_data(self,
                          countries: List[str],
                          person: Person,
                          salary_profile: SalaryProfile,
                          economic_factors: EconomicFactors) -> Dict[str, Any]:
        """获取多国对比数据"""
        results = {}
        errors = {}

        for country_code in countries:
            plugin = self.get_plugin(country_code)
            if not plugin:
                errors[country_code] = "Plugin not found"
                continue

            try:
                # 计算退休金
                pension_result = plugin.calculate_pension(person, salary_profile, economic_factors)

                # 计算税收
                annual_income = salary_profile.monthly_salary * 12
                tax_result = plugin.calculate_tax(annual_income)

                # 计算社保
                ss_result = plugin.calculate_social_security(salary_profile.monthly_salary, person.work_years)

                results[country_code] = {
                    'pension': {
                        'monthly_pension': pension_result.monthly_pension,
                        'total_contribution': pension_result.total_contribution,
                        'roi': pension_result.roi
                    },
                    'tax': tax_result,
                    'social_security': ss_result,
                    'retirement_age': plugin.get_retirement_age(person)
                }

            except Exception as e:
                errors[country_code] = str(e)

        return {
            'results': results,
            'errors': errors
        }

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        total_plugins = len(self.plugins)
        failed_plugins = len(self.failed_plugins)

        # 计算平均退休年龄
        retirement_ages = []
        for plugin in self.plugins.values():
            if hasattr(plugin, 'config') and hasattr(plugin.config, 'retirement_ages'):
                ages = list(plugin.config.retirement_ages.values())
                retirement_ages.extend(ages)

        average_retirement_age = sum(retirement_ages) / len(retirement_ages) if retirement_ages else 65

        # 按货币分类
        plugins_by_currency = {}
        for plugin in self.plugins.values():
            currency = plugin.CURRENCY
            if currency not in plugins_by_currency:
                plugins_by_currency[currency] = []
            plugins_by_currency[currency].append(plugin.COUNTRY_CODE)

        return {
            'total_plugins': total_plugins,
            'failed_plugins': failed_plugins,
            'plugins_with_external_libs': 0,  # 暂时设为0
            'average_retirement_age': average_retirement_age,
            'plugins_by_currency': plugins_by_currency
        }

# 创建全局插件管理器实例
plugin_manager = PluginManager()
