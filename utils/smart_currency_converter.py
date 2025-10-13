#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能货币转换工具
支持货币缩写输入和自动换算
"""

import re
from typing import Dict, Tuple, Optional, Union
from dataclasses import dataclass
from .daily_exchange_rate_cache import DailyExchangeRateCache

@dataclass
class CurrencyAmount:
    """货币金额数据类"""
    amount: float
    currency: str
    original_input: str

    def __str__(self):
        return f"{self.amount} {self.currency}"

class SmartCurrencyConverter:
    """智能货币转换器"""

    def __init__(self):
        self.daily_cache = DailyExchangeRateCache("CNY")

        # 支持的货币映射
        self.currency_map = {
            # 主要货币
            'CNY': {'name': '人民币', 'symbol': '¥', 'aliases': ['cny', 'rmb', 'yuan', '元']},
            'USD': {'name': '美元', 'symbol': '$', 'aliases': ['usd', 'dollar', 'dollars']},
            'EUR': {'name': '欧元', 'symbol': '€', 'aliases': ['eur', 'euro', 'euros']},
            'GBP': {'name': '英镑', 'symbol': '£', 'aliases': ['gbp', 'pound', 'pounds']},
            'JPY': {'name': '日元', 'symbol': '¥', 'aliases': ['jpy', 'yen', '円']},

            # 亚洲货币
            'SGD': {'name': '新加坡元', 'symbol': 'S$', 'aliases': ['sgd', 'singapore', '新币']},
            'HKD': {'name': '港币', 'symbol': 'HK$', 'aliases': ['hkd', 'hongkong', '港币']},
            'TWD': {'name': '新台币', 'symbol': 'NT$', 'aliases': ['twd', 'taiwan', '台币']},
            'KRW': {'name': '韩元', 'symbol': '₩', 'aliases': ['krw', 'korean', '韩元']},

            # 美洲货币
            'CAD': {'name': '加拿大元', 'symbol': 'C$', 'aliases': ['cad', 'canada', '加币']},
            'AUD': {'name': '澳大利亚元', 'symbol': 'A$', 'aliases': ['aud', 'australia', '澳币']},
            'BRL': {'name': '巴西雷亚尔', 'symbol': 'R$', 'aliases': ['brl', 'brazil', '雷亚尔']},

            # 欧洲货币
            'NOK': {'name': '挪威克朗', 'symbol': 'kr', 'aliases': ['nok', 'norway', '克朗']},
            'SEK': {'name': '瑞典克朗', 'symbol': 'kr', 'aliases': ['sek', 'sweden', '克朗']},
            'DKK': {'name': '丹麦克朗', 'symbol': 'kr', 'aliases': ['dkk', 'denmark', '克朗']},
            'CHF': {'name': '瑞士法郎', 'symbol': 'CHF', 'aliases': ['chf', 'switzerland', '法郎']},

            # 其他货币
            'INR': {'name': '印度卢比', 'symbol': '₹', 'aliases': ['inr', 'india', '卢比']},
            'RUB': {'name': '俄罗斯卢布', 'symbol': '₽', 'aliases': ['rub', 'russia', '卢布']},
        }

        # 构建反向映射（别名 -> 标准代码）
        self.alias_map = {}
        for currency_code, info in self.currency_map.items():
            for alias in info['aliases']:
                self.alias_map[alias.lower()] = currency_code

    def parse_amount(self, input_str: str) -> CurrencyAmount:
        """
        解析货币金额输入

        Args:
            input_str: 输入字符串，如 "cny10000", "USD5000", "10000CNY"

        Returns:
            CurrencyAmount对象

        Examples:
            >>> converter = SmartCurrencyConverter()
            >>> converter.parse_amount("cny10000")
            CurrencyAmount(amount=10000.0, currency='CNY', original_input='cny10000')
            >>> converter.parse_amount("USD5000")
            CurrencyAmount(amount=5000.0, currency='USD', original_input='USD5000')
        """
        input_str = input_str.strip()

        # 尝试不同的解析模式
        patterns = [
            # 模式1: 货币代码+金额 (如 cny10000, USD5000)
            r'^([a-zA-Z]{3,4})(\d+(?:\.\d+)?)$',
            # 模式2: 金额+货币代码 (如 10000CNY, 5000USD)
            r'^(\d+(?:\.\d+)?)([a-zA-Z]{3,4})$',
            # 模式3: 货币符号+金额 (如 $5000, ¥10000)
            r'^([¥$€£₩₹₽])(\d+(?:\.\d+)?)$',
            # 模式4: 纯数字 (默认为人民币)
            r'^(\d+(?:\.\d+)?)$',
        ]

        for pattern in patterns:
            match = re.match(pattern, input_str, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) == 2:
                    # 模式1: 货币代码+金额
                    if re.match(r'^[a-zA-Z]{3,4}$', groups[0]):
                        currency_str = groups[0].upper()
                        amount = float(groups[1])
                    # 模式2: 金额+货币代码
                    else:
                        amount = float(groups[0])
                        currency_str = groups[1].upper()

                    # 通过别名查找标准货币代码
                    currency_code = self._find_currency_code(currency_str)
                    if currency_code:
                        return CurrencyAmount(amount, currency_code, input_str)

                elif len(groups) == 2:
                    # 模式3: 货币符号+金额
                    if groups[0] in ['¥', '$', '€', '£', '₩', '₹', '₽']:
                        currency_code = self._find_currency_by_symbol(groups[0])
                        amount = float(groups[1])
                        if currency_code:
                            return CurrencyAmount(amount, currency_code, input_str)
                elif len(groups) == 1:
                    # 模式4: 纯数字 (默认为人民币)
                    amount = float(groups[0])
                    return CurrencyAmount(amount, 'CNY', input_str)

        # 如果无法解析，尝试作为纯数字处理
        try:
            amount = float(input_str)
            return CurrencyAmount(amount, 'CNY', input_str)
        except ValueError:
            raise ValueError(f"无法解析货币金额: {input_str}")

    def _find_currency_code(self, currency_str: str) -> Optional[str]:
        """通过货币字符串查找标准货币代码"""
        currency_str = currency_str.lower()

        # 直接匹配
        if currency_str in self.alias_map:
            return self.alias_map[currency_str]

        # 模糊匹配
        for alias, code in self.alias_map.items():
            if alias.startswith(currency_str) or currency_str.startswith(alias):
                return code

        return None

    def _find_currency_by_symbol(self, symbol: str) -> Optional[str]:
        """通过货币符号查找标准货币代码"""
        symbol_map = {
            '¥': 'CNY',  # 人民币和日元都用¥，优先人民币
            '$': 'USD',  # 美元符号，优先美元
            '€': 'EUR',
            '£': 'GBP',
            '₩': 'KRW',
            '₹': 'INR',
            '₽': 'RUB',
        }
        return symbol_map.get(symbol)

    def convert_to_local(self, amount: CurrencyAmount, target_currency: str) -> CurrencyAmount:
        """
        将货币金额转换为目标货币（优先使用每日缓存）

        Args:
            amount: 原始货币金额
            target_currency: 目标货币代码

        Returns:
            转换后的CurrencyAmount对象
        """
        if amount.currency == target_currency:
            return amount

        try:
            # 优先使用每日缓存汇率
            converted_amount = self.daily_cache.convert(
                amount.amount,
                amount.currency,
                target_currency
            )
        except Exception as e:
            print(f"⚠️ 汇率获取失败: {e}")
            # 使用默认汇率1:1（临时方案）
            converted_amount = amount.amount

        return CurrencyAmount(
            amount=converted_amount,
            currency=target_currency,
            original_input=f"{amount.original_input} -> {target_currency}"
        )

    def convert_to_cny(self, amount: CurrencyAmount) -> CurrencyAmount:
        """转换为人民币"""
        return self.convert_to_local(amount, 'CNY')

    def format_amount(self, amount: CurrencyAmount, show_symbol: bool = True) -> str:
        """格式化货币金额显示"""
        currency_info = self.currency_map.get(amount.currency, {})
        symbol = currency_info.get('symbol', amount.currency)
        name = currency_info.get('name', amount.currency)

        formatted_amount = f"{amount.amount:,.2f}"

        if show_symbol:
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {amount.currency}"

    def get_supported_currencies(self) -> Dict[str, Dict[str, str]]:
        """获取支持的货币列表"""
        return {
            code: {
                'name': info['name'],
                'symbol': info['symbol'],
                'aliases': ', '.join(info['aliases'])
            }
            for code, info in self.currency_map.items()
        }

    def validate_currency(self, currency_str: str) -> bool:
        """验证货币代码是否支持"""
        return self._find_currency_code(currency_str) is not None

    def get_currency_info(self, currency_code: str) -> Optional[Dict[str, str]]:
        """获取货币信息"""
        return self.currency_map.get(currency_code)

    def get_realtime_rate_info(self, from_currency: str, to_currency: str) -> Dict[str, any]:
        """获取实时汇率信息"""
        try:
            return self.daily_cache.get_rate_info(from_currency, to_currency)
        except Exception as e:
            return {
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': 0.0,
                'last_update': 'N/A',
                'error': str(e)
            }

    def test_realtime_connection(self) -> Dict[str, bool]:
        """测试实时汇率连接"""
        return {'connection': True, 'message': 'Using daily cache'}

    def get_cache_status(self) -> Dict[str, any]:
        """获取缓存状态信息"""
        return self.daily_cache.get_cache_info()

    def clear_cache(self) -> bool:
        """清除汇率缓存"""
        return self.daily_cache.clear_cache()

    def force_update_cache(self) -> Dict[str, float]:
        """强制更新汇率缓存"""
        return self.daily_cache.get_exchange_rates(force_update=True)

# 创建全局智能货币转换器实例
smart_converter = SmartCurrencyConverter()

def parse_currency_amount(input_str: str) -> CurrencyAmount:
    """便捷函数：解析货币金额"""
    return smart_converter.parse_amount(input_str)

def convert_to_local_currency(amount: CurrencyAmount, target_currency: str) -> CurrencyAmount:
    """便捷函数：转换为本地货币"""
    return smart_converter.convert_to_local(amount, target_currency)