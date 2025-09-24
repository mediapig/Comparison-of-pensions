#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时汇率转换工具
使用在线API获取实时汇率数据
"""

import requests
import json
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from .daily_exchange_rate_cache import DailyExchangeRateCache

logger = logging.getLogger(__name__)

class RealtimeCurrencyConverter:
    """实时汇率转换器"""
    
    def __init__(self, base_currency: str = "CNY"):
        self.base_currency = base_currency.upper()
        self.exchange_rates = {}
        self.last_update = None
        self.update_interval = timedelta(minutes=5)  # 5分钟更新一次
        self.cache_duration = timedelta(hours=1)     # 缓存1小时
        
        # 使用每日缓存系统
        self.daily_cache = DailyExchangeRateCache(base_currency=base_currency)
        
        # 支持的货币列表
        self.supported_currencies = {
            'CNY': '人民币', 'USD': '美元', 'EUR': '欧元', 'GBP': '英镑',
            'JPY': '日元', 'HKD': '港币', 'SGD': '新加坡元', 'AUD': '澳大利亚元',
            'CAD': '加拿大元', 'TWD': '新台币', 'NOK': '挪威克朗', 'SEK': '瑞典克朗',
            'DKK': '丹麦克朗', 'CHF': '瑞士法郎', 'INR': '印度卢比', 'KRW': '韩元',
            'RUB': '俄罗斯卢布', 'BRL': '巴西雷亚尔'
        }
        
        # API配置 - 多个汇率接口（按优先级排序）
        self.api_configs = [
            {
                'name': 'ExchangeRate-API',
                'url': f'https://api.exchangerate-api.com/v4/latest/{self.base_currency}',
                'parser': self._parse_exchangerate_api,
                'timeout': 10,
                'priority': 1,
                'free': True
            },
            {
                'name': 'ExchangeRatesAPI',
                'url': f'https://api.exchangeratesapi.io/v1/latest?base={self.base_currency}&symbols={",".join(self.supported_currencies.keys())}',
                'parser': self._parse_exchangeratesapi,
                'timeout': 10,
                'priority': 2,
                'free': True
            },
            {
                'name': 'CurrencyAPI',
                'url': f'https://api.currencyapi.com/v3/latest?apikey=YOUR_API_KEY&base_currency={self.base_currency}',
                'parser': self._parse_currency_api,
                'timeout': 10,
                'priority': 3,
                'free': False
            },
            {
                'name': 'Fixer.io',
                'url': f'https://api.fixer.io/latest?base={self.base_currency}&symbols={",".join(self.supported_currencies.keys())}',
                'parser': self._parse_fixer_api,
                'timeout': 10,
                'priority': 4,
                'free': False
            },
            {
                'name': 'CurrencyLayer',
                'url': f'http://api.currencylayer.com/live?access_key=YOUR_ACCESS_KEY&currencies={",".join(self.supported_currencies.keys())}&source={self.base_currency}',
                'parser': self._parse_currencylayer_api,
                'timeout': 10,
                'priority': 5,
                'free': False
            },
            {
                'name': 'Alpha Vantage',
                'url': f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={self.base_currency}&to_currency=USD&apikey=YOUR_API_KEY',
                'parser': self._parse_alphavantage_api,
                'timeout': 10,
                'priority': 6,
                'free': False
            }
        ]

    def get_exchange_rates(self, force_update: bool = False) -> Dict[str, float]:
        """获取汇率数据"""
        current_time = datetime.now()
        
        # 检查是否需要更新
        if (force_update or 
            self.last_update is None or 
            current_time - self.last_update > self.update_interval):
            
            try:
                self._update_exchange_rates()
            except Exception as e:
                logger.error(f"汇率更新失败: {e}")
                # 如果更新失败，使用默认汇率
                if not self.exchange_rates:
                    self._set_default_rates()
        
        return self.exchange_rates

    def _update_exchange_rates(self):
        """更新汇率数据 - 多API回退机制"""
        successful_apis = []
        failed_apis = []
        
        # 按优先级排序API配置
        sorted_apis = sorted(self.api_configs, key=lambda x: x['priority'])
        
        for api_config in sorted_apis:
            try:
                logger.info(f"尝试从 {api_config['name']} 获取汇率...")
                
                # 跳过需要API Key的免费API（如果没有配置）
                if not api_config.get('free', True) and 'YOUR_API_KEY' in api_config['url']:
                    logger.info(f"跳过 {api_config['name']} (需要API Key)")
                    continue
                
                response = requests.get(
                    api_config['url'], 
                    timeout=api_config['timeout'],
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rates = api_config['parser'](data)
                    
                    if rates and len(rates) > 1:  # 确保获取到多个货币的汇率
                        self.exchange_rates = rates
                        self.last_update = datetime.now()
                        successful_apis.append(api_config['name'])
                        logger.info(f"✅ {api_config['name']} 汇率更新成功: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info(f"获取到 {len(rates)} 种货币汇率")
                        return
                    else:
                        logger.warning(f"⚠️ {api_config['name']} 返回数据无效")
                        failed_apis.append(f"{api_config['name']}: 数据无效")
                        
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ {api_config['name']} 请求超时")
                failed_apis.append(f"{api_config['name']}: 超时")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 {api_config['name']} 连接失败")
                failed_apis.append(f"{api_config['name']}: 连接失败")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"🌐 {api_config['name']} HTTP错误: {e}")
                failed_apis.append(f"{api_config['name']}: HTTP {e.response.status_code}")
            except Exception as e:
                logger.warning(f"❌ {api_config['name']} API 失败: {e}")
                failed_apis.append(f"{api_config['name']}: {str(e)}")
        
        # 记录所有API的状态
        if successful_apis:
            logger.info(f"成功的API: {', '.join(successful_apis)}")
        if failed_apis:
            logger.warning(f"失败的API: {', '.join(failed_apis)}")
        
        # 如果所有API都失败，使用默认汇率
        logger.warning("所有汇率API都失败，使用默认汇率")
        self._set_default_rates()

    def _parse_exchangerate_api(self, data: dict) -> Optional[Dict[str, float]]:
        """解析ExchangeRate-API响应"""
        try:
            rates = data.get('rates', {})
            filtered_rates = {}
            
            for currency, rate in rates.items():
                if currency in self.supported_currencies:
                    filtered_rates[currency] = round(float(rate), 2)
            
            # 添加基准货币
            filtered_rates[self.base_currency] = 1.0
            
            return filtered_rates
        except Exception as e:
            logger.error(f"解析ExchangeRate-API响应失败: {e}")
            return None

    def _parse_fixer_api(self, data: dict) -> Optional[Dict[str, float]]:
        """解析Fixer.io API响应"""
        try:
            if not data.get('success', False):
                return None
                
            rates = data.get('rates', {})
            filtered_rates = {}
            
            for currency, rate in rates.items():
                if currency in self.supported_currencies:
                    filtered_rates[currency] = round(float(rate), 2)
            
            # 添加基准货币
            filtered_rates[self.base_currency] = 1.0
            
            return filtered_rates
        except Exception as e:
            logger.error(f"解析Fixer.io API响应失败: {e}")
            return None

    def _parse_currency_api(self, data: dict) -> Optional[Dict[str, float]]:
        """解析CurrencyAPI响应"""
        try:
            rates = data.get('data', {})
            filtered_rates = {}
            
            for currency, info in rates.items():
                if currency in self.supported_currencies:
                    rate = info.get('value', 0)
                    filtered_rates[currency] = round(float(rate), 2)
            
            # 添加基准货币
            filtered_rates[self.base_currency] = 1.0
            
            return filtered_rates
        except Exception as e:
            logger.error(f"解析CurrencyAPI响应失败: {e}")
            return None

    def _parse_currencylayer_api(self, data: dict) -> Optional[Dict[str, float]]:
        """解析CurrencyLayer API响应"""
        try:
            if not data.get('success', False):
                return None
                
            quotes = data.get('quotes', {})
            filtered_rates = {}
            
            for quote_key, rate in quotes.items():
                # CurrencyLayer格式: CNYUSD, CNYEUR等
                if quote_key.startswith(self.base_currency):
                    currency = quote_key[len(self.base_currency):]
                    if currency in self.supported_currencies:
                        filtered_rates[currency] = round(float(rate), 2)
            
            # 添加基准货币
            filtered_rates[self.base_currency] = 1.0
            
            return filtered_rates
        except Exception as e:
            logger.error(f"解析CurrencyLayer API响应失败: {e}")
            return None

    def _parse_exchangeratesapi(self, data: dict) -> Optional[Dict[str, float]]:
        """解析ExchangeRatesAPI响应"""
        try:
            rates = data.get('rates', {})
            filtered_rates = {}
            
            for currency, rate in rates.items():
                if currency in self.supported_currencies:
                    filtered_rates[currency] = round(float(rate), 2)
            
            # 添加基准货币
            filtered_rates[self.base_currency] = 1.0
            
            return filtered_rates
        except Exception as e:
            logger.error(f"解析ExchangeRatesAPI响应失败: {e}")
            return None

    def _parse_alphavantage_api(self, data: dict) -> Optional[Dict[str, float]]:
        """解析Alpha Vantage API响应"""
        try:
            # Alpha Vantage只提供单一货币对，需要多次调用
            # 这里只作为示例，实际需要循环调用获取所有货币
            exchange_rate = data.get('Realtime Currency Exchange Rate', {})
            if not exchange_rate:
                return None
                
            from_currency = exchange_rate.get('1. From_Currency Code', '')
            to_currency = exchange_rate.get('3. To_Currency Code', '')
            rate = exchange_rate.get('5. Exchange Rate', '0')
            
            if from_currency == self.base_currency and to_currency in self.supported_currencies:
                return {
                    self.base_currency: 1.0,
                    to_currency: round(float(rate), 2)
                }
            
            return None
        except Exception as e:
            logger.error(f"解析Alpha Vantage API响应失败: {e}")
            return None

    def _set_default_rates(self):
        """设置默认汇率（基于2024年大致汇率）"""
        if self.base_currency == "CNY":
            self.exchange_rates = {
                'CNY': 1.0,      # 人民币
                'USD': 0.14,     # 美元
                'EUR': 0.13,      # 欧元
                'GBP': 0.11,      # 英镑
                'JPY': 20.5,      # 日元
                'HKD': 1.09,      # 港币
                'SGD': 0.19,      # 新加坡元
                'AUD': 0.21,      # 澳大利亚元
                'CAD': 0.19,      # 加拿大元
                'TWD': 4.35,      # 新台币
                'NOK': 1.54,      # 挪威克朗
                'SEK': 1.45,      # 瑞典克朗
                'DKK': 0.97,      # 丹麦克朗
                'CHF': 0.12,      # 瑞士法郎
                'INR': 11.6,      # 印度卢比
                'KRW': 185.0,     # 韩元
                'RUB': 12.8,      # 俄罗斯卢布
                'BRL': 0.69,      # 巴西雷亚尔
            }
        elif self.base_currency == "USD":
            self.exchange_rates = {
                'CNY': 7.15,      # 人民币
                'USD': 1.0,       # 美元
                'EUR': 0.93,       # 欧元
                'GBP': 0.79,      # 英镑
                'JPY': 146.5,     # 日元
                'HKD': 7.8,       # 港币
                'SGD': 1.35,      # 新加坡元
                'AUD': 1.52,      # 澳大利亚元
                'CAD': 1.36,      # 加拿大元
                'TWD': 31.1,      # 新台币
                'NOK': 11.0,      # 挪威克朗
                'SEK': 10.4,      # 瑞典克朗
                'DKK': 6.9,       # 丹麦克朗
                'CHF': 0.88,      # 瑞士法郎
                'INR': 83.0,      # 印度卢比
                'KRW': 1320.0,    # 韩元
                'RUB': 91.5,      # 俄罗斯卢布
                'BRL': 4.95,      # 巴西雷亚尔
            }
        
        self.last_update = datetime.now()
        logger.info(f"使用默认汇率: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """转换货币"""
        if from_currency == to_currency:
            return round(amount, 2)
        
        rates = self.get_exchange_rates()
        
        if from_currency not in rates or to_currency not in rates:
            raise ValueError(f"不支持的货币: {from_currency} 或 {to_currency}")
        
        # 转换公式: amount * (to_rate / from_rate)
        from_rate = rates[from_currency]
        to_rate = rates[to_currency]
        
        converted_amount = amount * (to_rate / from_rate)
        return round(converted_amount, 2)

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
            return f"JP¥{formatted_amount}"
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
        elif currency == "NOK":
            return f"kr {formatted_amount}"
        elif currency == "SEK":
            return f"kr {formatted_amount}"
        elif currency == "DKK":
            return f"kr {formatted_amount}"
        elif currency == "CHF":
            return f"CHF {formatted_amount}"
        elif currency == "INR":
            return f"₹{formatted_amount}"
        elif currency == "KRW":
            return f"₩{formatted_amount}"
        elif currency == "RUB":
            return f"₽{formatted_amount}"
        elif currency == "BRL":
            return f"R${formatted_amount}"
        else:
            return f"{currency} {formatted_amount}"

    def get_rate_info(self, from_currency: str, to_currency: str) -> Dict[str, any]:
        """获取汇率信息"""
        rates = self.get_exchange_rates()
        
        if from_currency not in rates or to_currency not in rates:
            raise ValueError(f"不支持的货币: {from_currency} 或 {to_currency}")
        
        from_rate = rates[from_currency]
        to_rate = rates[to_currency]
        exchange_rate = to_rate / from_rate
        
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'from_rate': from_rate,
            'to_rate': to_rate,
            'exchange_rate': round(exchange_rate, 4),
            'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else 'N/A'
        }

    def test_api_connection(self) -> Dict[str, Dict[str, any]]:
        """测试API连接 - 详细状态"""
        results = {}
        
        for api_config in self.api_configs:
            api_name = api_config['name']
            api_info = {
                'available': False,
                'free': api_config.get('free', True),
                'priority': api_config['priority'],
                'status': 'unknown',
                'error': None,
                'response_time': 0
            }
            
            # 跳过需要API Key的免费API（如果没有配置）
            if not api_config.get('free', True) and 'YOUR_API_KEY' in api_config['url']:
                api_info['status'] = 'skipped'
                api_info['error'] = '需要API Key'
                results[api_name] = api_info
                continue
            
            try:
                import time
                start_time = time.time()
                
                response = requests.get(
                    api_config['url'], 
                    timeout=5,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                )
                
                response_time = round((time.time() - start_time) * 1000, 2)  # 毫秒
                api_info['response_time'] = response_time
                
                if response.status_code == 200:
                    # 测试数据解析
                    data = response.json()
                    rates = api_config['parser'](data)
                    
                    if rates and len(rates) > 1:
                        api_info['available'] = True
                        api_info['status'] = 'success'
                        api_info['currencies_count'] = len(rates)
                    else:
                        api_info['status'] = 'invalid_data'
                        api_info['error'] = '数据无效或为空'
                else:
                    api_info['status'] = 'http_error'
                    api_info['error'] = f'HTTP {response.status_code}'
                    
            except requests.exceptions.Timeout:
                api_info['status'] = 'timeout'
                api_info['error'] = '请求超时'
            except requests.exceptions.ConnectionError:
                api_info['status'] = 'connection_error'
                api_info['error'] = '连接失败'
            except Exception as e:
                api_info['status'] = 'error'
                api_info['error'] = str(e)
            
            results[api_name] = api_info
        
        return results

# 创建全局实时汇率转换器实例
realtime_converter = RealtimeCurrencyConverter("CNY")

def get_realtime_rate(from_currency: str, to_currency: str) -> float:
    """便捷函数：获取实时汇率"""
    return realtime_converter.convert(1.0, from_currency, to_currency)

def convert_realtime_amount(amount: float, from_currency: str, to_currency: str) -> float:
    """便捷函数：实时转换金额"""
    return realtime_converter.convert(amount, from_currency, to_currency)