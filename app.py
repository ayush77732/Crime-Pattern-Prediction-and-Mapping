"""
Flask Application - Crime Pattern Prediction & Mapping
Main server with API routes for data upload, analysis, prediction, and AI chat.
"""

import os
import json
import traceback
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

from data_processor import DataProcessor
from ml_model import CrimePredictor
from ai_assistant import AIAssistant
from report_generator import ReportGenerator

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global instances
data_processor = DataProcessor()
predictor = CrimePredictor()
ai_assistant = AIAssistant()
report_generator = ReportGenerator()


# ---- Page Routes ----

@app.route('/')
def index():
    """Serve the landing page."""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page."""
    return render_template('dashboard.html')


# ---- API Routes ----

@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    """Upload and process a CSV dataset."""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'}), 400

        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'dataset.csv')
        file.save(filepath)

        # Process
        metadata = data_processor.load_csv(filepath)

        # Train ML model
        train_result = predictor.train(data_processor.df, data_processor.column_map)

        # Set AI assistant context
        ai_assistant.set_context(data_processor, predictor)

        return jsonify({
            'status': 'success',
            'metadata': metadata,
            'training': train_result,
            'message': f"Dataset loaded successfully! {metadata['total_rows']} rows processed."
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Run analysis with filters and return chart data."""
    try:
        if data_processor.df is None:
            return jsonify({'status': 'error', 'message': 'No dataset loaded'}), 400

        filters = request.json or {}

        result = {
            'status': 'success',
            'stats': data_processor.get_stats(filters),
            'crime_type_distribution': data_processor.get_crime_type_distribution(filters),
            'yearly_trend': data_processor.get_yearly_trend(filters),
            'reported_vs_solved': data_processor.get_reported_vs_solved(filters),
            'city_comparison': data_processor.get_city_comparison(filters),
            'risk_zones': data_processor.get_risk_zones(filters),
            'high_risk_alerts': data_processor.get_high_risk_alerts(filters),
        }

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """Run ML prediction."""
    try:
        if data_processor.df is None:
            return jsonify({'status': 'error', 'message': 'No dataset loaded'}), 400

        filters = request.json or {}

        prediction = predictor.predict(filters, data_processor.column_map)
        forecast = predictor.forecast_trend(data_processor.df, data_processor.column_map)
        hotspots = predictor.get_hotspot_prediction(data_processor.df, data_processor.column_map)

        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'forecast': forecast,
            'hotspots': hotspots
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/heatmap', methods=['POST'])
def heatmap():
    """Generate heatmap data."""
    try:
        if data_processor.df is None:
            return jsonify({'status': 'error', 'message': 'No dataset loaded'}), 400

        filters = request.json or {}
        heatmap_data = data_processor.get_heatmap_data(filters)

        return jsonify({
            'status': 'success',
            'heatmap': heatmap_data
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI Assistant chat endpoint."""
    try:
        data = request.json or {}
        question = data.get('message', '').strip()
        filters = data.get('filters', {})

        if not question:
            return jsonify({'status': 'error', 'message': 'No question provided'}), 400

        answer = ai_assistant.answer(question, filters)

        return jsonify({
            'status': 'success',
            'answer': answer
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate and return a PDF report."""
    try:
        if data_processor.df is None:
            return jsonify({'status': 'error', 'message': 'No dataset loaded'}), 400

        filters = request.json or {}
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crime_report.pdf')

        report_generator.generate_report(
            data_processor, predictor, filters, report_path
        )

        return send_file(
            report_path,
            as_attachment=True,
            download_name='CrimePredict_Report.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cities', methods=['POST'])
def get_cities():
    """Get cities for a selected state."""
    try:
        if data_processor.df is None:
            return jsonify({'cities': []})

        data = request.json or {}
        state = data.get('state', 'all')

        if state == 'all' or 'city' not in data_processor.column_map or 'state' not in data_processor.column_map:
            cities = data_processor.metadata.get('filters', {}).get('cities', [])
        else:
            state_col = data_processor.column_map['state']
            city_col = data_processor.column_map['city']
            cities = sorted(data_processor.df[data_processor.df[state_col] == state][city_col].dropna().unique().tolist())
            cities = [str(c) for c in cities]

        return jsonify({'cities': cities})

    except Exception as e:
        return jsonify({'cities': [], 'error': str(e)})


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  CrimePredict - Crime Pattern Prediction & Mapping")
    print("  Server running at http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
