# 3. 数据清洗模块

**对应源文件**：`src/data_cleaner.py`

## 3.1 模块职责

对原始数据进行清洗，包括去重、排序、缺失值处理、过滤等操作，返回可执行的数据结构。

## 3.2 核心函数：`clean_data()`

```python
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
```

**功能**：执行自动数据清洗。

**清洗步骤**：
1. **去重** — `df.drop_duplicates()` 移除完全重复的行
2. **排序** — `df.sort_values(['country', 'date'])` 按国家和日期排序，确保时间序列有序
3. **日期转换** — `pd.to_datetime(df['date'])` 确保日期列为 datetime 类型

**参数**：
- `df`：原始 DataFrame

**返回值**：
- 清洗后的 DataFrame

## 3.3 缺失值处理：`handle_missing_values()`

```python
def handle_missing_values(df: pd.DataFrame, strategy: str = 'ffill') -> pd.DataFrame:
```

**功能**：处理数据集中的缺失值。

**支持的策略**：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `'ffill'`（默认） | 前向填充 → 后向填充 | 时间序列数据，用前一天的值填充后一天 |
| `'bfill'` | 后向填充 → 前向填充 | 与 ffill 相反 |
| `'drop'` | 删除含缺失值的行 | 缺失数据较少时 |
| `'zero'` | 用 0 填充 | 缺失表示无事件发生时 |
| `'interpolate'` | 线性插值 | 数据变化平滑时 |

**实现细节**：
- 只填充数值列（不填充 `country`, `code`, `continent` 等标识列）
- 按国家分组填充，避免跨国家填充
- 默认策略：先 `ffill`（用前一天的值填充），再 `bfill`（处理序列开头的缺失值）

**示例**：
```python
# 原始数据（某国家）
date       new_cases
2020-01-01  NaN       ← 序列开头缺失
2020-01-02  100
2020-01-03  NaN       ← 中间缺失
2020-01-04  150

# ffill 后
2020-01-01  NaN       ← 仍缺失（前面没有值）
2020-01-02  100
2020-01-03  100       ← 用前一天填充
2020-01-04  150

# bfill 后
2020-01-01  100       ← 用后一天填充
2020-01-02  100
2020-01-03  100
2020-01-04  150
```

## 3.4 过滤函数

### `filter_by_date()`

```python
def filter_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
```

按日期范围过滤数据。

**参数**：
- `start_date`：起始日期（格式 `YYYY-MM-DD`）
- `end_date`：结束日期（格式 `YYYY-MM-DD`）

### `filter_by_country()`

```python
def filter_by_country(df: pd.DataFrame, countries: list) -> pd.DataFrame:
```

只保留指定国家的数据。

### `filter_by_continent()`

```python
def filter_by_continent(df: pd.DataFrame, continents: list) -> pd.DataFrame:
```

只保留指定大洲的数据。

### `remove_outliers()`

```python
def remove_outliers(df: pd.DataFrame, column: str, method: str = 'iqr', threshold: float = 1.5) -> pd.DataFrame:
```

移除指定列的异常值。

**方法**：
- `'iqr'`（默认）：四分位距法，移除超出 `Q1 - 1.5*IQR` 到 `Q3 + 1.5*IQR` 范围的值
- `'zscore'`：Z-score 法，移除 Z-score 绝对值超过阈值的值

## 3.5 清洗统计：`get_cleaning_summary()`

```python
def get_cleaning_summary(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> dict:
```

**功能**：对比清洗前后的数据，返回清洗统计。

**返回值**：

| 字段 | 说明 |
|------|------|
| `original_rows` | 清洗前行数 |
| `cleaned_rows` | 清洗后行数 |
| `rows_removed` | 移除的行数 |
| `original_columns` | 清洗前列数 |
| `cleaned_columns` | 清洗后列数 |
| `missing_before` | 清洗前缺失值总数 |
| `missing_after` | 清洗后缺失值总数 |
| `duplicates_removed` | 移除的重复行数 |

**用途**：在 GUI 的 Data Pipeline 标签页中展示清洗前后对比。

## 3.6 在 GUI 中的使用

在 `app.py` 的 Data Pipeline 标签页中：

```python
# 获取清洗统计
summary = get_cleaning_summary(df_raw, df)

# 展示清洗操作
- Removed {summary['duplicates_removed']} duplicate rows
- Sorted by country and date
- Forward-filled missing values within each country
- Backward-filled remaining NaNs at start of series

# 展示清洗前后对比
- Rows Before: {summary['original_rows']}
- Rows After: {summary['cleaned_rows']}
- Missing Before: {summary['missing_before']}
- Missing After: {summary['missing_after']}
