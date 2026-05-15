# 7. 数据流与函数调用链

## 7.1 完整数据流

```
compact.csv (原始数据，570,606 行，67 列)
    │
    ▼
┌─────────────────────────────────────────────┐
│  Step 1: 数据加载                            │
│  data_loader.load_data('compact.csv')        │
│  ─────────────────────────────────           │
│  • pd.read_csv() 读取 CSV                    │
│  • pd.to_datetime() 转换日期列               │
│  • 返回原始 DataFrame                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 2: 数据清洗                            │
│  data_cleaner.clean_data(df_raw)             │
│  ─────────────────────────────────           │
│  • drop_duplicates() 去重                    │
│  • sort_values() 按国家+日期排序             │
│  • 返回排序后的 DataFrame                    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 3: 缺失值处理                          │
│  data_cleaner.handle_missing_values(df)      │
│  ─────────────────────────────────           │
│  • 按国家分组，前向填充 (ffill)              │
│  • 再后向填充 (bfill) 处理开头缺失           │
│  • 返回无缺失值的 DataFrame                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 4: 缓存保存                            │
│  pickle.dump((df_raw, df), 'data_cache.pkl') │
│  ─────────────────────────────────           │
│  • 下次启动直接读取缓存，跳过 Step 1-3       │
│  • 二次启动仅需 0.5 秒                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 5: 提取元数据                          │
│  ─────────────────────────────────           │
│  • get_countries(df) → 262 个国家            │
│  • get_continents(df) → 6 个大洲             │
│  • get_date_range(df) → 2020-01 至 2026-02   │
│  • get_numeric_columns(df) → 数值列列表      │
│  • 所有日期列表 → 时间轴滑块                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 6: 预计算（扩展版特有）                │
│  ─────────────────────────────────           │
│  • PIPELINE_SUMMARY → 清洗统计               │
│  • PIPELINE_COLS_INFO → 列元数据             │
│  • CLUSTER_BASE_DF → 聚类基础数据            │
│  • CLUSTER_CACHE → 预计算 k=3~7 聚类结果     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 7: 启动 Dash 应用                      │
│  app.run(host='127.0.0.1', port=8051)        │
│  ─────────────────────────────────           │
│  • 用户打开 http://127.0.0.1:8051            │
│  • 看到 14 个标签页的 GUI（扩展版）          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 8: 用户交互 → 回调触发                 │
│  ─────────────────────────────────           │
│  • 点击侧栏导航 → sidebar-state 更新         │
│  • 选择指标 → global-metric 更新             │
│  • 选择国家 → global-country 更新            │
│  • 拖动滑块 → global-slider 更新             │
│  • 切换分组 → group-states 更新              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 9: 数据分析                            │
│  ─────────────────────────────────           │
│  • descriptive_stats() → 统计卡片            │
│  • country_trend() → 国家趋势数据            │
│  • compare_countries() → 对比数据            │
│  • top_countries() → 排名数据                │
│  • growth_rate_analysis() → 增长率数据       │
│  • continent_comparison() → 大洲汇总         │
│  • moving_average() → 移动平均               │
│  • anomaly_detection() → 异常检测            │
│  • fatality_trend() → 病死率                 │
│  • cross_lag_correlation() → 滞后分析        │
│  • simple_clustering() → 聚类                │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 10: 可视化生成                         │
│  ─────────────────────────────────           │
│  • plot_choropleth_map() → 世界地图          │
│  • plot_trend_line() → 趋势折线图            │
│  • plot_bar_chart() → 排名柱状图             │
│  • plot_dual_axis() → 双轴图                 │
│  • plot_growth_rate() → 增长率图             │
│  • plot_scatter() → 散点图                   │
│  • make_moving_average_outputs() → MA 图     │
│  • make_anomaly_figure() → 异常图            │
│  • make_fatality_outputs() → 病死率图        │
│  • make_lag_figure() → 滞后图                │
│  • make_cluster_outputs() → 聚类图           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 11: GUI 展示                           │
│  ─────────────────────────────────           │
│  • Dash 将 Plotly Figure 渲染为 HTML         │
│  • 用户看到交互式图表                        │
│  • 可缩放、平移、悬停查看详情                │
└─────────────────────────────────────────────┘
```

## 7.2 用户操作 → 函数调用链示例

### 示例 1：查看全球新增病例趋势

```
用户操作：
1. 选择指标 "Daily New Cases"
2. 选择国家 "United States"
3. 点击侧栏 "Global Trends"
4. 拖动时间轴滑块到 2022-01

函数调用链：
─────────────────────────────────────────────
global-metric = 'new_cases_smoothed'
global-country = 'United States'
sidebar-state = {active_tab: 'tab-global'}
global-slider = 42 (对应 2022-01-15)
    │
    ▼
render_active_tab(sidebar_state, metric, country, compare_list)
    → render_tab_content('tab-global', 'new_cases_smoothed', 'United States', [...])
    → build_global('new_cases_smoothed', [...])
    │
    ▼
update_global_map('new_cases_smoothed', 42)
    → plot_choropleth_map(df, 'new_cases_smoothed', '2022-01-15')
    → 返回世界地图（颜色表示各国新增病例数）
    │
    ▼
update_global_trend('new_cases_smoothed', 'United States', [...], 42)
    → np.searchsorted(date_values, '2022-01-15')  ← 二分查找
    → plot_trend_line(filtered_df, ['United States', ...], 'new_cases_smoothed')
    → 返回趋势折线图（从 2020-01 到 2022-01）
    │
    ▼
update_global_stats('new_cases_smoothed', 42)
    → 计算 2022-01-15 的全球总计、平均、最大
    → 返回 4 个统计卡片
```

### 示例 2：对比多国疫苗接种率

```
用户操作：
1. 选择指标 "Fully Vaccinated (%)"
2. 选择国家 "United States"
3. 对比选择 "United Kingdom", "Germany", "Japan"
4. 点击侧栏 "Country Comparison"

函数调用链：
─────────────────────────────────────────────
global-metric = 'people_fully_vaccinated_per_hundred'
global-country = 'United States'
global-compare = ['United Kingdom', 'Germany', 'Japan']
sidebar-state = {active_tab: 'tab-compare'}
    │
    ▼
render_active_tab(sidebar_state, metric, country, compare_list)
    → render_tab_content('tab-compare', 'people_fully_vaccinated_per_hundred',
                         'United States', ['United Kingdom', 'Germany', 'Japan'])
    → build_compare('people_fully_vaccinated_per_hundred',
                    'United States', ['United Kingdom', 'Germany', 'Japan'])
    │
    ▼
plot_trend_line(df, ['United States', 'United Kingdom', 'Germany', 'Japan'],
                'people_fully_vaccinated_per_hundred',
                title='Fully Vaccinated (%) — Country Comparison')
    → 返回 4 条折线的对比图
```

### 示例 3：查看美国时间序列

```
用户操作：
1. 选择指标 "Daily New Cases"
2. 选择国家 "United States"
3. 点击侧栏 "Time Series"

函数调用链：
─────────────────────────────────────────────
sidebar-state = {active_tab: 'tab-timeseries'}
    │
    ▼
render_active_tab(sidebar_state, metric, country, compare_list)
    → render_tab_content('tab-timeseries', 'new_cases_smoothed', 'United States', [...])
    → build_timeseries('new_cases_smoothed', 'United States')
    │
    ▼
make_deepdive_stats('United States', 'new_cases_smoothed', 'Daily New Cases')
    → growth_rate_analysis(df, 'United States', 'new_cases_smoothed')
    → 返回 6 个统计卡片
    │
    ▼
plot_dual_axis(df, 'United States', 'new_cases_smoothed',
               'people_fully_vaccinated_per_hundred')
    → 双轴图：左轴新增病例，右轴疫苗接种率
```

### 示例 4：查看美国增长率

```
用户操作：
1. 选择指标 "Daily New Cases"
2. 选择国家 "United States"
3. 点击侧栏 "Growth Rate"

函数调用链：
─────────────────────────────────────────────
sidebar-state = {active_tab: 'tab-growthrate'}
    │
    ▼
render_active_tab(sidebar_state, metric, country, compare_list)
    → render_tab_content('tab-growthrate', 'new_cases_smoothed', 'United States', [...])
    → build_growth_rate_page('new_cases_smoothed', 'United States')
    │
    ▼
plot_growth_rate(df, 'United States', 'new_cases_smoothed')
    → 内部调用 growth_rate_analysis(df, 'United States', 'new_cases_smoothed')
    → 上方面板：每日新增病例折线
    → 下方面板：每日增长率柱状
```

### 示例 5：移动平均分析

```
用户操作：
1. 选择指标 "Daily New Cases"
2. 选择国家 "United States"
3. 点击侧栏 "Moving Average"
4. 选择时间段 "2022 Omicron Wave"
5. 勾选 "Show Raw"

函数调用链：
─────────────────────────────────────────────
sidebar-state = {active_tab: 'tab-ma'}
ma-range = '2022_omicron'
ma-show-raw = ['raw']
    │
    ▼
update_moving_average('new_cases_smoothed', 'United States', '2022_omicron', ['raw'])
    → make_moving_average_outputs('United States', 'new_cases_smoothed',
                                  view_range='2022_omicron', show_raw=True)
    → moving_average_base_series('United States', 'new_cases_smoothed')
    → ma_range_bounds(ma_df, '2022_omicron') → (2022-01-01, 2022-12-31)
    → filter_ma_range(ma_df, '2022_omicron')
    → 生成 3 个图表 + 6 个统计卡片
```

## 7.3 模块间依赖关系

```
app_extended.py
  ├── 依赖 src/data_loader.py
  │     └── 依赖 pandas, numpy
  ├── 依赖 src/data_cleaner.py
  │     └── 依赖 pandas, numpy
  ├── 依赖 src/data_analysis.py
  │     └── 依赖 pandas, numpy
  ├── 依赖 src/advanced_analysis.py
  │     └── 依赖 pandas, numpy, sklearn
  └── 依赖 src/visualization.py
        ├── 依赖 plotly.express, plotly.graph_objects
        └── 依赖 src/data_analysis (growth_rate_analysis)
```

## 7.4 关键性能优化点

| 位置 | 优化 | 效果 |
|------|------|------|
| `app_extended.py` 启动 | Pickle 缓存 | 二次启动 0.5 秒 |
| `update_global_trend()` | `np.searchsorted` 二分查找 | 57 万行数据毫秒级过滤 |
| `global-slider` | 每月采样（`all_dates[::30]`） | 滑块从 2000+ 步减少到 ~70 步 |
| `PIPELINE_SUMMARY` | 启动时预计算 | 避免每次切换标签页重新计算 |
| `CLUSTER_CACHE` | 缓存 k=3~7 聚类结果 | 聚类标签页秒级切换 |
| `app.run(debug=False)` | 关闭 debug 模式 | 避免双重重载 |
