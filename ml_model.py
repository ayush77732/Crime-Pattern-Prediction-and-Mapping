"""
ML Model Module
Handles crime prediction using ensemble methods (Random Forest + Gradient Boosting).
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')


class CrimePredictor:
    """Ensemble ML model for crime prediction and forecasting."""

    def __init__(self):
        self.rf_model = RandomForestRegressor(
            n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
        )
        self.gb_model = GradientBoostingRegressor(
            n_estimators=150, max_depth=8, learning_rate=0.1, random_state=42
        )
        self.label_encoders = {}
        self.is_trained = False
        self.training_data = None
        self.feature_columns = []
        self.target_column = None
        self.metrics = {}

    def train(self, df, column_map):
        """Train the ensemble model on the provided dataset."""
        if df is None or len(df) == 0:
            return {'status': 'error', 'message': 'No data provided'}

        try:
            self.training_data = df.copy()
            self.target_column = column_map.get('cases_reported')

            if not self.target_column or self.target_column not in df.columns:
                return {'status': 'error', 'message': 'No target column found'}

            # Prepare features
            feature_cols = []
            categorical_cols = []

            if 'state' in column_map and column_map['state'] in df.columns:
                feature_cols.append(column_map['state'])
                categorical_cols.append(column_map['state'])

            if 'city' in column_map and column_map['city'] in df.columns:
                feature_cols.append(column_map['city'])
                categorical_cols.append(column_map['city'])

            if 'crime_type' in column_map and column_map['crime_type'] in df.columns:
                feature_cols.append(column_map['crime_type'])
                categorical_cols.append(column_map['crime_type'])

            if 'year' in column_map and column_map['year'] in df.columns:
                feature_cols.append(column_map['year'])

            if len(feature_cols) == 0:
                return {'status': 'error', 'message': 'No feature columns detected'}

            self.feature_columns = feature_cols

            # Prepare training data
            train_df = df[feature_cols + [self.target_column]].dropna()

            if len(train_df) < 10:
                return {'status': 'error', 'message': 'Not enough data to train'}

            # Encode categorical columns
            self.label_encoders = {}
            X = train_df[feature_cols].copy()

            for col in categorical_cols:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                self.label_encoders[col] = le

            y = train_df[self.target_column].values.astype(float)

            # Train Random Forest
            self.rf_model.fit(X, y)

            # Train Gradient Boosting
            self.gb_model.fit(X, y)

            # Evaluate with cross-validation
            rf_scores = cross_val_score(self.rf_model, X, y, cv=min(5, len(X)), scoring='r2')
            gb_scores = cross_val_score(self.gb_model, X, y, cv=min(5, len(X)), scoring='r2')

            # Ensemble predictions
            rf_pred = self.rf_model.predict(X)
            gb_pred = self.gb_model.predict(X)
            ensemble_pred = (rf_pred + gb_pred) / 2

            self.metrics = {
                'r2_score': round(float(r2_score(y, ensemble_pred)), 4),
                'mae': round(float(mean_absolute_error(y, ensemble_pred)), 2),
                'rf_cv_mean': round(float(rf_scores.mean()), 4),
                'gb_cv_mean': round(float(gb_scores.mean()), 4),
                'training_samples': len(X)
            }

            self.is_trained = True
            return {'status': 'success', 'metrics': self.metrics}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def predict(self, filters, column_map):
        """Predict crime cases for given filters."""
        if not self.is_trained:
            return self._fallback_prediction(filters, column_map)

        try:
            # Build input features
            input_data = {}
            for col in self.feature_columns:
                col_role = None
                for role, mapped_col in column_map.items():
                    if mapped_col == col:
                        col_role = role
                        break

                if col_role and filters.get(col_role) and filters[col_role] != 'all':
                    input_data[col] = filters[col_role]
                else:
                    input_data[col] = None

            # If any required feature is missing, use fallback
            if any(v is None for v in input_data.values()):
                return self._fallback_prediction(filters, column_map)

            X_input = pd.DataFrame([input_data])

            # Encode
            for col in self.label_encoders:
                if col in X_input.columns:
                    le = self.label_encoders[col]
                    val = str(X_input[col].iloc[0])
                    if val in le.classes_:
                        X_input[col] = le.transform([val])
                    else:
                        return self._fallback_prediction(filters, column_map)

            rf_pred = self.rf_model.predict(X_input)[0]
            gb_pred = self.gb_model.predict(X_input)[0]
            prediction = (rf_pred + gb_pred) / 2

            return {
                'predicted_cases': max(0, int(round(prediction))),
                'confidence': round(float(max(0, self.metrics.get('r2_score', 0.5)) * 100), 1),
                'method': 'ML Ensemble (Random Forest + Gradient Boosting)'
            }

        except Exception:
            return self._fallback_prediction(filters, column_map)

    def _fallback_prediction(self, filters, column_map):
        """Fallback prediction using historical data trends."""
        if self.training_data is None:
            return {'predicted_cases': 0, 'confidence': 0, 'method': 'No data available'}

        df = self.training_data.copy()

        # Apply filters
        if filters.get('state') and filters['state'] != 'all' and 'state' in column_map:
            df = df[df[column_map['state']] == filters['state']]
        if filters.get('city') and filters['city'] != 'all' and 'city' in column_map:
            df = df[df[column_map['city']] == filters['city']]
        if filters.get('crime_type') and filters['crime_type'] != 'all' and 'crime_type' in column_map:
            df = df[df[column_map['crime_type']] == filters['crime_type']]

        if len(df) == 0:
            return {'predicted_cases': 0, 'confidence': 0, 'method': 'No matching data'}

        cases_col = column_map.get('cases_reported')
        if cases_col and cases_col in df.columns:
            avg = df[cases_col].mean()
            return {
                'predicted_cases': max(0, int(round(avg))),
                'confidence': 45.0,
                'method': 'Historical Average (Fallback)'
            }

        return {'predicted_cases': 0, 'confidence': 0, 'method': 'Insufficient data'}

    def forecast_trend(self, df, column_map, future_years=3):
        """Forecast crime trends for future years."""
        if 'year' not in column_map or 'cases_reported' not in column_map:
            return {'years': [], 'actual': [], 'predicted': [], 'lower_bound': [], 'upper_bound': []}

        year_col = column_map['year']
        case_col = column_map['cases_reported']

        yearly = df.groupby(year_col)[case_col].sum().sort_index()

        if len(yearly) < 2:
            return {'years': [], 'actual': [], 'predicted': [], 'lower_bound': [], 'upper_bound': []}

        years = yearly.index.tolist()
        values = yearly.values.tolist()

        # Simple trend analysis with linear regression
        x = np.array(range(len(years))).reshape(-1, 1)
        y = np.array(values)

        from sklearn.linear_model import LinearRegression
        lr = LinearRegression()
        lr.fit(x, y)

        # Predict future
        last_year = int(max(years))
        future_x = np.array(range(len(years), len(years) + future_years)).reshape(-1, 1)
        future_pred = lr.predict(future_x)

        # Calculate confidence interval
        residuals = y - lr.predict(x)
        std_err = np.std(residuals)

        result = {
            'years': [int(y) for y in years] + [last_year + i + 1 for i in range(future_years)],
            'actual': [int(v) for v in values] + [None] * future_years,
            'predicted': [None] * len(years) + [max(0, int(p)) for p in future_pred],
            'lower_bound': [None] * len(years) + [max(0, int(p - 1.96 * std_err)) for p in future_pred],
            'upper_bound': [None] * len(years) + [int(p + 1.96 * std_err) for p in future_pred]
        }

        return result

    def get_hotspot_prediction(self, df, column_map):
        """Predict future crime hotspots based on growth trends."""
        col_key = 'city' if 'city' in column_map else 'state'

        if col_key not in column_map or 'year' not in column_map or 'cases_reported' not in column_map:
            return []

        year_col = column_map['year']
        case_col = column_map['cases_reported']
        area_col = column_map[col_key]

        years = sorted(df[year_col].unique())
        if len(years) < 2:
            return []

        hotspots = []
        areas = df[area_col].unique()

        for area in areas:
            area_data = df[df[area_col] == area].groupby(year_col)[case_col].sum().sort_index()

            if len(area_data) < 2:
                continue

            # Calculate trend
            x = np.array(range(len(area_data))).reshape(-1, 1)
            y = area_data.values

            from sklearn.linear_model import LinearRegression
            lr = LinearRegression()
            lr.fit(x, y)

            slope = lr.coef_[0]
            current = area_data.iloc[-1]
            predicted_next = max(0, lr.predict([[len(area_data)]])[0])
            growth_rate = ((predicted_next - current) / current * 100) if current > 0 else 0

            risk_score = min(100, max(0, 50 + growth_rate))

            hotspots.append({
                'area': str(area),
                'current_cases': int(current),
                'predicted_cases': int(predicted_next),
                'growth_rate': round(float(growth_rate), 1),
                'risk_score': round(float(risk_score), 1),
                'trend': 'increasing' if slope > 0 else 'decreasing'
            })

        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        return hotspots[:15]
