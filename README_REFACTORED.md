# 养老金对比系统 - 重构版本

## 项目概述

这是一个重构后的养老金对比系统，支持9个国家和地区的养老金计算和对比分析。重构后的系统采用了更清晰的模块化架构，将各个国家的分析功能分离到各自的文件夹中。

## 重构特点

### 1. 模块化架构
- **main.py**: 轻量化的主程序，只负责参数解析和调用分析器
- **analyzers/**: 统一的分析器管理模块
- **plugins/国家代码/**: 每个国家独立的计算器和分析器

### 2. 代码组织
```
Comparison-of-pensions/
├── main.py                          # 轻量化主程序
├── analyzers/                       # 分析器管理模块
│   ├── __init__.py
│   └── analyzer_manager.py         # 统一的分析器管理器
├── core/                           # 核心计算引擎
│   ├── models.py                   # 数据模型
│   ├── pension_engine.py           # 养老金计算引擎
│   └── ...
├── plugins/                        # 各国计算器和分析器
│   ├── usa/                        # 美国
│   │   ├── usa_calculator.py      # 计算器
│   │   └── usa_analyzer.py        # 分析器
│   ├── china/                      # 中国
│   │   ├── china_calculator.py    # 计算器
│   │   └── china_analyzer.py      # 分析器
│   ├── hongkong/                   # 香港
│   ├── singapore/                  # 新加坡
│   ├── taiwan/                     # 台湾
│   ├── japan/                      # 日本
│   ├── uk/                         # 英国
│   ├── australia/                  # 澳大利亚
│   └── canada/                     # 加拿大
└── utils/                          # 工具模块
    ├── currency_converter.py       # 货币转换
    └── ...
```

## 使用方法

### 1. 单国分析
```bash
# 分析美国养老金
python main.py --us

# 分析中国养老金
python main.py --cn

# 分析香港MPF
python main.py --hk

# 分析新加坡CPF
python main.py --sg

# 分析台湾养老金
python main.py --tw

# 分析日本养老金
python main.py --jp

# 分析英国养老金
python main.py --uk

# 分析澳大利亚养老金
python main.py --au

# 分析加拿大养老金
python main.py --ca
```

### 2. 多国对比
```bash
# 对比中国和澳大利亚
python main.py cn,au

# 对比美国、中国和澳大利亚
python main.py us,cn,au

# 对比香港、新加坡和台湾
python main.py hk,sg,tw
```

### 3. 显示帮助
```bash
python main.py
```

## 重构优势

### 1. 代码可维护性
- 每个国家的分析逻辑独立，便于维护和修改
- 统一的接口设计，便于扩展新的国家
- 清晰的模块边界，降低代码耦合度

### 2. 功能扩展性
- 新增国家只需添加对应的计算器和分析器
- 分析器管理器统一管理所有分析器
- 支持灵活的多国对比组合

### 3. 代码复用性
- 分析器基类提供通用功能
- 计算器专注于核心算法
- 分析器专注于结果展示和对比

### 4. 测试友好性
- 每个模块可以独立测试
- 分析器可以单独验证
- 便于单元测试和集成测试

## 技术架构

### 1. 分析器管理器 (AnalyzerManager)
- 统一管理所有国家的分析器
- 提供单国分析和多国对比接口
- 处理参数验证和错误处理

### 2. 国家分析器 (CountryAnalyzer)
- 继承自基础分析器类
- 实现特定国家的分析逻辑
- 处理本地化的显示格式

### 3. 计算器 (Calculator)
- 专注于养老金计算算法
- 提供标准化的计算接口
- 返回结构化的计算结果

## 扩展指南

### 添加新国家

1. 在 `plugins/` 下创建新的国家文件夹
2. 实现计算器类 (继承自 BaseCalculator)
3. 实现分析器类 (继承自基础分析器)
4. 在 `analyzer_manager.py` 中注册新分析器
5. 在 `main.py` 中添加参数支持

### 示例结构
```
plugins/newcountry/
├── __init__.py
├── newcountry_calculator.py
└── newcountry_analyzer.py
```

## 性能优化

### 1. 延迟导入
- 计算器按需导入，减少启动时间
- 分析器按需创建，节省内存

### 2. 缓存机制
- 计算结果可以缓存
- 汇率转换结果缓存

### 3. 并行计算
- 多国对比可以并行计算
- 支持异步分析

## 总结

重构后的系统具有以下特点：
- **模块化**: 清晰的代码组织结构
- **可扩展**: 易于添加新的国家支持
- **可维护**: 降低代码复杂度
- **可测试**: 支持单元测试和集成测试
- **高性能**: 优化的计算和缓存机制

这种架构设计使得系统更加健壮、可维护，同时保持了原有的功能完整性。
