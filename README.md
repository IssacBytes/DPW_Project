# COVID-19 Data Explorer

COVID-19 Data Explorer is an interactive Dash and Plotly dashboard for exploring the Our World in Data COVID-19 dataset. The current application entry point is `app_extended.py`. It provides data loading, cleaning, summary statistics, map-based global trends, country and continent comparison, time-series analysis, relationship analysis, and advanced analytical views.

## Project Overview

The project is a browser-based Python web application. It loads the COVID-19 CSV dataset, preprocesses it with reusable cleaning code, caches the cleaned DataFrame for faster startup, and renders interactive analytical pages through Dash callbacks.

Main technologies:

| Technology | Purpose |
| --- | --- |
| Dash | Web application framework |
| dash-bootstrap-components | UI components and layout support |
| Plotly | Interactive charts and maps |
| pandas | Data loading, cleaning, grouping, and tabular analysis |
| numpy | Numeric calculation and fast filtering |
| scikit-learn | Standardization and KMeans clustering |

## Dataset

The app expects the dataset file to be available at the project root:

```text
compact.csv
```

Current dataset characteristics used by the project:

| Item | Value |
| --- | --- |
| Source | Our World in Data COVID-19 dataset |
| Rows | 570,606 |
| Countries or regions | 262 |
| Date range | 2020-01-01 to 2026-02-22 |
| Main cache file | `data_cache.pkl` |

`data_cache.pkl` is generated from `compact.csv` after preprocessing. If the source dataset is changed, delete `data_cache.pkl` and restart the application so the cache can be rebuilt.

## Submission Notes

If the submission file size exceeds the upload limit:

- The original dataset should not be included.
- A cleaned dataset is optional.
- The data cleaning code must still be included. In this project, the cleaning workflow is implemented in `src/data_cleaner.py`.
- `data_cache.pkl` is a generated cache file and can be omitted from submission. It can be rebuilt from `compact.csv`.
- No pre-trained model is used in this project.
- No self-trained or fine-tuned model is used. Clustering is computed at runtime with KMeans from scikit-learn.
- External package references are listed in the "External Package References" section below.

The final report must specify the contribution of every group member. This README does not invent member names or contribution percentages; those details should be filled in the report by the group.

Only the group leader should submit the final shared submission. If a newer version is uploaded, do not remove the existing submission unless the course platform explicitly requires it.

## Environment Setup

Recommended environment:

- Windows 10 or later
- Python 3.10 or later
- A local browser such as Chrome, Edge, or Firefox

Create and activate a virtual environment from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

The dependency file currently contains:

```text
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
dash>=2.14.0
dash-bootstrap-components>=1.5.0
scikit-learn>=1.3.0
gunicorn
```

## Running the Application

### Option 1: Windows launcher

Double-click:

```text
run_extended.bat
```

The script activates `.venv`, starts the Dash server, and opens the browser when the server is ready.

### Option 2: Command line

Run from the project root:

```powershell
.\.venv\Scripts\python.exe app_extended.py
```

Then open:

```text
http://127.0.0.1:8051
```

The app runs with:

```python
app.run(debug=False, host='127.0.0.1', port=8051)
```

## Online Deployment

The deployable Dash entry point is `app.py`. It exposes the Flask server as `server = app.server`, so production platforms can start the app with Gunicorn.

`compact.csv` is not committed to the repository because it is a large data file. For local runs, place `compact.csv` in the project root manually. For Render, set `DATA_URL` to a direct download link for `compact.csv`; the app will download it automatically when `data_cache.pkl` is not present.

### Render deployment configuration

- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:server`
- Branch: `web_version`
- Main app entry: `app.py`
- Environment Variable: `DATA_URL=<direct compact.csv download URL>`

### Local deployment test

Make sure `compact.csv` exists in the project root, then run:

Run from the project root:

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8050
```

For cloud-style local testing, set `PORT` before starting the app:

```powershell
$env:PORT=8055
python app.py
```

Then open `http://127.0.0.1:8055`.

### Custom domain

After the Render service is live, add a Custom Domain in Render, for example:

```text
dpw.issacbytes.com
```

In Cloudflare DNS, add a CNAME record:

```text
Name: dpw
Target: Render-provided target domain
Proxy status: DNS only, or as required by Render
```

## First Launch and Cache Behavior

On first launch, the app loads `compact.csv`, cleans the data, prepares derived fields, and writes `data_cache.pkl`. Later launches use the cache for faster startup.

To force a full reload:

1. Stop the running Dash server.
2. Delete `data_cache.pkl`.
3. Start `app_extended.py` again.

## Project Structure

```text
covid19-data-explorer/
|-- app_extended.py              # Main Dash application
|-- run_extended.bat             # Windows launcher for the extended app
|-- requirements.txt             # Python dependencies
|-- compact.csv                  # Required source dataset, if included locally
|-- compact_cleaned.csv          # Optional cleaned dataset
|-- data_cache.pkl               # Generated preprocessing cache
|-- assets/
|   `-- animations.css           # UI animation and styling support
|-- src/
|   |-- data_loader.py           # Dataset loading and metadata helpers
|   |-- data_cleaner.py          # Data preprocessing and cleaning workflow
|   |-- data_analysis.py         # Descriptive statistics and ranking helpers
|   |-- advanced_analysis.py     # Moving average, anomalies, CFR, lag, clustering
|   `-- visualization.py         # Plotly chart and map generation
|-- docs/                        # Design and module documentation
`-- tools/                       # Report/document generation helper scripts
```

## Application Guide

The extended GUI uses a collapsible sidebar. Global controls at the top select the main metric, primary country, and comparison countries. Some pages use all global controls, while pages such as Fatality Trend and Clustering use fixed analysis inputs where the global metric is not needed.

### Overview

**Global Trends**

- Displays a world choropleth map for the selected metric and date.
- Includes a timeline slider and Play button for observing global changes over time.
- Shows global summary cards and a trend chart for selected comparison countries.

**Summary Statistics**

- Shows dataset-level summary cards such as total countries, date range, row count, and global total for the selected metric.
- Includes key metrics and a filterable country summary table.

**Pandemic Timeline**

- Documents the data pipeline from loading to cleaning.
- Shows source file information, cleaning summary, and column metadata.

### Comparison Analysis

**Country Comparison**

- Compares the selected country with selected comparison countries.
- Uses a multi-line time-series chart for the selected metric.

**Continent Comparison**

- Aggregates the selected metric by continent.
- Supports continent-level comparison rather than country-level comparison.

**Rankings**

- Shows the top countries for the selected metric.
- Uses a horizontal bar chart colored by continent.

### Trend Analysis

**Time Series**

- Focuses on the selected country and metric over time.
- Includes summary cards for the displayed series.

**Moving Average**

- Uses a more interpretable daily baseline for smoothed or cumulative metrics.
- Shows trend overview, moving-average window comparison, momentum, and peak summary.
- Helps identify whether the short-term trend is rising, falling, or stable.

**Growth Rate**

- Shows value and growth-rate views for the selected country and metric.
- Adds summary cards for the displayed trend data.

**Fatality Trend**

- Analyzes case fatality rate behavior using cumulative CFR and recent fatality ratio.
- Supports comparison countries where relevant.
- This page is independent of the global metric selector because fatality rate is computed from cases and deaths.

### Relationship Analysis

**Correlation**

- Compares two selected indicators in a scatter plot.
- Supports coloring countries by continent, population group, GDP level, median age group, HDI level, or life expectancy group.
- Includes a simple analysis process and conclusion text in English.

**Lead-Lag Analysis**

- Computes cross-lag correlation between two selected indicators for the selected country.
- Helps explore whether one signal tends to lead or lag another signal.
- Includes a simple analysis process and conclusion text in English.

### Advanced Analytics

**Clustering**

- Groups countries using KMeans based on latest per-country metrics.
- Uses total cases per million, total deaths per million, fully vaccinated percentage, and population.
- Provides cluster scatter output and cluster summary cards.

**Anomaly Detection**

- Detects unusual spikes or drops using rolling mean and rolling standard deviation.
- Lets the user adjust rolling window and anomaly threshold.

## Data Cleaning Workflow

The cleaning workflow is implemented in `src/data_cleaner.py` through `CovidDataPreprocessor`.

Main steps include:

- Load CSV data with pandas.
- Standardize column names.
- Remove duplicate rows.
- Trim and standardize text fields.
- Convert date fields to datetime.
- Convert numeric fields to numeric types.
- Drop rows missing essential identifiers.
- Remove impossible negative cumulative values.
- Prepare a cleaned DataFrame for dashboard analysis.

## External Package References

This project uses external open-source packages:

- pandas: https://pandas.pydata.org/
- numpy: https://numpy.org/
- Plotly: https://plotly.com/python/
- Dash: https://dash.plotly.com/
- dash-bootstrap-components: https://dash-bootstrap-components.opensource.faculty.ai/
- scikit-learn: https://scikit-learn.org/

Dataset reference:

- Our World in Data COVID-19 dataset: https://ourworldindata.org/coronavirus

## Troubleshooting

**`compact.csv` is missing**

Place `compact.csv` in the project root, or update `DATA_PATH` in `app_extended.py` to point to the dataset location.

**The app still shows old data**

Stop the server, delete `data_cache.pkl`, and restart the app.

**Port 8051 is already in use**

Stop the other process using the port, or change the port in the final `app.run(...)` call in `app_extended.py`.

**Dependencies are missing**

Activate the virtual environment and run:

```powershell
pip install -r requirements.txt
```

**The browser does not show the latest UI**

Refresh the browser page. If needed, stop and restart `app_extended.py`.

## Verification Commands

Run a syntax check:

```powershell
.\.venv\Scripts\python.exe -m py_compile app_extended.py
```

Start the app:

```powershell
.\.venv\Scripts\python.exe app_extended.py
```

Open:

```text
http://127.0.0.1:8051
```
