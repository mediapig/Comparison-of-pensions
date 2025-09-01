import requests
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import time

class CurrencyConverter:
    """汇率转换器"""

    def __init__(self, base_currency: str = "CNY"):
        self.base_currency = base_currency.upper()
        self.exchange_rates = {}
        self.last_update = None
        self.update_interval = timedelta(hours=1)  # 1小时更新一次

        # 支持的货币列表
        self.supported_currencies = {
            'CNY': '人民币',
            'USD': '美元',
            'EUR': '欧元',
            'GBP': '英镑',
            'JPY': '日元',
            'HKD': '港币',
            'SGD': '新币',
            'AUD': '澳币',
            'CAD': '加币',
            'TWD': '新台币'
        }

    def get_exchange_rates(self, force_update: bool = False) -> Dict[str, float]:
        """获取汇率数据"""
        current_time = datetime.now()

        # 检查是否需要更新汇率
        if (force_update or
            self.last_update is None or
            current_time - self.last_update > self.update_interval):

            try:
                self._update_exchange_rates()
            except Exception as e:
                print(f"汇率更新失败: {e}")
                # 如果更新失败，使用默认汇率
                if not self.exchange_rates:
                    self._set_default_rates()

        return self.exchange_rates

    def _update_exchange_rates(self):
        """更新汇率数据"""
        try:
            # 方案1: 使用ExchangeRate-API (免费)
            url = f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})

                # 转换为以基准货币为1的汇率
                self.exchange_rates = {}
                for currency, rate in rates.items():
                    if currency in self.supported_currencies:
                        self.exchange_rates[currency] = rate

                self.last_update = datetime.now()
                print(f"汇率更新成功: {self.last_update}")
                return

        except Exception as e:
            print(f"ExchangeRate-API 失败: {e}")

        try:
            # 方案2: 使用Fixer.io (需要API key，这里用免费版)
            # 注意：实际使用时需要注册获取免费API key
            url = f"http://data.fixer.io/api/latest?base={self.base_currency}&symbols={','.join(self.supported_currencies.keys())}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    rates = data.get('rates', {})
                    self.exchange_rates = rates
                    self.last_update = datetime.now()
                    print(f"汇率更新成功 (Fixer): {self.last_update}")
                    return

        except Exception as e:
            print(f"Fixer.io 失败: {e}")

        # 如果所有API都失败，使用默认汇率
        self._set_default_rates()

    def _set_default_rates(self):
        """设置默认汇率（基于2024年大致汇率）"""
        if self.base_currency == "CNY":
            self.exchange_rates = {
                'CNY': 1.0,
                'USD': 0.14,      # 1 CNY = 0.14 USD
                'EUR': 0.13,      # 1 CNY = 0.13 EUR
                'GBP': 0.11,      # 1 CNY = 0.11 GBP
                'JPY': 20.5,      # 1 CNY = 20.5 JPY
                'HKD': 1.09,      # 1 CNY = 1.09 HKD
                'SGD': 0.19,      # 1 CNY = 0.19 SGD
                'AUD': 0.21,      # 1 CNY = 0.21 AUD
                'CAD': 0.19,      # 1 CNY = 0.19 CAD
                'TWD': 4.35       # 1 CNY = 4.35 TWD
            }
        elif self.base_currency == "USD":
            self.exchange_rates = {
                'CNY': 7.15,      # 1 USD = 7.15 CNY
                'USD': 1.0,
                'EUR': 0.93,      # 1 USD = 0.93 EUR
                'GBP': 0.79,      # 1 USD = 0.79 GBP
                'JPY': 146.5,     # 1 USD = 146.5 JPY
                'HKD': 7.8,       # 1 USD = 7.8 HKD
                'SGD': 1.35,      # 1 USD = 1.35 SGD
                'AUD': 1.52,      # 1 USD = 1.52 AUD
                'CAD': 1.36,      # 1 USD = 1.36 CAD
                'TWD': 31.1       # 1 USD = 31.1 TWD
            }

        self.last_update = datetime.now()
        print(f"使用默认汇率: {self.last_update}")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """转换货币"""
        if from_currency == to_currency:
            return amount

        rates = self.get_exchange_rates()

        if from_currency not in rates or to_currency not in rates:
            raise ValueError(f"不支持的货币: {from_currency} 或 {to_currency}")

        # 转换公式: amount * (to_rate / from_rate)
        from_rate = rates[from_currency]
        to_rate = rates[to_currency]

        converted_amount = amount * (to_rate / from_rate)
        return converted_amount

    def convert_to_base(self, amount: float, currency: str) -> float:
        """转换为基准货币"""
        return self.convert(amount, currency, self.base_currency)

    def convert_from_base(self, amount: float, currency: str) -> float:
        """从基准货币转换"""
        return self.convert(amount, self.base_currency, currency)

    def get_currency_name(self, currency_code: str) -> str:
        """获取货币名称"""
        return self.supported_currencies.get(currency_code, currency_code)

    def format_amount(self, amount: float, currency: str, decimal_places: int = 2) -> str:
        """格式化货币金额"""
        currency_name = self.get_currency_name(currency)
        formatted_amount = f"{amount:,.{decimal_places}f}"

        if currency == "CNY":
            return f"¥{formatted_amount}"
        elif currency == "USD":
            return f"${formatted_amount}"
        elif currency == "EUR":
            return f"€{formatted_amount}"
        elif currency == "GBP":
            return f"£{formatted_amount}"
        elif currency == "JPY":
            return f"¥{formatted_amount}"
        elif currency == "HKD":
            return f"HK${formatted_amount}"
        elif currency == "SGD":
            return f"S${formatted_amount}"
        elif currency == "AUD":
            return f"A${formatted_amount}"
        elif currency == "CAD":
            return f"C${formatted_amount}"
        elif currency == "TWD":
            return f"NT${formatted_amount}"
        else:
            return f"{currency} {formatted_amount}"

# 创建全局汇率转换器实例
converter = CurrencyConverter("CNY")  # 默认使用人民币作为基准
