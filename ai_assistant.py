"""
AI Assistant Module
Provides intelligent, data-driven answers about crime patterns,
chart explanations, predictions, and recommendations.
"""

import re
import random


class AIAssistant:
    """AI Assistant for Crime Pattern Prediction system."""

    def __init__(self):
        self.data_processor = None
        self.predictor = None
        self.context = {}

    def set_context(self, data_processor, predictor=None):
        """Set the data context for the assistant."""
        self.data_processor = data_processor
        self.predictor = predictor

    def answer(self, question, filters=None):
        """Answer a user question about the crime data."""
        if not self.data_processor or self.data_processor.df is None:
            return self._general_answer(question)

        question_lower = question.lower().strip()

        # Route to specific handlers
        if any(kw in question_lower for kw in ['chart', 'graph', 'plot', 'diagram', 'visualization']):
            return self._explain_charts(question_lower, filters)

        if any(kw in question_lower for kw in ['trend', 'increase', 'decrease', 'growing', 'declining', 'pattern']):
            return self._explain_trends(question_lower, filters)

        if any(kw in question_lower for kw in ['hotspot', 'danger', 'unsafe', 'risky', 'high risk', 'high crime']):
            return self._explain_hotspots(question_lower, filters)

        if any(kw in question_lower for kw in ['predict', 'forecast', 'future', 'next year', 'expect']):
            return self._explain_predictions(question_lower, filters)

        if any(kw in question_lower for kw in ['safe', 'low crime', 'safest', 'low risk', 'secure']):
            return self._explain_safe_areas(question_lower, filters)

        if any(kw in question_lower for kw in ['compare', 'comparison', 'vs', 'versus', 'between']):
            return self._compare_areas(question_lower, filters)

        if any(kw in question_lower for kw in ['summary', 'overview', 'describe', 'tell me about', 'dataset', 'data']):
            return self._data_summary(filters)

        if any(kw in question_lower for kw in ['heatmap', 'heat map', 'map', 'zone', 'red zone']):
            return self._explain_heatmap(question_lower, filters)

        if any(kw in question_lower for kw in ['prevent', 'reduce', 'solution', 'recommend', 'suggestion', 'measures']):
            return self._recommendations(question_lower, filters)

        if any(kw in question_lower for kw in ['state', 'which state', 'top state']):
            return self._state_analysis(question_lower, filters)

        if any(kw in question_lower for kw in ['crime type', 'type of crime', 'most common', 'frequent crime',
                                                 'murder', 'theft', 'robbery', 'assault', 'kidnap']):
            return self._crime_type_analysis(question_lower, filters)

        if any(kw in question_lower for kw in ['year', 'when', 'which year', 'worst year']):
            return self._year_analysis(question_lower, filters)

        if any(kw in question_lower for kw in ['report', 'download', 'pdf']):
            return ("📄 You can generate a comprehensive PDF report by clicking the **'Generate Report'** "
                    "button at the bottom of the dashboard. The report includes all charts, statistics, "
                    "risk assessments, and predictions based on your current analysis.")

        # General crime-related questions
        if any(kw in question_lower for kw in ['what is', 'how does', 'explain', 'define', 'why']):
            return self._general_answer(question)

        # Default: provide data summary with helpful info
        return self._data_summary(filters)

    def _explain_charts(self, question, filters):
        """Explain the charts displayed on the dashboard."""
        dp = self.data_processor
        cm = dp.column_map

        parts = []

        if any(kw in question for kw in ['crime type', 'distribution', 'pie', 'donut']):
            dist = dp.get_crime_type_distribution(filters)
            if dist['labels']:
                parts.append("📊 **Crime Type Distribution Chart:**")
                parts.append(f"This chart shows the distribution of {len(dist['labels'])} crime types.")
                top3 = list(zip(dist['labels'][:3], dist['values'][:3]))
                parts.append("Top crime types:")
                for name, val in top3:
                    parts.append(f"  • **{name}**: {val:,} cases")
                total = sum(dist['values'])
                if total > 0:
                    pct = (dist['values'][0] / total) * 100
                    parts.append(f"\nThe highest category accounts for **{pct:.1f}%** of all cases.")

        elif any(kw in question for kw in ['yearly', 'trend', 'line', 'time']):
            trend = dp.get_yearly_trend(filters)
            if trend['labels']:
                parts.append("📈 **Yearly Crime Trend Chart:**")
                parts.append(f"Shows crime cases from {trend['labels'][0]} to {trend['labels'][-1]}.")
                if len(trend['values']) >= 2:
                    change = trend['values'][-1] - trend['values'][0]
                    pct_change = (change / trend['values'][0] * 100) if trend['values'][0] > 0 else 0
                    direction = "increased" if change > 0 else "decreased"
                    parts.append(f"Overall, crime has **{direction}** by **{abs(pct_change):.1f}%**.")
                    parts.append(f"Peak year: **{trend['labels'][trend['values'].index(max(trend['values']))]}** "
                                f"with **{max(trend['values']):,}** cases.")

        elif any(kw in question for kw in ['reported', 'solved', 'bar']):
            rvs = dp.get_reported_vs_solved(filters)
            if rvs['labels']:
                parts.append("📊 **Reported vs Solved Cases Chart:**")
                total_r = sum(rvs['reported'])
                total_s = sum(rvs['solved'])
                solve_rate = (total_s / total_r * 100) if total_r > 0 else 0
                parts.append(f"Total reported: **{total_r:,}** | Total solved: **{total_s:,}**")
                parts.append(f"Overall solve rate: **{solve_rate:.1f}%**")
                if solve_rate > 70:
                    parts.append("✅ The solve rate is relatively good!")
                else:
                    parts.append("⚠️ The solve rate needs improvement.")

        elif any(kw in question for kw in ['city', 'comparison', 'horizontal']):
            city = dp.get_city_comparison(filters)
            if city['labels']:
                parts.append("📊 **City/Area-wise Crime Comparison:**")
                parts.append(f"Comparing top {len(city['labels'])} areas by crime count:")
                for name, val in zip(city['labels'][:5], city['values'][:5]):
                    parts.append(f"  • **{name}**: {val:,} cases")

        else:
            # General chart explanation
            parts.append("📊 **Dashboard Charts Overview:**")
            parts.append("The dashboard displays 4 key visualizations:")
            parts.append("1. **Crime Type Distribution** - Shows which types of crimes are most prevalent")
            parts.append("2. **Yearly Crime Trend** - Tracks how crime counts change over time")
            parts.append("3. **Reported vs Solved** - Compares cases reported against cases solved/convicted")
            parts.append("4. **Area-wise Comparison** - Ranks top areas by crime count")
            parts.append("\nAsk about any specific chart for detailed insights!")

        return "\n".join(parts) if parts else "I can explain any chart on the dashboard. Please specify which one!"

    def _explain_trends(self, question, filters):
        """Explain crime trends."""
        dp = self.data_processor
        trend = dp.get_yearly_trend(filters)

        if not trend['labels'] or len(trend['values']) < 2:
            return "📈 Not enough data to analyze trends. Please upload a dataset with multiple years of data."

        parts = ["📈 **Crime Trend Analysis:**\n"]

        values = trend['values']
        years = trend['labels']

        # Overall trend
        overall_change = values[-1] - values[0]
        pct_change = (overall_change / values[0] * 100) if values[0] > 0 else 0
        direction = "increasing" if overall_change > 0 else "decreasing"
        parts.append(f"**Overall Trend:** Crime is **{direction}** ({pct_change:+.1f}% from {years[0]} to {years[-1]})")

        # Peak and trough
        max_idx = values.index(max(values))
        min_idx = values.index(min(values))
        parts.append(f"\n**Peak Year:** {years[max_idx]} with {values[max_idx]:,} cases")
        parts.append(f"**Lowest Year:** {years[min_idx]} with {values[min_idx]:,} cases")

        # Year-over-year changes
        if len(values) >= 3:
            yoy_changes = []
            for i in range(1, len(values)):
                change = ((values[i] - values[i-1]) / values[i-1] * 100) if values[i-1] > 0 else 0
                yoy_changes.append((years[i], change))

            biggest_increase = max(yoy_changes, key=lambda x: x[1])
            biggest_decrease = min(yoy_changes, key=lambda x: x[1])

            parts.append(f"\n**Biggest Spike:** {biggest_increase[0]} ({biggest_increase[1]:+.1f}% YoY)")
            parts.append(f"**Biggest Drop:** {biggest_decrease[0]} ({biggest_decrease[1]:+.1f}% YoY)")

        # Recent trend (last 3 years)
        if len(values) >= 3:
            recent = values[-3:]
            if recent[-1] > recent[0]:
                parts.append("\n⚠️ **Recent trend (last 3 years):** Crime is **rising**. Immediate attention recommended.")
            else:
                parts.append("\n✅ **Recent trend (last 3 years):** Crime is **declining**. Positive progress!")

        return "\n".join(parts)

    def _explain_hotspots(self, question, filters):
        """Explain crime hotspots."""
        dp = self.data_processor
        risk = dp.get_risk_zones(filters)

        parts = ["🔴 **Crime Hotspot Analysis:**\n"]

        if risk['high']:
            parts.append("**HIGH RISK ZONES (Red):**")
            for zone in risk['high'][:5]:
                parts.append(f"  🔴 **{zone['name']}**: {zone['cases']:,} cases")

        if risk['moderate']:
            parts.append("\n**MODERATE RISK ZONES (Orange):**")
            for zone in risk['moderate'][:5]:
                parts.append(f"  🟠 **{zone['name']}**: {zone['cases']:,} cases")

        if risk['low']:
            parts.append("\n**LOW RISK ZONES (Green):**")
            for zone in risk['low'][:5]:
                parts.append(f"  🟢 **{zone['name']}**: {zone['cases']:,} cases")

        if not any(risk.values()):
            parts.append("No risk zone data available. Please check the filters and try again.")

        parts.append("\n💡 **Recommendation:** Focus law enforcement and community programs in HIGH risk zones.")

        return "\n".join(parts)

    def _explain_predictions(self, question, filters):
        """Explain predictions and forecasts."""
        parts = ["🔮 **Crime Prediction Analysis:**\n"]

        if self.predictor and self.predictor.is_trained:
            metrics = self.predictor.metrics
            parts.append(f"**Model Performance:**")
            parts.append(f"  • R² Score: **{metrics.get('r2_score', 'N/A')}**")
            parts.append(f"  • Mean Absolute Error: **{metrics.get('mae', 'N/A')}**")
            parts.append(f"  • Training Samples: **{metrics.get('training_samples', 'N/A'):,}**")

            forecast = self.predictor.forecast_trend(
                self.data_processor.df, self.data_processor.column_map
            )

            if forecast['predicted']:
                predictions = [(y, p) for y, p in zip(forecast['years'], forecast['predicted']) if p is not None]
                if predictions:
                    parts.append("\n**Forecasted Cases:**")
                    for year, pred in predictions:
                        parts.append(f"  📅 **{year}**: ~{pred:,} predicted cases")

        else:
            parts.append("⚠️ The ML model has not been trained yet. Upload a dataset and run analysis first.")

        parts.append("\n💡 **Note:** Predictions are estimates based on historical patterns and may vary "
                    "with real-world factors.")

        return "\n".join(parts)

    def _explain_safe_areas(self, question, filters):
        """Explain safest areas."""
        dp = self.data_processor
        risk = dp.get_risk_zones(filters)

        parts = ["🟢 **Safest Areas Analysis:**\n"]

        if risk['low']:
            parts.append("Areas with the **lowest crime rates**:")
            for zone in sorted(risk['low'], key=lambda x: x['cases'])[:10]:
                parts.append(f"  ✅ **{zone['name']}**: {zone['cases']:,} cases")
        else:
            parts.append("No data available for low-risk areas.")

        return "\n".join(parts)

    def _compare_areas(self, question, filters):
        """Compare crime data between areas."""
        dp = self.data_processor
        city = dp.get_city_comparison(filters)

        if not city['labels']:
            return "📊 Not enough data for comparison. Please try different filters."

        parts = ["📊 **Area Comparison:**\n"]

        for name, val in zip(city['labels'], city['values']):
            bar_len = int((val / max(city['values'])) * 20) if max(city['values']) > 0 else 0
            bar = "█" * bar_len
            parts.append(f"  **{name}**: {val:,} {bar}")

        ratio = city['values'][0] / city['values'][-1] if city['values'][-1] > 0 else 0
        parts.append(f"\n📌 The highest area has **{ratio:.1f}x** more crime than the lowest shown.")

        return "\n".join(parts)

    def _data_summary(self, filters):
        """Provide a summary of the data."""
        dp = self.data_processor
        stats = dp.get_stats(filters)
        summary = dp.get_dataset_summary()

        parts = ["📋 **Dataset Summary:**\n"]
        parts.append(summary)

        if stats:
            parts.append(f"\n**Key Statistics:**")
            if 'total_cases' in stats:
                parts.append(f"  • Total Cases: **{stats['total_cases']:,}**")
            if 'total_states' in stats:
                parts.append(f"  • States/UTs: **{stats['total_states']}**")
            if 'total_cities' in stats:
                parts.append(f"  • Cities/Districts: **{stats['total_cities']}**")
            if 'total_crime_types' in stats:
                parts.append(f"  • Crime Types: **{stats['total_crime_types']}**")
            if 'year_range' in stats:
                parts.append(f"  • Year Range: **{stats['year_range']}**")

        return "\n".join(parts)

    def _explain_heatmap(self, question, filters):
        """Explain the heatmap visualization."""
        dp = self.data_processor
        risk = dp.get_risk_zones(filters)

        parts = ["🗺️ **Heatmap Analysis:**\n"]
        parts.append("The heatmap shows crime intensity across different regions:\n")
        parts.append("  🔴 **Red zones** = High crime areas (top 25% by case count)")
        parts.append("  🟠 **Orange zones** = Moderate crime areas (middle 50%)")
        parts.append("  🟢 **Green zones** = Low crime areas (bottom 25%)")

        h, m, l = len(risk['high']), len(risk['moderate']), len(risk['low'])
        total = h + m + l
        if total > 0:
            parts.append(f"\n**Current Distribution:**")
            parts.append(f"  • High Risk: **{h}** areas ({h/total*100:.0f}%)")
            parts.append(f"  • Moderate Risk: **{m}** areas ({m/total*100:.0f}%)")
            parts.append(f"  • Low Risk: **{l}** areas ({l/total*100:.0f}%)")

        parts.append("\n💡 The darker the zone on the map, the higher the crime density in that region.")

        return "\n".join(parts)

    def _recommendations(self, question, filters):
        """Provide crime prevention recommendations."""
        dp = self.data_processor
        risk = dp.get_risk_zones(filters)

        parts = ["💡 **Crime Prevention Recommendations:**\n"]

        if risk['high']:
            parts.append("**For High-Risk Areas:**")
            parts.append("  1. 🚔 Increase police patrols and surveillance")
            parts.append("  2. 📹 Install CCTV cameras in vulnerable spots")
            parts.append("  3. 💡 Improve street lighting in dark areas")
            parts.append("  4. 👥 Community policing and neighborhood watch programs")
            parts.append("  5. 📱 Deploy mobile crime reporting apps")

        parts.append("\n**General Recommendations:**")
        parts.append("  1. 📊 Use data-driven policing to allocate resources efficiently")
        parts.append("  2. 🏫 Invest in education and youth programs")
        parts.append("  3. 💼 Create employment opportunities in high-crime areas")
        parts.append("  4. 🤝 Strengthen community engagement programs")
        parts.append("  5. ⚖️ Fast-track judicial processes for quicker justice")
        parts.append("  6. 🔍 Regular crime audits and pattern analysis")
        parts.append("  7. 📡 Smart city integration for real-time monitoring")

        return "\n".join(parts)

    def _state_analysis(self, question, filters):
        """Analyze specific states."""
        dp = self.data_processor

        if 'state' not in dp.column_map or 'cases_reported' not in dp.column_map:
            return "State-level data is not available in the current dataset."

        state_data = dp.df.groupby(dp.column_map['state'])[dp.column_map['cases_reported']].sum()
        state_data = state_data.sort_values(ascending=False)

        parts = ["🏛️ **State-wise Crime Analysis:**\n"]
        parts.append("**Top 10 States by Crime Cases:**")
        for i, (state, cases) in enumerate(state_data.head(10).items(), 1):
            parts.append(f"  {i}. **{state}**: {int(cases):,} cases")

        parts.append(f"\n**Bottom 5 States (Safest):**")
        for state, cases in state_data.tail(5).items():
            parts.append(f"  ✅ **{state}**: {int(cases):,} cases")

        return "\n".join(parts)

    def _crime_type_analysis(self, question, filters):
        """Analyze specific crime types."""
        dp = self.data_processor

        if 'crime_type' not in dp.column_map or 'cases_reported' not in dp.column_map:
            return "Crime type data is not available in the current dataset."

        crime_data = dp.df.groupby(dp.column_map['crime_type'])[dp.column_map['cases_reported']].sum()
        crime_data = crime_data.sort_values(ascending=False)

        total = crime_data.sum()

        parts = ["🔍 **Crime Type Analysis:**\n"]
        parts.append(f"Total crime types in dataset: **{len(crime_data)}**\n")
        parts.append("**Most Common Crime Types:**")
        for i, (crime, cases) in enumerate(crime_data.head(10).items(), 1):
            pct = (cases / total * 100) if total > 0 else 0
            parts.append(f"  {i}. **{crime}**: {int(cases):,} cases ({pct:.1f}%)")

        return "\n".join(parts)

    def _year_analysis(self, question, filters):
        """Analyze specific years."""
        dp = self.data_processor
        trend = dp.get_yearly_trend(filters)

        if not trend['labels']:
            return "Year-wise data is not available in the current dataset."

        parts = ["📅 **Year-wise Analysis:**\n"]

        for year, cases in zip(trend['labels'], trend['values']):
            parts.append(f"  **{year}**: {cases:,} cases")

        max_idx = trend['values'].index(max(trend['values']))
        min_idx = trend['values'].index(min(trend['values']))
        parts.append(f"\n⚠️ **Worst Year:** {trend['labels'][max_idx]} ({trend['values'][max_idx]:,} cases)")
        parts.append(f"✅ **Best Year:** {trend['labels'][min_idx]} ({trend['values'][min_idx]:,} cases)")

        return "\n".join(parts)

    def _general_answer(self, question):
        """Answer general questions about crime and the system."""
        question_lower = question.lower()

        knowledge_base = {
            'crime pattern': (
                "🔍 **Crime Pattern Prediction** uses machine learning algorithms to analyze historical crime data "
                "and identify recurring patterns. Our system uses an ensemble of Random Forest and Gradient Boosting "
                "models to predict future crime occurrences based on factors like location, time, crime type, and "
                "historical trends."
            ),
            'heat map': (
                "🗺️ **Heat Maps** are visual representations of data where values are depicted by color. In our "
                "system, crime heat maps show areas with varying crime intensities:\n"
                "  🔴 Red = High crime density\n  🟠 Orange = Moderate crime\n  🟢 Green = Low crime\n\n"
                "They help identify geographic patterns and focus resources effectively."
            ),
            'hotspot': (
                "🔴 **Crime Hotspots** are geographic areas with significantly higher-than-average crime rates. "
                "Our system identifies hotspots by analyzing case counts, growth trends, and spatial clustering. "
                "Hotspot prediction helps law enforcement allocate resources proactively."
            ),
            'machine learning': (
                "🤖 **Machine Learning in Crime Prediction:**\n"
                "Our system uses two powerful algorithms:\n"
                "1. **Random Forest** - An ensemble of decision trees for robust predictions\n"
                "2. **Gradient Boosting** - Sequentially improving weak learners for accuracy\n\n"
                "The final prediction is an average of both models for better reliability."
            ),
            'ipc': (
                "⚖️ **Indian Penal Code (IPC)** is the official criminal code of India that covers all substantive "
                "aspects of criminal law. Crime datasets from India typically categorize offenses under IPC sections. "
                "Common IPC crimes include murder (302), theft (379), robbery (392), and kidnapping (363)."
            ),
            'how to use': (
                "📖 **How to use this system:**\n"
                "1. Upload your crime dataset (CSV format)\n"
                "2. Select filters (State, City, Crime Type, Year)\n"
                "3. Click 'Analyze' to see charts and statistics\n"
                "4. View the heatmap for geographic distribution\n"
                "5. Check Crime Hotspot Predictions\n"
                "6. Use the AI Assistant (me!) for detailed insights\n"
                "7. Generate a PDF report for documentation"
            ),
            'hello': "👋 Hello! I'm the CrimePredict AI Assistant. I can help you understand crime data, explain charts, and provide insights. Ask me anything!",
            'hi': "👋 Hi there! I'm ready to help you analyze crime patterns. What would you like to know?",
            'thank': "You're welcome! 😊 Feel free to ask more questions about the crime data analysis.",
            'help': (
                "🆘 **I can help with:**\n"
                "  • Explaining charts and visualizations\n"
                "  • Analyzing crime trends and patterns\n"
                "  • Identifying hotspots and risk zones\n"
                "  • Understanding predictions and forecasts\n"
                "  • Comparing areas or crime types\n"
                "  • Providing prevention recommendations\n"
                "  • Generating data summaries\n\n"
                "Just ask a question in plain English!"
            )
        }

        for key, response in knowledge_base.items():
            if key in question_lower:
                return response

        return (
            "🤖 I'm the CrimePredict AI Assistant! I can help you with:\n\n"
            "  📊 **Charts** - 'Explain the crime type distribution chart'\n"
            "  📈 **Trends** - 'What's the crime trend over the years?'\n"
            "  🔴 **Hotspots** - 'Which areas have the highest crime?'\n"
            "  🔮 **Predictions** - 'What's the crime forecast?'\n"
            "  🟢 **Safe areas** - 'Which areas are safest?'\n"
            "  💡 **Recommendations** - 'How to reduce crime?'\n"
            "  📋 **Data Summary** - 'Give me a data overview'\n\n"
            "Try asking one of these questions!"
        )
