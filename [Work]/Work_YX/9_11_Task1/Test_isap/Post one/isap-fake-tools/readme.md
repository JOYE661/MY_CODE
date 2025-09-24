# ISAP Demo Data Generator

一个灵活的Python框架，用于生成模拟数据并插入到PostgreSQL数据库中。该框架基于FastAPI构建，提供REST API接口和Streamlit可视化界面，支持通过配置文件定义数据生成规则。

## 功能特点

1. **基于配置的数据生成**：通过JSON配置文件定义表结构和数据生成规则
2. **数据关联性支持**：可以配置表之间的数据关联
3. **可控制的数据量**：通过参数控制每天生成的数据量
4. **时间规律模拟**：模拟符合实际业务场景的时间分布规律
5. **随机性与真实性**：生成具有随机性但又符合业务逻辑的数据
6. **PostgreSQL数据库对接**：直接将生成的数据插入到数据库
7. **FastAPI接口**：提供REST API接口控制数据生成任务
8. **Streamlit控制面板**：提供直观的可视化界面，方便操作和监控
9. **易扩展框架**：添加新表的数据生成只需添加对应的配置文件

## 项目结构

```
├── main.py                 # FastAPI应用入口文件
├── streamlit_app.py        # Streamlit控制面板应用
├── run_streamlit.sh        # Streamlit启动脚本
├── requirements.txt        # 项目依赖
├── .env                    # 环境变量配置
├── configs/                # 表配置目录
│   ├── __init__.py
│   ├── crm_customer.json       # CRM客户表配置
│   ├── oms_order.json          # 订单表配置
│   ├── oms_order_item.json     # 订单商品表配置
│   ├── lms_shipment.json       # 物流表配置
│   ├── fms_financial_transaction.json  # 财务交易表配置
│   ├── ext_market_trend.json   # 市场趋势表配置
│   └── crawler_competitor_price.json  # 竞争对手价格表配置
└── app/
    ├── core/              # 核心配置和功能
    │   ├── config.py      # 配置管理
    │   └── database.py    # 数据库连接管理
    ├── api/               # API接口定义
    │   └── api_v1/
    │       ├── api.py     # API路由
    │       └── endpoints/ # API端点
    │           └── data_generation.py
    ├── schemas/           # 数据模型
    │   └── data_generation.py
    └── services/          # 业务服务
        └── data_generator.py  # 数据生成器核心实现
```

## 安装指南

1. 确保已安装Python 3.7+和PostgreSQL数据库

2. 安装项目依赖：
   ```
   pip3 install -r requirements.txt
   ```

3. 配置环境变量：
   修改`.env`文件，配置PostgreSQL数据库连接信息

4. 启动FastAPI应用（可选）：
   ```
   python3 main.py
   ```
   访问API文档：http://localhost:8000/docs

5. 启动Streamlit控制面板：
   ```
   ./run_streamlit.sh
   ```
   或直接运行：
   ```
   python3 -m streamlit run streamlit_app.py
   ```
   访问控制面板：http://localhost:8501

## 使用方法

### 1. 通过Streamlit控制面板（推荐）

Streamlit提供了直观的可视化界面，操作步骤如下：

1. 启动控制面板：`./run_streamlit.sh`
2. 在侧边栏选择要生成数据的表
3. 配置每天生成的记录数和日期范围
4. 点击"生成数据"按钮开始生成数据
5. 查看日志输出了解生成进度和结果

控制面板功能：
- 数据库连接状态显示
- 表选择和参数配置
- 实时日志输出
- 表结构信息查看
- 数据清空功能（需二次确认）

### 2. 通过API生成数据

使用FastAPI的交互式文档页面，调用`/api/v1/data/generate`接口：

- `tables`：要生成数据的表名列表，为空则生成所有表
- `records_per_day`：每天生成的记录数量
- `start_date`：开始日期（YYYY-MM-DD格式）
- `end_date`：结束日期（YYYY-MM-DD格式）
- `async_mode`：是否异步生成数据

### 2. 添加新表的数据生成

要为新表添加数据生成功能，只需在`configs/`目录下创建一个新的JSON配置文件，文件名与表名相同。配置文件格式如下：

```json
{
  "fields": {
    "字段名": {
      "type": "数据类型",
      "generator": "生成器类型",
      "min": 最小值,
      "max": 最大值,
      "precision": 小数精度
    }
  },
  "relationships": {
    "关联字段名": {
      "table": "关联表名",
      "field": "关联字段名"
    }
  },
  "post_process": [
    {
      "type": "calculate",
      "formula": "计算公式"
    }
  ]
}
```

### 3. 配置数据生成规则

支持的字段类型：
- `string`：字符串类型
- `integer`：整数类型
- `decimal`：小数类型
- `boolean`：布尔类型
- `timestamp`：时间戳类型

支持的生成器：
- `uuid`：生成UUID
- `current_timestamp`：生成当前时间戳（遵循时间规律）
- `incremental`：生成递增ID
- `random_choice:选项1,选项2,...`：从选项中随机选择

## 时间规律配置

在`app/core/config.py`中可以配置数据生成的时间规律：
- `PEAK_HOURS`：一天中的高峰期时段
- `PEAK_DAYS`：一周中的高峰期日期

## 注意事项

1. 使用前请确保PostgreSQL数据库连接配置正确
2. 生成大量数据时建议使用异步模式
3. 新表的配置文件必须放在`configs/`目录下
4. 表之间的关联关系需要正确配置以保证数据一致性

## 示例

运行测试脚本验证框架功能：
```
python3 test_framework.py
```

这将显示可用的表和生成的数据示例，但不会实际插入数据库。