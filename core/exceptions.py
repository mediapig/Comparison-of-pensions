#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目异常定义
统一管理所有自定义异常
"""

from typing import Optional, Dict, Any


class PensionSystemError(Exception):
    """退休金系统基础异常类"""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class PluginError(PensionSystemError):
    """插件相关异常"""
    pass


class PluginLoadError(PluginError):
    """插件加载失败"""

    def __init__(self, plugin_name: str, reason: str):
        super().__init__(
            message=f"插件 '{plugin_name}' 加载失败: {reason}",
            error_code="PLUGIN_LOAD_ERROR",
            details={"plugin_name": plugin_name, "reason": reason}
        )


class PluginNotFoundError(PluginError):
    """插件未找到"""

    def __init__(self, country_code: str):
        super().__init__(
            message=f"未找到国家代码为 '{country_code}' 的插件",
            error_code="PLUGIN_NOT_FOUND",
            details={"country_code": country_code}
        )


class PluginMethodNotImplementedError(PluginError):
    """插件方法未实现"""

    def __init__(self, plugin_name: str, method_name: str):
        super().__init__(
            message=f"插件 '{plugin_name}' 未实现方法 '{method_name}'",
            error_code="PLUGIN_METHOD_NOT_IMPLEMENTED",
            details={"plugin_name": plugin_name, "method_name": method_name}
        )


class CalculationError(PensionSystemError):
    """计算相关异常"""
    pass


class PensionCalculationError(CalculationError):
    """退休金计算错误"""

    def __init__(self, message: str, country_code: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="PENSION_CALCULATION_ERROR",
            details={"country_code": country_code}
        )


class TaxCalculationError(CalculationError):
    """税务计算错误"""

    def __init__(self, message: str, country_code: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="TAX_CALCULATION_ERROR",
            details={"country_code": country_code}
        )


class CPFCalculationError(CalculationError):
    """新加坡CPF计算错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CPF_CALCULATION_ERROR",
            details=details or {}
        )


class ValidationError(PensionSystemError):
    """输入验证错误"""

    def __init__(self, message: str, field_name: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_name": field_name, "value": value}
        )


class SalaryValidationError(ValidationError):
    """工资验证错误"""

    def __init__(self, salary: float, min_salary: float = 0.01):
        super().__init__(
            message=f"工资 {salary} 无效，必须大于 {min_salary}",
            field_name="salary",
            value=salary
        )


class AgeValidationError(ValidationError):
    """年龄验证错误"""

    def __init__(self, age: int, min_age: int = 18, max_age: int = 100):
        super().__init__(
            message=f"年龄 {age} 无效，必须在 {min_age}-{max_age} 岁之间",
            field_name="age",
            value=age
        )


class CountryValidationError(ValidationError):
    """国家代码验证错误"""

    def __init__(self, country_code: str, supported_countries: list):
        super().__init__(
            message=f"不支持的国家代码 '{country_code}'，支持的国家: {', '.join(supported_countries)}",
            field_name="country_code",
            value=country_code
        )


class CurrencyError(PensionSystemError):
    """货币相关异常"""
    pass


class CurrencyConversionError(CurrencyError):
    """货币转换错误"""

    def __init__(self, from_currency: str, to_currency: str, amount: float, reason: str = ""):
        super().__init__(
            message=f"货币转换失败: {amount} {from_currency} -> {to_currency}. {reason}",
            error_code="CURRENCY_CONVERSION_ERROR",
            details={
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
                "reason": reason
            }
        )


class CurrencyNotFoundError(CurrencyError):
    """货币未找到"""

    def __init__(self, currency_code: str):
        super().__init__(
            message=f"未找到货币代码 '{currency_code}'",
            error_code="CURRENCY_NOT_FOUND",
            details={"currency_code": currency_code}
        )


class CacheError(PensionSystemError):
    """缓存相关异常"""
    pass


class CacheLoadError(CacheError):
    """缓存加载错误"""

    def __init__(self, cache_file: str, reason: str):
        super().__init__(
            message=f"缓存文件 '{cache_file}' 加载失败: {reason}",
            error_code="CACHE_LOAD_ERROR",
            details={"cache_file": cache_file, "reason": reason}
        )


class CacheSaveError(CacheError):
    """缓存保存错误"""

    def __init__(self, cache_file: str, reason: str):
        super().__init__(
            message=f"缓存文件 '{cache_file}' 保存失败: {reason}",
            error_code="CACHE_SAVE_ERROR",
            details={"cache_file": cache_file, "reason": reason}
        )


class NetworkError(PensionSystemError):
    """网络相关异常"""
    pass


class ExchangeRateAPIError(NetworkError):
    """汇率API错误"""

    def __init__(self, api_url: str, status_code: Optional[int] = None, reason: str = ""):
        message = f"汇率API请求失败: {api_url}"
        if status_code:
            message += f" (状态码: {status_code})"
        if reason:
            message += f" - {reason}"

        super().__init__(
            message=message,
            error_code="EXCHANGE_RATE_API_ERROR",
            details={"api_url": api_url, "status_code": status_code, "reason": reason}
        )


class ConfigurationError(PensionSystemError):
    """配置相关异常"""
    pass


class MissingConfigurationError(ConfigurationError):
    """缺少配置错误"""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"缺少必需的配置项: {config_key}",
            error_code="MISSING_CONFIGURATION",
            details={"config_key": config_key}
        )


class InvalidConfigurationError(ConfigurationError):
    """无效配置错误"""

    def __init__(self, config_key: str, value: Any, reason: str):
        super().__init__(
            message=f"配置项 '{config_key}' 的值 '{value}' 无效: {reason}",
            error_code="INVALID_CONFIGURATION",
            details={"config_key": config_key, "value": value, "reason": reason}
        )


# 异常处理工具函数
def handle_exception(exception: Exception, logger=None) -> Dict[str, Any]:
    """统一异常处理函数"""

    if logger:
        logger.error(f"发生异常: {exception}")

    if isinstance(exception, PensionSystemError):
        return {
            "success": False,
            "error": {
                "type": exception.__class__.__name__,
                "message": exception.message,
                "error_code": exception.error_code,
                "details": exception.details
            }
        }
    else:
        return {
            "success": False,
            "error": {
                "type": exception.__class__.__name__,
                "message": str(exception),
                "error_code": "UNKNOWN_ERROR",
                "details": {}
            }
        }


def validate_salary(salary: float, min_salary: float = 0.01) -> None:
    """验证工资"""
    if not isinstance(salary, (int, float)):
        raise ValidationError(f"工资必须是数字，当前类型: {type(salary)}")

    if salary < min_salary:
        raise SalaryValidationError(salary, min_salary)


def validate_age(age: int, min_age: int = 18, max_age: int = 100) -> None:
    """验证年龄"""
    if not isinstance(age, int):
        raise ValidationError(f"年龄必须是整数，当前类型: {type(age)}")

    if age < min_age or age > max_age:
        raise AgeValidationError(age, min_age, max_age)


def validate_country_code(country_code: str, supported_countries: list) -> None:
    """验证国家代码"""
    if not isinstance(country_code, str):
        raise ValidationError(f"国家代码必须是字符串，当前类型: {type(country_code)}")

    if country_code.upper() not in [c.upper() for c in supported_countries]:
        raise CountryValidationError(country_code, supported_countries)


# 导出所有异常类
__all__ = [
    'PensionSystemError',
    'PluginError',
    'PluginLoadError',
    'PluginNotFoundError',
    'PluginMethodNotImplementedError',
    'CalculationError',
    'PensionCalculationError',
    'TaxCalculationError',
    'CPFCalculationError',
    'ValidationError',
    'SalaryValidationError',
    'AgeValidationError',
    'CountryValidationError',
    'CurrencyError',
    'CurrencyConversionError',
    'CurrencyNotFoundError',
    'CacheError',
    'CacheLoadError',
    'CacheSaveError',
    'NetworkError',
    'ExchangeRateAPIError',
    'ConfigurationError',
    'MissingConfigurationError',
    'InvalidConfigurationError',
    'handle_exception',
    'validate_salary',
    'validate_age',
    'validate_country_code'
]
