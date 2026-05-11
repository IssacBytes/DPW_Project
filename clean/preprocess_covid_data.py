"""
COVID-19 data preprocessing script for a university group project.

What this script does:
1. Loads a CSV file with pandas.
2. Explores the dataset structure.
3. Checks common data quality problems.
4. Cleans and standardizes the data.
5. Prepares analysis-friendly columns such as daily increase,
   growth rate, and 7-day moving average.
6. Saves a cleaned CSV file for later analysis and visualization.

This script is intentionally modular and easy to explain in a presentation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


class CovidDataPreprocessor:
    """Reusable preprocessing workflow for COVID-19 time-series data."""

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None

    @staticmethod
    def standardize_column_names(columns: Iterable[str]) -> list[str]:
        """
        Make column names easier to work with.

        Example:
        'Total Cases' -> 'total_cases'
        """
        clean_columns = []
        for column in columns:
            clean_name = str(column).strip().lower().replace(" ", "_").replace("-", "_")
            clean_columns.append(clean_name)
        return clean_columns

    @staticmethod
    def find_first_existing_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
        """Return the first matching column name from a list of possible names."""
        for column in candidates:
            if column in df.columns:
                return column
        return None

    def load_data(self) -> pd.DataFrame:
        """Load the CSV dataset into a pandas DataFrame."""
        self.data = pd.read_csv(self.file_path)
        self.data.columns = self.standardize_column_names(self.data.columns)
        return self.data

    def explore_data(self, sample_rows: int = 5) -> None:
        """
        Print the main structure of the dataset.

        This is useful for understanding the dataset before cleaning it.
        """
        if self.data is None:
            raise ValueError("Data has not been loaded yet.")

        print("\n" + "=" * 70)
        print("1. INITIAL DATA EXPLORATION")
        print("=" * 70)
        print(f"Dataset shape: {self.data.shape}")
        print("\nColumn names:")
        print(self.data.columns.tolist())
        print("\nData types:")
        print(self.data.dtypes)
        print(f"\nSample rows (first {sample_rows} rows):")
        print(self.data.head(sample_rows))
        print("\nSummary statistics for numeric columns:")
        print(self.data.describe(include="number").transpose())
        print("\nSummary statistics for all columns:")
        print(self.data.describe(include="all").transpose())

    def check_data_quality(self) -> dict:
        """
        Check for common data quality issues and return the results.

        Checks include:
        - missing values
        - duplicate rows
        - invalid dates
        - numeric columns stored as text
        - inconsistent text formatting
        """
        if self.data is None:
            raise ValueError("Data has not been loaded yet.")

        df = self.data.copy()

        date_column = self.find_first_existing_column(df, ["date", "report_date", "day"])
        country_column = self.find_first_existing_column(df, ["country", "location", "region"])

        # These are common numeric fields in COVID-19 datasets.
        possible_numeric_columns = [
            "total_cases",
            "new_cases",
            "new_cases_smoothed",
            "total_deaths",
            "new_deaths",
            "new_deaths_smoothed",
            "total_tests",
            "new_tests",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "total_boosters",
            "population",
            "reproduction_rate",
            "stringency_index",
        ]
        numeric_columns = [column for column in possible_numeric_columns if column in df.columns]

        quality_report = {
            "missing_values": df.isna().sum().sort_values(ascending=False),
            "duplicate_rows": int(df.duplicated().sum()),
            "invalid_dates": 0,
            "numeric_columns_stored_as_text": [],
            "inconsistent_country_format_examples": [],
        }

        if date_column:
            parsed_dates = pd.to_datetime(df[date_column], errors="coerce")
            quality_report["invalid_dates"] = int(parsed_dates.isna().sum())

        for column in numeric_columns:
            if not pd.api.types.is_numeric_dtype(df[column]):
                quality_report["numeric_columns_stored_as_text"].append(column)

        if country_column and pd.api.types.is_string_dtype(df[country_column]):
            original_values = df[country_column].dropna().astype("string")
            cleaned_values = original_values.str.strip()
            inconsistent_mask = original_values != cleaned_values
            quality_report["inconsistent_country_format_examples"] = (
                original_values[inconsistent_mask].head(10).astype(str).tolist()
            )

        print("\n" + "=" * 70)
        print("2. DATA QUALITY CHECKS")
        print("=" * 70)
        print("\nMissing values per column:")
        print(quality_report["missing_values"])
        print(f"\nDuplicate rows: {quality_report['duplicate_rows']}")
        print(f"Invalid dates: {quality_report['invalid_dates']}")
        print(
            "\nNumeric columns stored as text:",
            quality_report["numeric_columns_stored_as_text"] or "None detected",
        )
        print(
            "\nInconsistent country format examples:",
            quality_report["inconsistent_country_format_examples"] or "None detected",
        )

        return quality_report

    def clean_data(self) -> pd.DataFrame:
        """
        Clean the dataset so it is ready for analysis.

        Cleaning decisions are chosen to be easy to explain:
        - remove exact duplicates
        - standardize text columns
        - convert dates and numbers to correct data types
        - drop rows missing essential identifiers
        - remove impossible negative cumulative values
        """
        if self.data is None:
            raise ValueError("Data has not been loaded yet.")

        df = self.data.copy()

        # Standardize column names once more in case the DataFrame was replaced.
        df.columns = self.standardize_column_names(df.columns)

        date_column = self.find_first_existing_column(df, ["date", "report_date", "day"])
        country_column = self.find_first_existing_column(df, ["country", "location", "region"])

        # Remove exact duplicate rows.
        df = df.drop_duplicates()

        # Clean text columns by stripping extra spaces.
        text_columns = df.select_dtypes(include=["object", "string"]).columns
        for column in text_columns:
            df[column] = df[column].astype("string").str.strip()
            df.loc[df[column].isin(["", "nan", "None"]), column] = pd.NA

        # Convert the date column to datetime.
        if date_column:
            df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

        # Convert likely numeric columns to numeric format if present.
        possible_numeric_columns = [
            "total_cases",
            "new_cases",
            "new_cases_smoothed",
            "total_cases_per_million",
            "new_cases_per_million",
            "new_cases_smoothed_per_million",
            "total_deaths",
            "new_deaths",
            "new_deaths_smoothed",
            "total_deaths_per_million",
            "new_deaths_per_million",
            "new_deaths_smoothed_per_million",
            "excess_mortality",
            "excess_mortality_cumulative",
            "excess_mortality_cumulative_absolute",
            "excess_mortality_cumulative_per_million",
            "hosp_patients",
            "hosp_patients_per_million",
            "weekly_hosp_admissions",
            "weekly_hosp_admissions_per_million",
            "icu_patients",
            "icu_patients_per_million",
            "weekly_icu_admissions",
            "weekly_icu_admissions_per_million",
            "stringency_index",
            "reproduction_rate",
            "total_tests",
            "new_tests",
            "total_tests_per_thousand",
            "new_tests_per_thousand",
            "new_tests_smoothed",
            "new_tests_smoothed_per_thousand",
            "positive_rate",
            "tests_per_case",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "total_boosters",
            "new_vaccinations",
            "new_vaccinations_smoothed",
            "total_vaccinations_per_hundred",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "total_boosters_per_hundred",
            "new_vaccinations_smoothed_per_million",
            "new_people_vaccinated_smoothed",
            "new_people_vaccinated_smoothed_per_hundred",
            "population",
            "population_density",
            "median_age",
            "life_expectancy",
            "gdp_per_capita",
            "extreme_poverty",
            "diabetes_prevalence",
            "handwashing_facilities",
            "hospital_beds_per_thousand",
            "human_development_index",
        ]
        numeric_columns = [column for column in possible_numeric_columns if column in df.columns]

        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        # Remove rows that do not have the key identifiers needed for trend analysis.
        required_columns = [column for column in [country_column, date_column] if column is not None]
        if required_columns:
            df = df.dropna(subset=required_columns)

        # Remove impossible negative values for cumulative metrics.
        cumulative_columns = [
            column
            for column in [
                "total_cases",
                "total_deaths",
                "total_tests",
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
                "population",
            ]
            if column in df.columns
        ]
        for column in cumulative_columns:
            df = df[(df[column].isna()) | (df[column] >= 0)]

        # For key flow variables, missing values are often treated as zero for daily reporting.
        daily_columns = [
            column
            for column in [
                "new_cases",
                "new_deaths",
                "new_tests",
                "new_vaccinations",
            ]
            if column in df.columns
        ]
        for column in daily_columns:
            df[column] = df[column].fillna(0)

        self.cleaned_data = df
        return df

    def prepare_for_analysis(
        self,
        countries: Optional[list[str]] = None,
        variables: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Prepare a cleaned dataset for later trend analysis and visualization.

        Optional filters:
        - countries: keep only selected countries
        - variables: keep only selected analysis columns plus key identifiers
        """
        if self.cleaned_data is None:
            raise ValueError("Data has not been cleaned yet.")

        df = self.cleaned_data.copy()

        date_column = self.find_first_existing_column(df, ["date", "report_date", "day"])
        country_column = self.find_first_existing_column(df, ["country", "location", "region"])

        if country_column and countries:
            country_lookup = {country.strip().lower() for country in countries}
            df = df[df[country_column].str.lower().isin(country_lookup)]

        # Sort data to support time-series calculations.
        sort_columns = [column for column in [country_column, date_column] if column is not None]
        if sort_columns:
            df = df.sort_values(sort_columns).reset_index(drop=True)

        # Create derived columns that are useful for later analysis.
        if country_column and "total_cases" in df.columns:
            df["daily_increase_from_total_cases"] = df.groupby(country_column)["total_cases"].diff()

        if country_column and "new_cases" in df.columns:
            previous_day_cases = df.groupby(country_column)["new_cases"].shift(1)
            df["new_cases_growth_rate"] = (
                (df["new_cases"] - previous_day_cases) / previous_day_cases.replace(0, pd.NA)
            ) * 100
            df["new_cases_7day_moving_avg"] = (
                df.groupby(country_column)["new_cases"]
                .transform(lambda series: series.rolling(window=7, min_periods=1).mean())
            )

        if country_column and "new_deaths" in df.columns:
            df["new_deaths_7day_moving_avg"] = (
                df.groupby(country_column)["new_deaths"]
                .transform(lambda series: series.rolling(window=7, min_periods=1).mean())
            )

        # Keep important columns for analysis if the user requests a smaller output.
        important_columns = [
            column
            for column in [
                country_column,
                "code",
                "continent",
                date_column,
                "population",
                "total_cases",
                "new_cases",
                "new_cases_smoothed",
                "daily_increase_from_total_cases",
                "new_cases_growth_rate",
                "new_cases_7day_moving_avg",
                "total_deaths",
                "new_deaths",
                "new_deaths_7day_moving_avg",
                "total_tests",
                "new_tests",
                "total_vaccinations",
                "new_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "stringency_index",
                "reproduction_rate",
            ]
            if column is not None and column in df.columns
        ]

        if variables:
            requested_columns = [
                column
                for column in variables
                if column in df.columns
            ]
            identifier_columns = [
                column for column in [country_column, date_column, "code", "continent"] if column in df.columns
            ]
            final_columns = list(dict.fromkeys(identifier_columns + requested_columns))
            df = df[final_columns]
        else:
            df = df[important_columns]

        self.cleaned_data = df
        return df

    def save_data(self, output_path: str | Path) -> Path:
        """Save the cleaned dataset as a new CSV file."""
        if self.cleaned_data is None:
            raise ValueError("There is no cleaned data to save yet.")

        output_path = Path(output_path)
        self.cleaned_data.to_csv(output_path, index=False)
        print(f"\nCleaned dataset saved to: {output_path}")
        return output_path

    def run_pipeline(
        self,
        output_path: str | Path,
        countries: Optional[list[str]] = None,
        variables: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Run the full preprocessing pipeline in order."""
        self.load_data()
        self.explore_data()
        self.check_data_quality()
        self.clean_data()
        final_df = self.prepare_for_analysis(countries=countries, variables=variables)
        self.save_data(output_path)
        return final_df


def parse_list_argument(value: Optional[str]) -> Optional[list[str]]:
    """Convert a comma-separated string into a clean Python list."""
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    """Parse command-line arguments and run the preprocessing workflow."""
    parser = argparse.ArgumentParser(description="Preprocess a COVID-19 dataset with pandas.")
    parser.add_argument(
        "--input",
        default="compact.csv",
        help="Path to the raw input CSV file.",
    )
    parser.add_argument(
        "--output",
        default="compact_cleaned.csv",
        help="Path for the cleaned output CSV file.",
    )
    parser.add_argument(
        "--countries",
        default=None,
        help="Optional comma-separated list of countries to keep, for example: Afghanistan,Japan,Brazil",
    )
    parser.add_argument(
        "--variables",
        default=None,
        help="Optional comma-separated list of analysis columns to keep.",
    )

    args = parser.parse_args()

    processor = CovidDataPreprocessor(args.input)
    processor.run_pipeline(
        output_path=args.output,
        countries=parse_list_argument(args.countries),
        variables=parse_list_argument(args.variables),
    )


if __name__ == "__main__":
    main()
