"""
Data Processor Module
Handles CSV parsing, column detection, data cleaning, and aggregation
for the Crime Pattern Prediction & Mapping system.
"""

import pandas as pd
import numpy as np
import re


class DataProcessor:
    """Processes uploaded crime datasets for analysis and visualization."""

    def __init__(self):
        self.df = None
        self.column_map = {}
        self.metadata = {}

    def load_csv(self, file_path):
        """Load and clean a CSV file."""
        self.df = pd.read_csv(file_path)
        self.df.columns = self.df.columns.str.strip()
        # Drop completely empty rows
        self.df.dropna(how='all', inplace=True)
        self._detect_columns()
        self._build_metadata()
        return self.metadata

    def load_dataframe(self, df):
        """Load from an existing DataFrame."""
        self.df = df.copy()
        self.df.columns = self.df.columns.str.strip()
        self.df.dropna(how='all', inplace=True)
        self._detect_columns()
        self._build_metadata()
        return self.metadata

    def _detect_columns(self):
        """Auto-detect column roles from column names."""
        cols = {c.lower().strip(): c for c in self.df.columns}
        self.column_map = {}

        # Detect STATE column
        for key in ['state/ut', 'state_ut', 'state', 'states', 'state / ut']:
            if key in cols:
                self.column_map['state'] = cols[key]
                break

        # Detect DISTRICT / CITY column
        for key in ['district', 'city', 'district_name', 'city_name']:
            if key in cols:
                self.column_map['city'] = cols[key]
                break

        # Detect AREA column
        for key in ['area', 'area_name', 'sub_district', 'region', 'locality', 'zone']:
            if key in cols:
                self.column_map['area'] = cols[key]
                break

        # Detect YEAR column
        for key in ['year', 'yr']:
            if key in cols:
                self.column_map['year'] = cols[key]
                break

        # Detect CRIME TYPE column
        for key in ['crime_head', 'crime head', 'crime type', 'crime_type', 'type_of_crime',
                     'crime', 'offence', 'crime_category', 'crime category']:
            if key in cols:
                self.column_map['crime_type'] = cols[key]
                break

        # Detect numeric case columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        year_col = self.column_map.get('year', '')

        case_keywords = ['case', 'count', 'total', 'reported', 'registered',
                         'victims', 'incidents', 'number', 'value', 'cases_reported',
                         'cases_registered']
        solved_keywords = ['solved', 'convicted', 'chargesheeted', 'charge_sheeted',
                           'chargesheet', 'disposal', 'conviction']

        # Find Cases Reported column
        for col in numeric_cols:
            col_lower = col.lower()
            if col == year_col:
                continue
            for kw in case_keywords:
                if kw in col_lower:
                    self.column_map['cases_reported'] = col
                    break
            if 'cases_reported' in self.column_map:
                break

        # Find Cases Solved/Convicted column
        for col in numeric_cols:
            col_lower = col.lower()
            if col == year_col or col == self.column_map.get('cases_reported', ''):
                continue
            for kw in solved_keywords:
                if kw in col_lower:
                    self.column_map['cases_solved'] = col
                    break
            if 'cases_solved' in self.column_map:
                break

        # Fallback: if no specific case column found, use the first numeric non-year column
        if 'cases_reported' not in self.column_map:
            for col in numeric_cols:
                if col != year_col:
                    self.column_map['cases_reported'] = col
                    break
                    
        # If STILL no cases column, it's a record-based dataset (each row = 1 case)
        if 'cases_reported' not in self.column_map:
            self.df['Cases_Reported_Synthetic'] = 1
            self.column_map['cases_reported'] = 'Cases_Reported_Synthetic'

    def _build_metadata(self):
        """Build metadata about the loaded dataset."""
        meta = {
            'total_rows': len(self.df),
            'columns': list(self.df.columns),
            'column_map': self.column_map,
            'filters': {}
        }

        if 'state' in self.column_map:
            states = sorted(self.df[self.column_map['state']].dropna().unique().tolist())
            meta['filters']['states'] = [str(s) for s in states]

        if 'city' in self.column_map:
            cities = sorted(self.df[self.column_map['city']].dropna().unique().tolist())
            meta['filters']['cities'] = [str(c) for c in cities]

        if 'crime_type' in self.column_map:
            crime_types = sorted(self.df[self.column_map['crime_type']].dropna().unique().tolist())
            meta['filters']['crime_types'] = [str(ct) for ct in crime_types]

        if 'year' in self.column_map:
            years = sorted(self.df[self.column_map['year']].dropna().unique().tolist())
            meta['filters']['years'] = [int(y) for y in years]

        self.metadata = meta

    def get_filtered_data(self, filters=None):
        """Filter the dataset based on user selections."""
        if self.df is None:
            return pd.DataFrame()

        df = self.df.copy()

        if filters:
            if filters.get('state') and filters['state'] != 'all' and 'state' in self.column_map:
                df = df[df[self.column_map['state']] == filters['state']]
            if filters.get('city') and filters['city'] != 'all' and 'city' in self.column_map:
                df = df[df[self.column_map['city']] == filters['city']]
            if filters.get('crime_type') and filters['crime_type'] != 'all' and 'crime_type' in self.column_map:
                df = df[df[self.column_map['crime_type']] == filters['crime_type']]
            if filters.get('year') and filters['year'] != 'all' and 'year' in self.column_map:
                df = df[df[self.column_map['year']] == int(filters['year'])]

        return df

    def get_crime_type_distribution(self, filters=None):
        """Get crime type distribution for pie/bar chart."""
        df = self.get_filtered_data(filters)
        if 'crime_type' not in self.column_map or 'cases_reported' not in self.column_map:
            return {'labels': [], 'values': []}

        grouped = df.groupby(self.column_map['crime_type'])[self.column_map['cases_reported']].sum()
        grouped = grouped.sort_values(ascending=False).head(15)

        return {
            'labels': grouped.index.tolist(),
            'values': [int(v) for v in grouped.values.tolist()]
        }

    def get_yearly_trend(self, filters=None):
        """Get yearly crime trend for line chart."""
        df = self.get_filtered_data(filters)
        if 'year' not in self.column_map or 'cases_reported' not in self.column_map:
            return {'labels': [], 'values': []}

        grouped = df.groupby(self.column_map['year'])[self.column_map['cases_reported']].sum()
        grouped = grouped.sort_index()

        return {
            'labels': [int(y) for y in grouped.index.tolist()],
            'values': [int(v) for v in grouped.values.tolist()]
        }

    def get_reported_vs_solved(self, filters=None):
        """Get reported vs solved comparison."""
        df = self.get_filtered_data(filters)
        result = {'labels': [], 'reported': [], 'solved': []}

        if 'year' not in self.column_map or 'cases_reported' not in self.column_map:
            return result

        year_col = self.column_map['year']
        reported_col = self.column_map['cases_reported']

        grouped_reported = df.groupby(year_col)[reported_col].sum().sort_index()
        result['labels'] = [int(y) for y in grouped_reported.index.tolist()]
        result['reported'] = [int(v) for v in grouped_reported.values.tolist()]

        if 'cases_solved' in self.column_map:
            solved_col = self.column_map['cases_solved']
            grouped_solved = df.groupby(year_col)[solved_col].sum().sort_index()
            result['solved'] = [int(v) for v in grouped_solved.values.tolist()]
        else:
            # Estimate solved as ~70% of reported
            result['solved'] = [int(v * 0.7) for v in result['reported']]

        return result

    def get_city_comparison(self, filters=None):
        """Get city-wise crime comparison."""
        df = self.get_filtered_data(filters)
        col_key = 'city' if 'city' in self.column_map else 'state'

        if col_key not in self.column_map or 'cases_reported' not in self.column_map:
            return {'labels': [], 'values': []}

        grouped = df.groupby(self.column_map[col_key])[self.column_map['cases_reported']].sum()
        grouped = grouped.sort_values(ascending=False).head(10)

        return {
            'labels': grouped.index.tolist(),
            'values': [int(v) for v in grouped.values.tolist()]
        }

    def get_stats(self, filters=None):
        """Get summary statistics."""
        df = self.get_filtered_data(filters)
        stats = {}

        if 'cases_reported' in self.column_map:
            total = df[self.column_map['cases_reported']].sum()
            stats['total_cases'] = int(total)
        else:
            stats['total_cases'] = len(df)

        if 'state' in self.column_map:
            stats['total_states'] = df[self.column_map['state']].nunique()

        if 'city' in self.column_map:
            stats['total_cities'] = df[self.column_map['city']].nunique()

        if 'crime_type' in self.column_map:
            stats['total_crime_types'] = df[self.column_map['crime_type']].nunique()

        if 'year' in self.column_map:
            stats['year_range'] = f"{int(df[self.column_map['year']].min())} - {int(df[self.column_map['year']].max())}"

        return stats

    def get_risk_zones(self, filters=None):
        """Calculate risk zones (high, moderate, low) based on crime rates."""
        df = self.get_filtered_data(filters)
        col_key = 'city' if 'city' in self.column_map else 'state'

        if col_key not in self.column_map or 'cases_reported' not in self.column_map:
            return {'high': [], 'moderate': [], 'low': []}

        grouped = df.groupby(self.column_map[col_key])[self.column_map['cases_reported']].sum()
        grouped = grouped.sort_values(ascending=False)

        if len(grouped) == 0:
            return {'high': [], 'moderate': [], 'low': []}

        q75 = grouped.quantile(0.75)
        q25 = grouped.quantile(0.25)

        high = grouped[grouped >= q75]
        moderate = grouped[(grouped >= q25) & (grouped < q75)]
        low = grouped[grouped < q25]

        return {
            'high': [{'name': str(k), 'cases': int(v)} for k, v in high.items()],
            'moderate': [{'name': str(k), 'cases': int(v)} for k, v in moderate.items()],
            'low': [{'name': str(k), 'cases': int(v)} for k, v in low.items()]
        }

    def get_high_risk_alerts(self, filters=None):
        """Generate high-risk alerts based on year-over-year growth."""
        df = self.get_filtered_data(filters)
        col_key = 'city' if 'city' in self.column_map else 'state'

        if col_key not in self.column_map or 'year' not in self.column_map or 'cases_reported' not in self.column_map:
            return []

        year_col = self.column_map['year']
        case_col = self.column_map['cases_reported']
        area_col = self.column_map[col_key]

        years = sorted(df[year_col].unique())
        if len(years) < 2:
            return []

        latest_year = years[-1]
        prev_year = years[-2]

        latest_data = df[df[year_col] == latest_year].groupby(area_col)[case_col].sum()
        prev_data = df[df[year_col] == prev_year].groupby(area_col)[case_col].sum()

        alerts = []
        for area in latest_data.index:
            if area in prev_data.index and prev_data[area] > 0:
                growth = ((latest_data[area] - prev_data[area]) / prev_data[area]) * 100
                if growth > 10:
                    alerts.append({
                        'area': str(area),
                        'growth_rate': round(float(growth), 1),
                        'latest_cases': int(latest_data[area]),
                        'previous_cases': int(prev_data[area]),
                        'risk_level': 'Critical' if growth > 30 else 'High'
                    })

        alerts.sort(key=lambda x: x['growth_rate'], reverse=True)
        return alerts[:10]

    def get_heatmap_data(self, filters=None):
        """Generate heatmap data with coordinates for Indian states/cities."""
        # Approximate coordinates for Indian states
        state_coords = {
            'ANDHRA PRADESH': [15.9129, 79.7400],
            'ARUNACHAL PRADESH': [28.2180, 94.7278],
            'ASSAM': [26.2006, 92.9376],
            'BIHAR': [25.0961, 85.3131],
            'CHHATTISGARH': [21.2787, 81.8661],
            'GOA': [15.2993, 74.1240],
            'GUJARAT': [22.2587, 71.1924],
            'HARYANA': [29.0588, 76.0856],
            'HIMACHAL PRADESH': [31.1048, 77.1734],
            'JHARKHAND': [23.6102, 85.2799],
            'KARNATAKA': [15.3173, 75.7139],
            'KERALA': [10.8505, 76.2711],
            'MADHYA PRADESH': [22.9734, 78.6569],
            'MAHARASHTRA': [19.7515, 75.7139],
            'MANIPUR': [24.6637, 93.9063],
            'MEGHALAYA': [25.4670, 91.3662],
            'MIZORAM': [23.1645, 92.9376],
            'NAGALAND': [26.1584, 94.5624],
            'ODISHA': [20.9517, 85.0985],
            'PUNJAB': [31.1471, 75.3412],
            'RAJASTHAN': [27.0238, 74.2179],
            'SIKKIM': [27.5330, 88.5122],
            'TAMIL NADU': [11.1271, 78.6569],
            'TELANGANA': [18.1124, 79.0193],
            'TRIPURA': [23.9408, 91.9882],
            'UTTAR PRADESH': [26.8467, 80.9462],
            'UTTARAKHAND': [30.0668, 79.0193],
            'WEST BENGAL': [22.9868, 87.8550],
            'A & N ISLANDS': [11.7401, 92.6586],
            'CHANDIGARH': [30.7333, 76.7794],
            'D & N HAVELI': [20.1809, 73.0169],
            'DAMAN & DIU': [20.4283, 72.8397],
            'DELHI': [28.7041, 77.1025],
            'DELHI UT': [28.7041, 77.1025],
            'LAKSHADWEEP': [10.5667, 72.6417],
            'PUDUCHERRY': [11.9416, 79.8083],
            'JAMMU & KASHMIR': [33.7782, 76.5762],
            'LADAKH': [34.1526, 77.5771],
        }

        df = self.get_filtered_data(filters)
        
        # Decide grouping level
        col_key = None
        level = None
        
        if filters and filters.get('city') and filters.get('city') != 'all' and 'area' in self.column_map:
            col_key = self.column_map['area']
            level = 'area'
        elif filters and filters.get('state') and filters.get('state') != 'all' and 'city' in self.column_map:
            col_key = self.column_map['city']
            level = 'city'
        else:
            if 'city' in self.column_map:
                col_key = self.column_map['city']
                level = 'city'
            elif 'state' in self.column_map:
                col_key = self.column_map['state']
                level = 'state'

        if not col_key or col_key not in self.column_map.values() or 'cases_reported' not in self.column_map:
            return []

        grouped = df.groupby(col_key)[self.column_map['cases_reported']].sum()

        if len(grouped) == 0:
            return []

        # Get most common crime type per area
        most_common_crimes = {}
        if 'crime_type' in self.column_map:
            try:
                crime_grouped = df.groupby([col_key, self.column_map['crime_type']])[self.column_map['cases_reported']].sum()
                for area in grouped.index:
                    if area in crime_grouped.index.levels[0]:
                        area_crimes = crime_grouped.loc[area]
                        most_common_crimes[area] = area_crimes.idxmax()
            except Exception as e:
                pass

        max_cases = grouped.max()
        min_cases = grouped.min()
        range_cases = max_cases - min_cases if max_cases != min_cases else 1

        city_coords = {
            'MUMBAI': [19.0760, 72.8777], 'PUNE': [18.5204, 73.8567], 'NAGPUR': [21.1458, 79.0882],
            'NASHIK': [19.9975, 73.7898], 'THANE': [19.2183, 72.9781], 'AURANGABAD': [19.8762, 75.3433],
            'KOLHAPUR': [16.7050, 74.2433], 'SOLAPUR': [17.6599, 75.9064], 'AMRAVATI': [20.9320, 77.7523],
            'NAVI MUMBAI': [19.0330, 73.0297], 'DELHI': [28.7041, 77.1025], 'BANGALORE': [12.9716, 77.5946],
            'CHENNAI': [13.0827, 80.2707], 'KOLKATA': [22.5726, 88.3639], 'HYDERABAD': [17.3850, 78.4867],
            'AHMEDABAD': [23.0225, 72.5714], 'JAIPUR': [26.9124, 75.7873], 'SURAT': [21.1702, 72.8311],
            'LUCKNOW': [26.8467, 80.9462], 'KANPUR': [26.4499, 80.3319], 'INDORE': [22.7196, 75.8577],
            'BHOPAL': [23.2599, 77.4126], 'PATNA': [25.5941, 85.1376], 'CHANDIGARH': [30.7333, 76.7794]
        }

        # Seed random for consistent area scatter
        np.random.seed(42)

        heatmap_points = []
        for area, cases in grouped.items():
            area_upper = str(area).upper().strip()
            coords = None
            
            if level == 'area' and filters and filters.get('city') and filters.get('city') != 'all':
                city_filter = str(filters.get('city')).upper().strip()
                base_coords = city_coords.get(city_filter)
                if base_coords:
                    # Random small scatter within ~8km of city center for "areas"
                    coords = [base_coords[0] + np.random.normal(0, 0.06), base_coords[1] + np.random.normal(0, 0.06)]

            if coords is None:
                coords = city_coords.get(area_upper) or state_coords.get(area_upper)

            if coords is None:
                # Try partial match fallback
                for city_name, city_coord in city_coords.items():
                    if area_upper in city_name or city_name in area_upper:
                        coords = city_coord
                        break
                if coords is None:
                    for state_name, state_coord in state_coords.items():
                        if area_upper in state_name or state_name in area_upper:
                            coords = state_coord
                            break

            if coords is None:
                # Assign localized random coords within India for unknown places
                coords = [20.5937 + np.random.uniform(-5, 5), 78.9629 + np.random.uniform(-5, 5)]

            intensity = (int(cases) - min_cases) / range_cases
            risk = 'high' if intensity > 0.66 else ('moderate' if intensity > 0.33 else 'low')

            heatmap_points.append({
                'name': str(area),
                'lat': coords[0],
                'lng': coords[1],
                'cases': int(cases),
                'intensity': round(float(intensity), 3),
                'risk': risk,
                'most_common_crime': str(most_common_crimes.get(area, 'Unknown'))
            })

        return heatmap_points

    def get_dataset_summary(self):
        """Get a comprehensive text summary of the dataset for the AI assistant."""
        if self.df is None:
            return "No dataset loaded."

        summary_parts = [
            f"Dataset has {len(self.df)} rows and {len(self.df.columns)} columns.",
            f"Columns: {', '.join(self.df.columns.tolist())}.",
            f"Detected mappings: {self.column_map}."
        ]

        if 'state' in self.column_map:
            states = self.df[self.column_map['state']].nunique()
            summary_parts.append(f"Number of unique states/UTs: {states}")

        if 'year' in self.column_map:
            years = sorted(self.df[self.column_map['year']].unique())
            summary_parts.append(f"Years covered: {int(min(years))} to {int(max(years))}")

        if 'cases_reported' in self.column_map:
            total = self.df[self.column_map['cases_reported']].sum()
            summary_parts.append(f"Total reported cases: {int(total):,}")

        if 'crime_type' in self.column_map:
            top_crimes = self.df.groupby(self.column_map['crime_type'])[
                self.column_map.get('cases_reported', self.df.columns[0])
            ].sum().sort_values(ascending=False).head(5)
            summary_parts.append("Top 5 crime types by reported cases:")
            for crime, count in top_crimes.items():
                summary_parts.append(f"  - {crime}: {int(count):,}")

        return "\n".join(summary_parts)
