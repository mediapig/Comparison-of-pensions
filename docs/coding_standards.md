# 退休金对比系统 - 编码标准

## 1. 项目结构规范

### 1.1 目录结构
```
Comparison-of-pensions/
├── core/                    # 核心模块
│   ├── models.py           # 数据模型
│   ├── base_plugin.py      # 插件基类
│   ├── plugin_manager.py   # 插件管理器
│   └── analysis_runner.py  # 分析运行器
├── plugins/                # 国家插件
│   ├── {country}/          # 每个国家一个目录
│   │   ├── plugin.py       # 主插件文件
│   │   ├── calculator.py   # 计算器
│   │   ├── analyzer.py     # 分析器
│   │   ├── tax_calculator.py # 税务计算器
│   │   └── config.py       # 配置文件
├── utils/                  # 工具模块
├── tests/                  # 测试文件
├── docs/                   # 文档
└── main.py                 # 主程序
```

### 1.2 文件命名规范
- 使用小写字母和下划线：`tax_calculator.py`
- 类名使用大驼峰：`TaxCalculator`
- 函数和变量使用小写字母和下划线：`calculate_tax()`
- 常量使用大写字母和下划线：`DEFAULT_RETIREMENT_AGE`

## 2. 代码质量规范

### 2.1 类型注解
所有函数和方法必须包含完整的类型注解：

```python
def calculate_pension(
    monthly_salary: float,
    start_age: int,
    retirement_age: int = 65
) -> Dict[str, float]:
    """计算退休金"""
    pass
```

### 2.2 文档字符串
使用Google风格的文档字符串：

```python
def calculate_pension(
    monthly_salary: float,
    start_age: int,
    retirement_age: int = 65
) -> Dict[str, float]:
    """计算退休金

    Args:
        monthly_salary: 月薪
        start_age: 开始工作年龄
        retirement_age: 退休年龄，默认为65岁

    Returns:
        包含退休金信息的字典

    Raises:
        ValueError: 当输入参数无效时
    """
    pass
```

### 2.3 错误处理
使用统一的错误处理机制：

```python
class PensionCalculationError(Exception):
    """退休金计算错误"""
    pass

def calculate_pension(monthly_salary: float) -> Dict[str, float]:
    if monthly_salary <= 0:
        raise PensionCalculationError("月薪必须大于0")
    # ...
```

### 2.4 常量定义
将魔法数字提取为常量：

```python
class PensionConstants:
    DEFAULT_RETIREMENT_AGE = 65
    DEFAULT_START_AGE = 30
    MAX_WORKING_YEARS = 50
    MIN_SALARY = 0.01
```

## 3. 插件开发规范

### 3.1 插件基类
所有国家插件必须继承自`BaseCountryPlugin`：

```python
class CountryPlugin(BaseCountryPlugin):
    COUNTRY_CODE = "XX"
    COUNTRY_NAME = "国家名称"
    CURRENCY = "货币代码"

    def calculate_pension(self, profile: SalaryProfile) -> Dict[str, Any]:
        """计算退休金 - 必须实现"""
        pass

    def calculate_tax(self, income: float) -> Dict[str, float]:
        """计算税务 - 必须实现"""
        pass
```

### 3.2 返回数据格式
所有插件必须返回统一格式的数据：

```python
{
    "country": "国家名称",
    "currency": "货币代码",
    "analysis_time": "分析时间",
    "first_year_analysis": {
        "age": 30,
        "income_situation": {...},
        "social_security": {...},
        "tax_situation": {...}
    },
    "work_period_summary": {...},
    "retirement_analysis": {...},
    "final_account_balances": {...},
    "investment_return_analysis": {...}
}
```

## 4. 测试规范

### 4.1 测试文件结构
```
tests/
├── test_core/              # 核心模块测试
├── test_plugins/           # 插件测试
│   ├── test_singapore.py
│   ├── test_china.py
│   └── ...
├── test_utils/             # 工具模块测试
└── conftest.py             # 测试配置
```

### 4.2 测试命名
- 测试文件：`test_module_name.py`
- 测试类：`TestClassName`
- 测试方法：`test_function_name_scenario`

### 4.3 测试覆盖
- 单元测试覆盖率 > 80%
- 集成测试覆盖主要功能
- 边界条件测试
- 错误情况测试

## 5. 日志规范

### 5.1 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 5.2 日志格式
```python
import logging

logger = logging.getLogger(__name__)

def calculate_pension(monthly_salary: float) -> Dict[str, float]:
    logger.info(f"开始计算退休金，月薪: {monthly_salary}")
    try:
        # 计算逻辑
        result = perform_calculation(monthly_salary)
        logger.info("退休金计算完成")
        return result
    except Exception as e:
        logger.error(f"退休金计算失败: {e}")
        raise
```

## 6. 性能规范

### 6.1 性能要求
- 单个国家分析 < 5秒
- 内存使用 < 100MB
- 支持并发处理

### 6.2 性能优化
- 使用缓存机制
- 避免重复计算
- 优化数据库查询
- 使用异步处理（如需要）

## 7. 安全规范

### 7.1 输入验证
- 所有用户输入必须验证
- 防止SQL注入
- 防止XSS攻击
- 数据脱敏

### 7.2 敏感信息
- 不在日志中记录敏感信息
- 使用环境变量存储配置
- 定期更新依赖包

## 8. 版本控制规范

### 8.1 Git提交信息
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

### 8.2 分支管理
- `main`: 主分支
- `develop`: 开发分支
- `feature/xxx`: 功能分支
- `hotfix/xxx`: 热修复分支
