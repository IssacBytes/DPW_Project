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
│  Step 6: 启动 Dash 应用                      │
│  app.run(host='127.0.0.1', port=8050)        │
│  ─────────────────────────────────           │
│  • 用户打开 http://127.0.0.1:8050            │
│  • 看到 8 个标签页的 GUI                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 7: 用户交互 → 回调触发                 │
│  ─────────────────────────────────           │
│  • 选择指标 → global-metric 更新             │
│  • 选择国家 → global-country 更新            │
│  • 切换标签页 → main-tabs 更新               │
│  • 拖动滑块 → global-slider 更新             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 8: 数据分析                            │
│  ─────────────────────────────────           │
│  • descriptive_stats() → 统计卡片            │
│  • country_trend() → 国家趋势数据            │
│  • compare_countries() → 对比数据            │
│  • top_countries() → 排名数据                │
│  • growth_rate_analysis() → 增长率数据       │
│  • continent_comparison() → 大洲汇总         │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 9: 可视化生成                          │
│  ─────────────────────────────────           │
│  • plot_choropleth_map() → 世界地图          │
│  • plot_trend_line() → 趋势折线图            │
│  • plot_bar_chart() → 排名柱状图             │
│  • plot_dual_axis() → 双轴图                 │
│  • plot_growth_rate() → 增长率图             │
│  • plot_scatter() → 散点图                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Step 10: GUI 展示                           │
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
3. 切换到 "Global Trends" 标签页
4. 拖动时间轴滑块到 2022-01

函数调用链：
─────────────────────────────────────────────
global-metric = 'new_cases_smoothed'
global-country = 'United States'
main-tabs = 'tab-global'
global-slider = 42 (对应 2022-01-15)
    │
    ▼
render_tab('tab-global', 'new_cases_smoothed', 'United States', [...])
    → build_global_tab('new_cases_smoothed')
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
4. 切换到 "Country Comparison" 标签页

函数调用链：
─────────────────────────────────────────────
global-metric = 'people_fully_vaccinated_per_hundred'
global-country = 'United States'
global-compare = ['United Kingdom', 'Germany', 'Japan']
main-tabs = 'tab-compare'
    │
    ▼
render_tab('tab-compare', 'people_fully_vaccinated_per_hundred', 
           'United States', ['United Kingdom', 'Germany', 'Japan'])
    → build_compare_tab('people_fully_vaccinated_per_hundred', 
                        'United States', ['United Kingdom', 'Germany', 'Japan'])
    │
    ▼
plot_trend_line(df, ['United States', 'United Kingdom', 'Germany', 'Japan'],
                'people_fully_vaccinated_per_hundred',
                title='Fully Vaccinated (%) — Country Comparison')
    → 返回 4 条折线的对比图
```

### 示例 3：查看美国疫情峰值

```
用户操作：
1. 选择指标 "Daily New Cases"
2. 选择国家 "United States"
3. 切换到 "Country Deep Dive" 标签页

函数调用链：
─────────────────────────────────────────────
main-tabs = 'tab-deepdive'
    │
    ▼
render_tab('tab-deepdive', 'new_cases_smoothed', 'United States', [...])
    → build_deepdive_tab('new_cases_smoothed', 'United States')
    │
    ▼
plot_dual_axis(df, 'United States', 'new_cases_smoothed', 
               'people_fully_vaccinated_per_hundred')
    → 双轴图：左轴新增病例，右轴疫苗接种率
    │
    ▼
plot_growth_rate(df, 'United States', 'new_cases_smoothed')
    → 内部调用 growth_rate_analysis(df, 'United States', 'new_cases_smoothed')
    → 上方面板：每日新增病例折线
    → 下方面板：每日增长率柱状
```

## 7.3 模块间依赖关系

```
app.py
  ├── 依赖 src/data_loader.py
  │     └── 依赖 pandas, numpy
  ├── 依赖 src/data_cleaner.py
  │     └── 依赖 pandas, numpy
  ├── 依赖 src/data_analysis.py
  │     └── 依赖 pandas, numpy
  └── 依赖 src/visualization.py
        ├── 依赖 plotly.express, plotly.graph_objects
        └── 依赖 src/data_analysis (growth_rate_analysis)
```

## 7.4 关键性能优化点

| 位置 | 优化 | 效果 |
|------|------|------|
| `app.py` 启动 | Pickle 缓存 | 二次启动 0.5 秒 |
| `update_global_trend()` | `np.searchsorted` 二分查找 | 57 万行数据毫秒级过滤 |
| `global-slider` | 每月采样（`all_dates[::30]`） | 滑块从 2000+ 步减少到 ~70 步 |
| `app.run(debug=False)` | 关闭 debug 模式 | 避免双重重载 |
