#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Engine setup for pension comparison system
"""

from core.pension_engine import PensionEngine
from plugins.china.china_calculator import ChinaPensionCalculator
from plugins.usa.usa_calculator import USAPensionCalculator
from plugins.taiwan.taiwan_calculator import TaiwanPensionCalculator
from plugins.hongkong.hongkong_calculator import HongKongPensionCalculator
from plugins.singapore.singapore_calculator import SingaporePensionCalculator
from plugins.japan.japan_calculator import JapanPensionCalculator
from plugins.uk.uk_calculator import UKPensionCalculator
from plugins.australia.australia_calculator import AustraliaPensionCalculator
from plugins.canada.canada_calculator import CanadaPensionCalculator

def create_pension_engine() -> PensionEngine:
    """创建并配置退休金计算引擎"""
    engine = PensionEngine()
    
    # 注册各国计算器
    engine.register_calculator(ChinaPensionCalculator())
    engine.register_calculator(USAPensionCalculator())
    engine.register_calculator(TaiwanPensionCalculator())
    engine.register_calculator(HongKongPensionCalculator())
    engine.register_calculator(SingaporePensionCalculator())
    engine.register_calculator(JapanPensionCalculator())
    engine.register_calculator(UKPensionCalculator())
    engine.register_calculator(AustraliaPensionCalculator())
    engine.register_calculator(CanadaPensionCalculator())
    
    return engine