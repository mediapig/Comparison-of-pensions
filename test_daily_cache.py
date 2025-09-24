#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试每日汇率缓存系统
验证固定JSON文件缓存机制
"""

import os
import json
from datetime import date, datetime
from utils.daily_exchange_rate_cache import DailyExchangeRateCache
from utils.smart_currency_converter import SmartCurrencyConverter

def test_daily_cache_system():
    """测试每日缓存系统"""
    print("=" * 80)
    print("🧪 每日汇率缓存系统测试")
    print("=" * 80)
    
    # 创建缓存实例
    cache = DailyExchangeRateCache()
    
    print(f"\n📁 缓存文件路径: {cache.cache_file}")
    print(f"📅 今天日期: {date.today()}")
    
    # 1. 检查初始缓存状态
    print("\n" + "="*50)
    print("1️⃣ 检查初始缓存状态")
    print("="*50)
    
    cache_info = cache.get_cache_info()
    print("📊 缓存信息:")
    for key, value in cache_info.items():
        print(f"  {key}: {value}")
    
    # 2. 获取汇率（会触发API请求或使用缓存）
    print("\n" + "="*50)
    print("2️⃣ 获取汇率数据")
    print("="*50)
    
    print("🌐 正在获取汇率数据...")
    rates = cache.get_exchange_rates()
    print(f"✅ 获取到 {len(rates)} 种货币汇率")
    
    # 显示部分汇率
    print("\n💱 部分汇率数据:")
    for currency, rate in list(rates.items())[:8]:
        print(f"  {currency}: {rate:.4f}")
    
    # 3. 再次检查缓存状态
    print("\n" + "="*50)
    print("3️⃣ 再次检查缓存状态")
    print("="*50)
    
    cache_info = cache.get_cache_info()
    print("📊 更新后的缓存信息:")
    for key, value in cache_info.items():
        print(f"  {key}: {value}")
    
    # 4. 测试缓存文件内容
    print("\n" + "="*50)
    print("4️⃣ 检查缓存文件内容")
    print("="*50)
    
    if cache.cache_file.exists():
        try:
            with open(cache.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print("📄 缓存文件结构:")
            print(f"  日期: {cache_data.get('date')}")
            print(f"  时间戳: {cache_data.get('timestamp')}")
            print(f"  API来源: {cache_data.get('api_source')}")
            print(f"  基准货币: {cache_data.get('base_currency')}")
            print(f"  缓存版本: {cache_data.get('cache_version')}")
            print(f"  过期时间: {cache_data.get('expires_at')}")
            print(f"  货币数量: {len(cache_data.get('rates', {}))}")
            
            # 显示汇率数据样本
            rates_data = cache_data.get('rates', {})
            print(f"\n💱 汇率数据样本:")
            for currency, rate in list(rates_data.items())[:5]:
                print(f"  {currency}: {rate}")
                
        except Exception as e:
            print(f"❌ 读取缓存文件失败: {e}")
    else:
        print("❌ 缓存文件不存在")
    
    # 5. 测试货币转换
    print("\n" + "="*50)
    print("5️⃣ 测试货币转换")
    print("="*50)
    
    test_cases = [
        (100, 'CNY', 'USD'),
        (100, 'USD', 'CNY'),
        (100, 'EUR', 'GBP'),
        (100, 'JPY', 'CNY'),
        (1000, 'CNY', 'SGD')
    ]
    
    for amount, from_curr, to_curr in test_cases:
        converted = cache.convert(amount, from_curr, to_curr)
        print(f"  {amount} {from_curr} = {converted:.2f} {to_curr}")
    
    # 6. 测试智能转换器
    print("\n" + "="*50)
    print("6️⃣ 测试智能转换器")
    print("="*50)
    
    smart_converter = SmartCurrencyConverter()
    
    # 测试解析
    test_inputs = ['cny10000', 'USD5000', '10000EUR', '$1000', '5000']
    
    for input_str in test_inputs:
        try:
            amount = smart_converter.parse_amount(input_str)
            print(f"  解析 '{input_str}' -> {amount}")
        except Exception as e:
            print(f"  解析 '{input_str}' 失败: {e}")
    
    # 测试转换
    print("\n💱 智能转换测试:")
    test_amounts = [
        smart_converter.parse_amount('cny10000'),
        smart_converter.parse_amount('USD1000'),
        smart_converter.parse_amount('EUR500')
    ]
    
    for amount in test_amounts:
        converted = smart_converter.convert_to_local(amount, 'CNY')
        print(f"  {amount} -> {converted}")
    
    # 7. 测试缓存有效性
    print("\n" + "="*50)
    print("7️⃣ 测试缓存有效性")
    print("="*50)
    
    # 测试当日缓存有效性
    is_valid = cache._has_valid_cache(date.today())
    print(f"📅 当日缓存有效性: {'✅ 有效' if is_valid else '❌ 无效'}")
    
    # 测试强制更新
    print("\n🔄 测试强制更新:")
    print("  正在强制更新汇率...")
    updated_rates = cache.get_exchange_rates(force_update=True)
    print(f"  ✅ 强制更新完成，获取到 {len(updated_rates)} 种货币汇率")
    
    # 8. 显示最终状态
    print("\n" + "="*50)
    print("8️⃣ 最终状态")
    print("="*50)
    
    final_cache_info = cache.get_cache_info()
    print("📊 最终缓存状态:")
    for key, value in final_cache_info.items():
        print(f"  {key}: {value}")
    
    print(f"\n📁 缓存文件位置: {cache.cache_file}")
    if cache.cache_file.exists():
        file_size = cache.cache_file.stat().st_size
        print(f"📄 文件大小: {file_size} bytes")
    
    print("\n✅ 每日汇率缓存系统测试完成！")
    print("=" * 80)

def show_cache_file_structure():
    """显示缓存文件结构示例"""
    print("\n" + "="*60)
    print("📋 缓存文件结构示例")
    print("="*60)
    
    example_structure = {
        "date": "2024-12-19",
        "timestamp": "2024-12-19T10:30:00.123456",
        "api_source": "ExchangeRate-API",
        "base_currency": "CNY",
        "cache_version": "1.0",
        "expires_at": "2024-12-20",
        "rates": {
            "CNY": 1.0,
            "USD": 0.1405,
            "EUR": 0.1289,
            "GBP": 0.1102,
            "JPY": 20.45,
            "HKD": 1.0987,
            "SGD": 0.1892,
            "AUD": 0.2103,
            "CAD": 0.1915,
            "TWD": 4.32,
            "NOK": 1.52,
            "SEK": 1.41,
            "DKK": 0.96,
            "CHF": 0.1215,
            "INR": 11.67,
            "KRW": 182.34,
            "RUB": 12.89,
            "BRL": 0.72
        }
    }
    
    print("📄 缓存文件 (exchange_rates.json) 结构:")
    print(json.dumps(example_structure, indent=2, ensure_ascii=False))
    
    print("\n📝 字段说明:")
    print("  date: 缓存日期 (YYYY-MM-DD)")
    print("  timestamp: 缓存时间戳")
    print("  api_source: 数据来源API")
    print("  base_currency: 基准货币")
    print("  cache_version: 缓存版本")
    print("  expires_at: 过期日期")
    print("  rates: 汇率数据字典")

if __name__ == "__main__":
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # 运行测试
    test_daily_cache_system()
    
    # 显示缓存文件结构
    show_cache_file_structure()