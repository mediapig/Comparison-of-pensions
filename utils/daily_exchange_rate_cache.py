#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日汇率缓存系统
实现每日缓存检查，避免重复请求，提高系统速度
"""

import json
import os
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta, date
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DailyExchangeRateCache:
    """每日汇率缓存管理器 - 固定JSON文件存储"""
    
    def __init__(self, cache_dir: str = "cache", base_currency: str = "CNY"):
        self.base_currency = base_currency.upper()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 固定缓存文件路径 - 统一使用 exchange_rates.json
        self.cache_file = self.cache_dir / "exchange_rates.json"
        
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
            }
        ]
        
        # 默认汇率（当API失败时使用）
        self.default_rates = {
            'CNY': 1.0, 'USD': 0.14, 'EUR': 0.13, 'GBP': 0.11,
            'JPY': 20.0, 'HKD': 1.1, 'SGD': 0.19, 'AUD': 0.21,
            'CAD': 0.19, 'TWD': 4.3, 'NOK': 1.5, 'SEK': 1.4,
            'DKK': 1.0, 'CHF': 0.12, 'INR': 11.5, 'KRW': 180.0,
            'RUB': 12.5, 'BRL': 0.7
        }
    
    def get_exchange_rates(self, force_update: bool = False) -> Dict[str, float]:
        """
        获取汇率数据
        优先使用当日缓存，如果没有则请求API并缓存
        
        Args:
            force_update: 是否强制更新（忽略缓存）
            
        Returns:
            汇率字典
        """
        today = date.today()
        
        # 检查是否需要更新
        if force_update or not self._has_valid_cache(today):
            logger.info(f"🔄 更新汇率数据 (强制更新: {force_update})")
            success = self._fetch_and_cache_rates(today)
            
            if not success:
                logger.warning("⚠️ API请求失败，使用默认汇率")
                return self.default_rates.copy()
        
        # 从缓存读取
        cached_rates = self._load_from_cache()
        if cached_rates:
            logger.info(f"✅ 使用缓存汇率数据 ({cached_rates.get('date', 'unknown')})")
            return cached_rates.get('rates', self.default_rates.copy())
        
        # 如果缓存也失败，使用默认汇率
        logger.warning("⚠️ 缓存读取失败，使用默认汇率")
        return self.default_rates.copy()
    
    def _has_valid_cache(self, target_date: date) -> bool:
        """检查是否有有效的当日缓存 - 严格按照一天有效期"""
        if not self.cache_file.exists():
            logger.info("📁 缓存文件不存在")
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cache_date_str = cache_data.get('date')
            if not cache_date_str:
                logger.warning("⚠️ 缓存文件缺少日期信息")
                return False
            
            cache_date = datetime.strptime(cache_date_str, '%Y-%m-%d').date()
            is_valid = cache_date == target_date
            
            if is_valid:
                logger.info(f"✅ 找到有效的当日缓存: {cache_date_str}")
            else:
                logger.info(f"📅 缓存已过期: {cache_date_str} (需要: {target_date})")
            
            return is_valid
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"❌ 缓存文件损坏: {e}")
            return False
    
    def _fetch_and_cache_rates(self, target_date: date) -> bool:
        """从API获取汇率并缓存"""
        successful_apis = []
        failed_apis = []
        
        # 按优先级排序API配置
        sorted_apis = sorted(self.api_configs, key=lambda x: x['priority'])
        
        for api_config in sorted_apis:
            try:
                logger.info(f"🌐 尝试从 {api_config['name']} 获取汇率...")
                
                # 跳过需要API Key的免费API（如果没有配置）
                if not api_config.get('free', True) and 'YOUR_API_KEY' in api_config['url']:
                    logger.info(f"⏭️ 跳过 {api_config['name']} (需要API Key)")
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
                        # 缓存数据 - 固定JSON格式
                        cache_data = {
                            'date': target_date.strftime('%Y-%m-%d'),
                            'timestamp': datetime.now().isoformat(),
                            'api_source': api_config['name'],
                            'base_currency': self.base_currency,
                            'rates': rates,
                            'cache_version': '1.0',
                            'expires_at': (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
                        }
                        
                        self._save_to_cache(cache_data)
                        successful_apis.append(api_config['name'])
                        logger.info(f"✅ {api_config['name']} 汇率获取成功并已缓存到 {self.cache_file}")
                        logger.info(f"📊 获取到 {len(rates)} 种货币汇率")
                        logger.info(f"📅 缓存有效期至: {cache_data['expires_at']}")
                        return True
                    else:
                        logger.warning(f"⚠️ {api_config['name']} 返回数据无效")
                        failed_apis.append(f"{api_config['name']}: 数据无效")
                        
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ {api_config['name']} 请求超时")
                failed_apis.append(f"{api_config['name']}: 超时")
            except requests.exceptions.RequestException as e:
                logger.warning(f"❌ {api_config['name']} 请求失败: {e}")
                failed_apis.append(f"{api_config['name']}: {str(e)}")
            except Exception as e:
                logger.error(f"💥 {api_config['name']} 解析失败: {e}")
                failed_apis.append(f"{api_config['name']}: 解析错误")
        
        logger.error(f"❌ 所有API都失败了: {failed_apis}")
        return False
    
    def _save_to_cache(self, cache_data: Dict) -> None:
        """保存数据到固定JSON缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 汇率数据已保存到固定缓存文件: {self.cache_file}")
            logger.debug(f"📄 缓存文件大小: {self.cache_file.stat().st_size} bytes")
        except Exception as e:
            logger.error(f"❌ 缓存保存失败: {e}")
    
    def _load_from_cache(self) -> Optional[Dict]:
        """从缓存文件加载数据"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ 缓存读取失败: {e}")
            return None
    
    def get_cache_info(self) -> Dict[str, any]:
        """获取缓存信息 - 显示固定JSON文件状态"""
        if not self.cache_file.exists():
            return {
                'exists': False,
                'file_path': str(self.cache_file),
                'message': '固定缓存文件不存在',
                'cache_type': 'daily_json'
            }
        
        try:
            cache_data = self._load_from_cache()
            if cache_data:
                return {
                    'exists': True,
                    'file_path': str(self.cache_file),
                    'date': cache_data.get('date'),
                    'timestamp': cache_data.get('timestamp'),
                    'api_source': cache_data.get('api_source'),
                    'base_currency': cache_data.get('base_currency'),
                    'currencies_count': len(cache_data.get('rates', {})),
                    'file_size': self.cache_file.stat().st_size,
                    'cache_version': cache_data.get('cache_version', 'unknown'),
                    'expires_at': cache_data.get('expires_at'),
                    'cache_type': 'daily_json',
                    'is_valid_today': self._has_valid_cache(date.today())
                }
        except Exception as e:
            return {
                'exists': True,
                'file_path': str(self.cache_file),
                'error': str(e),
                'message': '固定缓存文件损坏',
                'cache_type': 'daily_json'
            }
    
    def clear_cache(self) -> bool:
        """清除缓存"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info(f"🗑️ 缓存已清除: {self.cache_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 缓存清除失败: {e}")
            return False
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """货币转换"""
        if from_currency == to_currency:
            return amount
        
        rates = self.get_exchange_rates()
        
        # 确保货币在汇率表中
        if from_currency not in rates or to_currency not in rates:
            logger.warning(f"⚠️ 货币 {from_currency} 或 {to_currency} 不在汇率表中")
            return amount
        
        # 转换逻辑：amount * (to_rate / from_rate)
        from_rate = rates[from_currency]
        to_rate = rates[to_currency]
        
        return amount * (to_rate / from_rate)
    
    def get_rate_info(self, from_currency: str, to_currency: str) -> Dict[str, any]:
        """获取汇率信息"""
        rates = self.get_exchange_rates()
        cache_info = self.get_cache_info()
        
        exchange_rate = 1.0
        if from_currency != to_currency and from_currency in rates and to_currency in rates:
            exchange_rate = rates[to_currency] / rates[from_currency]
        
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': exchange_rate,
            'last_update': cache_info.get('timestamp', 'N/A'),
            'cache_date': cache_info.get('date', 'N/A'),
            'api_source': cache_info.get('api_source', 'N/A'),
            'cache_exists': cache_info.get('exists', False)
        }
    
    # API解析器方法
    def _parse_exchangerate_api(self, data: Dict) -> Dict[str, float]:
        """解析ExchangeRate-API响应"""
        rates = data.get('rates', {})
        return {k: v for k, v in rates.items() if k in self.supported_currencies}
    
    def _parse_exchangeratesapi(self, data: Dict) -> Dict[str, float]:
        """解析ExchangeRatesAPI响应"""
        rates = data.get('rates', {})
        return {k: v for k, v in rates.items() if k in self.supported_currencies}
    
    def _parse_currency_api(self, data: Dict) -> Dict[str, float]:
        """解析CurrencyAPI响应"""
        rates = data.get('data', {})
        result = {}
        for currency, info in rates.items():
            if currency in self.supported_currencies:
                result[currency] = info.get('value', 0)
        return result
    
    def _parse_fixer_api(self, data: Dict) -> Dict[str, float]:
        """解析Fixer.io响应"""
        rates = data.get('rates', {})
        return {k: v for k, v in rates.items() if k in self.supported_currencies}


# 创建全局每日汇率缓存实例
daily_cache = DailyExchangeRateCache()

def get_daily_exchange_rates(force_update: bool = False) -> Dict[str, float]:
    """便捷函数：获取每日汇率"""
    return daily_cache.get_exchange_rates(force_update)

def convert_with_daily_cache(amount: float, from_currency: str, to_currency: str) -> float:
    """便捷函数：使用每日缓存进行货币转换"""
    return daily_cache.convert(amount, from_currency, to_currency)

def get_cache_status() -> Dict[str, any]:
    """便捷函数：获取缓存状态"""
    return daily_cache.get_cache_info()

def clear_exchange_rate_cache() -> bool:
    """便捷函数：清除汇率缓存"""
    return daily_cache.clear_cache()


if __name__ == "__main__":
    # 测试每日汇率缓存
    print("=" * 60)
    print("🧪 每日汇率缓存系统测试")
    print("=" * 60)
    
    # 创建缓存实例
    cache = DailyExchangeRateCache()
    
    # 显示缓存状态
    print("\n📊 缓存状态:")
    cache_info = cache.get_cache_info()
    for key, value in cache_info.items():
        print(f"  {key}: {value}")
    
    # 获取汇率
    print("\n🌐 获取汇率数据:")
    rates = cache.get_exchange_rates()
    print(f"  获取到 {len(rates)} 种货币汇率")
    for currency, rate in list(rates.items())[:5]:  # 显示前5个
        print(f"  {currency}: {rate:.4f}")
    
    # 测试转换
    print("\n💱 货币转换测试:")
    test_cases = [
        (100, 'CNY', 'USD'),
        (100, 'USD', 'CNY'),
        (100, 'EUR', 'GBP'),
        (100, 'JPY', 'CNY')
    ]
    
    for amount, from_curr, to_curr in test_cases:
        converted = cache.convert(amount, from_curr, to_curr)
        print(f"  {amount} {from_curr} = {converted:.2f} {to_curr}")
    
    # 显示汇率信息
    print("\n📈 汇率信息:")
    rate_info = cache.get_rate_info('CNY', 'USD')
    for key, value in rate_info.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 测试完成！")