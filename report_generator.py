"""
Report Generator Module
Generates PDF reports with crime analysis, charts, and recommendations.
"""

import io
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime


class ReportGenerator:
    """Generates comprehensive PDF reports for crime analysis."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a47a3'),
            spaceBefore=15,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            leading=16
        ))
        self.styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def generate_report(self, data_processor, predictor=None, filters=None, output_path=None):
        """Generate a comprehensive PDF report."""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crime_report.pdf')

        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=50, bottomMargin=50
        )

        story = []

        # Title page
        story.append(Spacer(1, 80))
        story.append(Paragraph("Crime Pattern Prediction<br/>&amp; Mapping Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor('#4a47a3')))
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['CustomBody']
        ))

        if filters:
            filter_text = []
            if filters.get('state') and filters['state'] != 'all':
                filter_text.append(f"State: {filters['state']}")
            if filters.get('city') and filters['city'] != 'all':
                filter_text.append(f"City: {filters['city']}")
            if filters.get('crime_type') and filters['crime_type'] != 'all':
                filter_text.append(f"Crime Type: {filters['crime_type']}")
            if filters.get('year') and filters['year'] != 'all':
                filter_text.append(f"Year: {filters['year']}")
            if filter_text:
                story.append(Paragraph("Filters: " + " | ".join(filter_text), self.styles['CustomBody']))

        story.append(PageBreak())

        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        stats = data_processor.get_stats(filters)
        summary_parts = []
        if 'total_cases' in stats:
            summary_parts.append(f"Total reported cases: {stats['total_cases']:,}")
        if 'total_states' in stats:
            summary_parts.append(f"States/UTs analyzed: {stats['total_states']}")
        if 'total_crime_types' in stats:
            summary_parts.append(f"Crime types covered: {stats['total_crime_types']}")
        if 'year_range' in stats:
            summary_parts.append(f"Period: {stats['year_range']}")
        for part in summary_parts:
            story.append(Paragraph(f"• {part}", self.styles['CustomBody']))

        story.append(Spacer(1, 15))

        # Crime Type Distribution
        story.append(Paragraph("Crime Type Distribution", self.styles['CustomHeading']))
        dist = data_processor.get_crime_type_distribution(filters)
        if dist['labels']:
            chart_path = self._create_pie_chart(dist['labels'][:8], dist['values'][:8], "Crime Type Distribution")
            if chart_path:
                story.append(Image(chart_path, width=400, height=280))
                story.append(Spacer(1, 10))

            # Table
            table_data = [['Crime Type', 'Cases', 'Percentage']]
            total = sum(dist['values'])
            for label, val in zip(dist['labels'][:10], dist['values'][:10]):
                pct = f"{(val/total*100):.1f}%" if total > 0 else "0%"
                table_data.append([label, f"{val:,}", pct])

            table = Table(table_data, colWidths=[250, 100, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a47a3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5ff')]),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(table)

        story.append(PageBreak())

        # Yearly Trend
        story.append(Paragraph("Yearly Crime Trend", self.styles['CustomHeading']))
        trend = data_processor.get_yearly_trend(filters)
        if trend['labels']:
            chart_path = self._create_line_chart(trend['labels'], trend['values'], "Yearly Crime Trend", "Year", "Cases")
            if chart_path:
                story.append(Image(chart_path, width=420, height=260))
                story.append(Spacer(1, 10))

            if len(trend['values']) >= 2:
                change = trend['values'][-1] - trend['values'][0]
                pct = (change / trend['values'][0] * 100) if trend['values'][0] > 0 else 0
                direction = "increased" if change > 0 else "decreased"
                story.append(Paragraph(
                    f"Overall, crime has {direction} by {abs(pct):.1f}% from "
                    f"{trend['labels'][0]} to {trend['labels'][-1]}.",
                    self.styles['CustomBody']
                ))

        # Risk Assessment
        story.append(Spacer(1, 15))
        story.append(Paragraph("Risk Zone Assessment", self.styles['CustomHeading']))
        risk = data_processor.get_risk_zones(filters)

        for level, label, color_hex in [('high', 'HIGH RISK', '#e74c3c'),
                                         ('moderate', 'MODERATE RISK', '#f39c12'),
                                         ('low', 'LOW RISK', '#27ae60')]:
            if risk[level]:
                story.append(Paragraph(
                    f'<font color="{color_hex}">■</font> {label} ({len(risk[level])} areas)',
                    self.styles['CustomBody']
                ))
                areas = [f"{z['name']} ({z['cases']:,} cases)" for z in risk[level][:5]]
                story.append(Paragraph("  " + ", ".join(areas), self.styles['CustomBody']))

        story.append(PageBreak())

        # Predictions
        if predictor and predictor.is_trained:
            story.append(Paragraph("Crime Predictions & Forecast", self.styles['CustomHeading']))

            forecast = predictor.forecast_trend(data_processor.df, data_processor.column_map)
            if forecast['predicted']:
                predictions = [(y, p) for y, p in zip(forecast['years'], forecast['predicted']) if p is not None]
                if predictions:
                    story.append(Paragraph("Forecasted values for upcoming years:", self.styles['CustomBody']))
                    for year, pred in predictions:
                        story.append(Paragraph(f"  • {year}: ~{pred:,} predicted cases", self.styles['CustomBody']))

            # Hotspot predictions
            hotspots = predictor.get_hotspot_prediction(data_processor.df, data_processor.column_map)
            if hotspots:
                story.append(Spacer(1, 10))
                story.append(Paragraph("Predicted Hotspots", self.styles['CustomHeading']))
                hs_data = [['Area', 'Current', 'Predicted', 'Growth', 'Risk Score']]
                for hs in hotspots[:10]:
                    hs_data.append([
                        hs['area'],
                        f"{hs['current_cases']:,}",
                        f"{hs['predicted_cases']:,}",
                        f"{hs['growth_rate']:+.1f}%",
                        f"{hs['risk_score']:.0f}/100"
                    ])
                hs_table = Table(hs_data, colWidths=[140, 80, 80, 70, 70])
                hs_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ]))
                story.append(hs_table)

        # Recommendations
        story.append(Spacer(1, 15))
        story.append(Paragraph("Recommendations", self.styles['CustomHeading']))
        recs = [
            "Increase law enforcement presence in high-risk zones",
            "Deploy predictive policing strategies using data insights",
            "Enhance CCTV surveillance in crime hotspots",
            "Strengthen community policing and awareness programs",
            "Invest in youth education and employment programs in vulnerable areas",
            "Implement smart city technologies for real-time crime monitoring",
            "Establish rapid response teams for recurring crime patterns",
        ]
        for i, rec in enumerate(recs, 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['CustomBody']))

        # Footer
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Paragraph(
            "CrimePredict - Crime Pattern Prediction &amp; Mapping System | Auto-generated Report",
            self.styles['CustomFooter']
        ))

        doc.build(story)

        # Cleanup temp charts
        for f in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if f.startswith('temp_chart_') and f.endswith('.png'):
                try:
                    os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), f))
                except:
                    pass

        return output_path

    def _create_pie_chart(self, labels, values, title):
        """Create a pie chart and save as temporary image."""
        try:
            fig, ax = plt.subplots(figsize=(8, 5.5))
            colors_list = ['#4a47a3', '#7978b7', '#a5a4cc', '#d1d0e0',
                          '#e8725c', '#f5a462', '#f9d56e', '#7ed6df']

            # Truncate long labels
            short_labels = [l[:25] + '...' if len(l) > 25 else l for l in labels]

            wedges, texts, autotexts = ax.pie(
                values, labels=short_labels, colors=colors_list[:len(values)],
                autopct='%1.1f%%', startangle=90, pctdistance=0.85
            )
            plt.setp(autotexts, size=7)
            plt.setp(texts, size=7)
            ax.set_title(title, fontsize=12, fontweight='bold')
            plt.tight_layout()

            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'temp_chart_pie.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except Exception:
            return None

    def _create_line_chart(self, x, y, title, xlabel, ylabel):
        """Create a line chart and save as temporary image."""
        try:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(x, y, color='#4a47a3', linewidth=2, marker='o', markersize=5)
            ax.fill_between(x, y, alpha=0.1, color='#4a47a3')
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'temp_chart_line.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            return path
        except Exception:
            return None
