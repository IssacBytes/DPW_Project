# 2. 数据加载模块

**对应源文件**：`src/data_loader.py`

## 2.1 模块职责

从 CSV 文件加载 COVID-19 数据集，解析为 pandas DataFrame，并提供数据探索的辅助函数。

## 2.2 核心函数：`load_data()`

```python
def load_data(filepath: str) -> pd.DataFrame:
```

**功能**：读取 CSV 文件并转换为 DataFrame。

**处理步骤**：
1. `pd.read_csv(filepath, low_memory=False)` — 读取 CSV，`low_memory=False` 避免混合类型警告
2. `pd.to_datetime(df['date'])` — 将日期列转为 datetime 类型

**参数**：
- `filepath`：CSV 文件路径（字符串）

**返回值**：
- `pd.DataFrame` — 包含全部 67 列、570,606 行数据的 DataFrame

**调用示例**：
```python
from src.data_loader import load_data
df = load_data('compact.csv')
print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")
# 输出: Loaded 570,606 rows, 67 columns
```

## 2.3 辅助函数

### `get_columns_info()`

```python
def get_columns_info(df: pd.DataFrame) -> list:
```

获取所有列的信息。

**返回值**：`list[dict]`，每个 dict 包含：
- `name` — 列名
- `dtype` — 数据类型（如 `float64`, `object`）
- `non_null` — 非空值数量
- `null_count` — 空值数量
- `sample_values` — 前 3 个唯一示例值

**用途**：在 GUI 的 Data Pipeline 标签页中展示列概览表格。

### `select_columns()`

```python
def select_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
```

选择指定的列，只保留在数据集中存在的列。

### `get_countries()`

```python
def get_countries(df: pd.DataFrame) -> list:
```

返回排序后的国家名称列表。

### `get_continents()`

```python
def get_continents(df: pd.DataFrame) -> list:
```

返回排序后的大洲名称列表。

### `get_date_range()`

```python
def get_date_range(df: pd.DataFrame) -> tuple:
```

返回 `(min_date, max_date)` 元组，均为 datetime 对象。

### `get_numeric_columns()`

```python
def get_numeric_columns(df: pd.DataFrame) -> list:
```

返回所有数值型列名（排除 `code` 等 ID 列）。

### `get_data_preview()`

```python
def get_data_preview(df: pd.DataFrame, n_rows: int = 10) -> pd.DataFrame:
```

返回前 n 行数据，用于快速预览。

### `get_basic_stats()`

```python
def get_basic_stats(df: pd.DataFrame) -> pd.DataFrame:
```

返回数值列的 `describe()` 统计表（count, mean, std, min, 25%, 50%, 75%, max）。

## 2.4 数据集列说明

数据集共有 **67 列**，以下是关键列的分组：

| 分组 | 列名 | 说明 |
|------|------|------|
| **标识** | `country` | 国家名称 |
| | `code` | 国家 ISO 代码 |
| | `continent` | 大洲 |
| | `date` | 日期 |
| **病例** | `new_cases_smoothed` | 每日新增病例（7 日平滑） |
| | `total_cases` | 累计病例 |
| | `total_cases_per_million` | 每百万人累计病例 |
| **死亡** | `new_deaths_smoothed` | 每日新增死亡（7 日平滑） |
| | `total_deaths` | 累计死亡 |
| | `total_deaths_per_million` | 每百万人累计死亡 |
| **疫苗接种** | `people_fully_vaccinated_per_hundred` | 完全接种率（%） |
| | `people_vaccinated_per_hundred` | 接种至少一剂率（%） |
| | `total_boosters_per_hundred` | 加强针接种率（%） |
| **检测** | `positive_rate` | 阳性检测率 |
| | `new_tests_smoothed` | 每日新增检测（7 日平滑） |
| **政策** | `stringency_index` | 政府响应严格指数（0-100） |
| **流行病学** | `reproduction_rate` | 病毒传播率（R 值） |
| **人口** | `population` | 人口数 |
| | `population_density` | 人口密度 |
| | `median_age` | 中位年龄 |
| | `gdp_per_capita` | 人均 GDP |

## 2.5 在 GUI 中的使用

### 基础版 (app.py)

在 `app.py` 中，数据加载在应用启动时执行：

```python
# app.py 启动流程
df_raw = load_data(DATA_PATH)           # 加载 CSV
df = clean_data(df_raw)                  # 清洗
df = handle_missing_values(df)           # 填充缺失值

# 获取元数据供全局使用
countries = get_countries(df)            # 国家列表 → 下拉框
continents = get_continents(df)          # 大洲列表
date_min, date_max = get_date_range(df)  # 日期范围
numeric_cols = get_numeric_columns(df)   # 数值列 → 指标选择
```

### 扩展版 (app_extended.py)

扩展版使用 `CovidDataPreprocessor` 类进行数据加载，并增加了 pickle 缓存机制：

```python
# app_extended.py 启动流程
if os.path.exists(CACHE_PATH):
    # 直接从缓存加载，跳过预处理
    with open(CACHE_PATH, 'rb') as f:
        df_raw, df = pickle.load(f)
else:
    # 首次运行：完整预处理
    processor = CovidDataPreprocessor(DATA_PATH)
    df_raw = processor.load_data()
    processor.clean_data()
    df = processor.prepare_for_analysis(variables=None)
    df = handle_missing_values(df, strategy='ffill')
    # 缓存到磁盘，下次秒开
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump((df_raw, df), f)

# 预计算管道统计和列信息（只计算一次）
PIPELINE_SUMMARY = get_cleaning_summary(df_raw, df)
PIPELINE_COLS_INFO = [...]  # 所有列的元数据

# 预计算聚类基础数据（避免每次切换标签页重新计算）
CLUSTER_FEATURES = ['total_cases_per_million', 'total_deaths_per_million',
                    'people_fully_vaccinated_per_hundred', 'population']
CLUSTER_BASE_DF = df.loc[df.groupby('country')['date'].idxmax()].dropna(subset=CLUSTER_FEATURES).copy()
```

**缓存优化效果**：
- 首次启动：约 10-15 秒（加载 + 清洗 + 缓存）
- 二次启动：约 0.5-1 秒（直接从 pickle 加载）
