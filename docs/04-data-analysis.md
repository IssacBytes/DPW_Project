# 4. 数据分析模块

**对应源文件**：`src/data_analysis.py`

## 4.1 模块职责

对清洗后的数据进行统计分析、趋势分析、对比分析、相关性分析等，提供函数接口供 GUI 调用。

## 4.2 描述统计：`descriptive_stats()`

```python
def descriptive_stats(df: pd.DataFrame, column: str) -> dict:
```

**功能**：计算指定列的描述性统计量。

**参数**：
- `df`：输入 DataFrame
- `column`：要分析的列名

**返回值**：

| 字段 | 说明 |
|------|------|
| `count` | 非空值数量 |
| `mean` | 平均值 |
| `median` | 中位数 |
| `std` | 标准差 |
| `min` | 最小值 |
| `max` | 最大值 |
| `q1` | 第一四分位数（25%） |
| `q3` | 第三四分位数（75%） |
| `sum` | 总和 |

**用途**：在 Overview 标签页中展示统计卡片。

## 4.3 趋势分析

### 全球趋势：`global_trend()`

```python
def global_trend(df: pd.DataFrame, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
```

**功能**：计算全球每日趋势（所有国家按日期汇总）。

**处理**：
- `df.groupby('date')[metric].sum()` — 按日期分组求和
- 按日期排序

**返回值**：`[date, metric_sum]` 的 DataFrame

### 国家趋势：`country_trend()`

```python
def country_trend(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
```

**功能**：提取单个国家的时间序列数据。

**返回值**：`[date, metric]` 的 DataFrame

## 4.4 对比分析

### 多国对比：`compare_countries()`

```python
def compare_countries(df: pd.DataFrame, countries: list, metric: str = 'total_cases_per_million') -> pd.DataFrame:
```

**功能**：对比多个国家在同一指标上的时间序列。

**返回值**：`[date, country, metric]` 的 DataFrame

**用途**：在 Country Comparison 标签页中生成多线折线图。

### 国家排名：`top_countries()`

```python
def top_countries(df: pd.DataFrame, metric: str = 'total_cases', n: int = 10, date: str = None) -> pd.DataFrame:
```

**功能**：获取指定指标排名前 N 的国家。

**参数**：
- `metric`：排名依据的指标
- `n`：返回前多少名
- `date`：指定日期（`None` 表示使用每个国家的最新日期）

**处理**：
- 如果 `date` 为 `None`，用 `df.groupby('country')['date'].idxmax()` 取每个国家的最新行
- 否则按指定日期过滤
- 用 `df.nlargest(n, metric)` 取前 N 名

**返回值**：`[country, metric, continent, population]` 的 DataFrame

**用途**：在 Rankings 标签页中生成排名柱状图。

## 4.5 增长率分析：`growth_rate_analysis()`

```python
def growth_rate_analysis(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
```

**功能**：计算一个国家指定指标的每日增长率和变化量。

**计算公式**：
- `daily_change = today_value - yesterday_value`（每日变化量）
- `growth_rate = (today_value - yesterday_value) / yesterday_value * 100`（每日增长率百分比）

**返回值**：`[date, metric, growth_rate, daily_change]` 的 DataFrame

**用途**：在 Country Deep Dive 标签页中生成增长率分析图。

## 4.6 累计分析：`cumulative_analysis()`

```python
def cumulative_analysis(df: pd.DataFrame, country: str) -> pd.DataFrame:
```

**功能**：分析一个国家的累计病例、累计死亡和死亡率。

**计算**：
- `death_rate = total_deaths / total_cases * 100`

**返回值**：`[date, total_cases, total_deaths, new_cases_smoothed, new_deaths_smoothed, death_rate]`

## 4.7 大洲对比：`continent_comparison()`

```python
def continent_comparison(df: pd.DataFrame, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
```

**功能**：按日期和大洲分组汇总指标。

**返回值**：`[date, continent, metric_sum]` 的 DataFrame

## 4.8 相关性分析：`correlation_analysis()`

```python
def correlation_analysis(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
```

**功能**：计算数值列之间的相关系数矩阵。

**默认分析的 11 个指标**：
- `new_cases_smoothed` — 新增病例
- `new_deaths_smoothed` — 新增死亡
- `total_cases_per_million` — 每百万人累计病例
- `total_deaths_per_million` — 每百万人累计死亡
- `people_fully_vaccinated_per_hundred` — 完全接种率
- `stringency_index` — 严格指数
- `population_density` — 人口密度
- `median_age` — 中位年龄
- `gdp_per_capita` — 人均 GDP
- `diabetes_prevalence` — 糖尿病患病率
- `life_expectancy` — 预期寿命

**返回值**：相关系数矩阵 DataFrame（值范围 -1 到 1）

## 4.9 疫苗接种影响：`vaccination_impact()`

```python
def vaccination_impact(df: pd.DataFrame, country: str) -> pd.DataFrame:
```

**功能**：对齐疫苗接种数据和病例数据，用于观察疫苗接种对疫情的影响。

**返回值**：`[date, new_cases_smoothed, new_deaths_smoothed, people_fully_vaccinated_per_hundred, total_vaccinations_per_hundred]`

## 4.10 峰值检测：`get_peak_dates()`

```python
def get_peak_dates(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed', n_peaks: int = 3) -> list:
```

**功能**：找出指标最高的 N 个日期。

**返回值**：`[(date_string, value), ...]` 列表

**示例**：
```python
peaks = get_peak_dates(df, 'United States', 'new_cases_smoothed', n_peaks=3)
# 返回: [('2022-01-15', 802432.0), ('2022-01-14', 786321.0), ('2022-01-16', 771245.0)]
```

## 4.11 函数调用关系图

```
用户操作（选择指标/国家）
    │
    ├── 概览标签页
    │   └── descriptive_stats(df, metric) → 统计卡片
    │
    ├── 全球趋势标签页
    │   └── global_trend(df, metric) → 全球趋势数据
    │
    ├── 国家对比标签页
    │   └── compare_countries(df, countries, metric) → 对比数据
    │
    ├── 深度分析标签页
    │   ├── growth_rate_analysis(df, country, metric) → 增长率
    │   └── vaccination_impact(df, country) → 疫苗影响
    │
    ├── 排名标签页
    │   └── top_countries(df, metric, n=20) → 前20名
    │
    └── 大洲分析标签页
        └── continent_comparison(df, metric) → 大洲汇总
