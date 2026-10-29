"""
Flask Backend — Updated routes for two-phase flow:
POST /api/discover → starts URL discovery
GET  /api/discovered → returns discovered URLs for selection
POST /api/scrape → starts scraping (selected_urls OR all)
"""

import os
import time
from flask import Flask, render_template, request, jsonify, send_file
from core.task_manager import LeadExtractionManager
from core.exporter import generate_excel_export, generate_csv_export
from data.india_data import INDIAN_STATES_AND_DISTRICTS, CONSTRUCTION_CATEGORIES

app = Flask(__name__)
manager = LeadExtractionManager()

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)

BACKEND_EXPORTS_DIR = os.path.join(os.path.dirname(__file__), 'backend', 'exports')
os.makedirs(BACKEND_EXPORTS_DIR, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/geo-data', methods=['GET'])
def get_geo_data():
    return jsonify({
        "states": sorted(list(INDIAN_STATES_AND_DISTRICTS.keys())),
        "districts_by_state": {k: sorted(v) for k, v in INDIAN_STATES_AND_DISTRICTS.items()}
    })


@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({"categories": CONSTRUCTION_CATEGORIES})


# ── PHASE 1: DISCOVER ────────────────────────────────────────────────────────
@app.route('/api/discover', methods=['POST'])
def discover():
    data = request.get_json() or {}
    selected_states = data.get('states', [])
    selected_districts = data.get('districts', [])
    selected_categories = data.get('categories', [])
    custom_location = data.get('custom_location', '')
    custom_keyword = data.get('custom_keyword', '')
    search_engines = data.get('search_engines', None)

    if not selected_states:
        return jsonify({"success": False, "message": "Please select at least one State."}), 400
    if not selected_categories and not custom_keyword.strip():
        return jsonify({"success": False, "message": "Please select at least one Category or enter a Custom Search Keyword."}), 400
    if isinstance(search_engines, list) and len(search_engines) == 0:
        return jsonify({"success": False, "message": "Please select at least one Search Engine."}), 400

    success, msg = manager.start_discovery(
        selected_states, selected_districts, selected_categories,
        custom_location, custom_keyword, search_engines=search_engines
    )
    return jsonify({"success": success, "message": msg})


@app.route('/api/discovered', methods=['GET'])
def get_discovered():
    """Return list of discovered candidate URLs for the selection panel."""
    candidates = manager.get_discovered()
    return jsonify({"total": len(candidates), "candidates": candidates})


# ── PHASE 2: SCRAPE ──────────────────────────────────────────────────────────
@app.route('/api/scrape', methods=['POST'])
def scrape():
    """
    Start scraping phase.
    Body: { "selected_urls": [...] }  ← specific URLs only
    Body: { "scrape_all": true }       ← all discovered URLs
    """
    data = request.get_json() or {}
    scrape_all = data.get('scrape_all', False)
    selected_urls = data.get('selected_urls', [])

    if scrape_all:
        success, msg = manager.start_scraping(selected_urls=None)
    elif selected_urls:
        success, msg = manager.start_scraping(selected_urls=selected_urls)
    else:
        return jsonify({"success": False, "message": "No URLs selected and scrape_all not set."}), 400

    return jsonify({"success": success, "message": msg})


# ── FULL AUTO PROCESSING ─────────────────────────────────────────────────────
@app.route('/api/auto-process', methods=['POST'])
def auto_process():
    data = request.get_json() or {}
    pan_india = data.get('pan_india', False)
    selected_states = data.get('states', [])
    selected_districts = data.get('districts', [])
    selected_categories = data.get('categories', [])
    custom_location = data.get('custom_location', '')
    custom_keyword = data.get('custom_keyword', '')
    search_engines = data.get('search_engines', ['google', 'brave'])

    if pan_india:
        selected_states = sorted(list(INDIAN_STATES_AND_DISTRICTS.keys()))
        selected_districts = []

    if not selected_states:
        return jsonify({"success": False, "message": "Please select at least one State."}), 400

    # Auto-ensure Google search engine is selected
    if isinstance(search_engines, list):
        if 'google' not in search_engines:
            search_engines.insert(0, 'google')
    else:
        search_engines = ['google', 'brave']

    success, msg = manager.start_auto_processing(
        selected_states, selected_districts, selected_categories,
        custom_location, custom_keyword, search_engines=search_engines,
        is_pan_india=pan_india
    )
    return jsonify({"success": success, "message": msg})


# ── LEGACY: direct start (still works, triggers discover then auto-scrape) ───
@app.route('/api/start', methods=['POST'])
def start_extraction():
    data = request.get_json() or {}
    selected_states = data.get('states', [])
    selected_districts = data.get('districts', [])
    selected_categories = data.get('categories', [])
    custom_location = data.get('custom_location', '')
    custom_keyword = data.get('custom_keyword', '')
    search_engines = data.get('search_engines', None)

    if not selected_states:
        return jsonify({"success": False, "message": "Please select at least one State."}), 400
    if not selected_categories and not custom_keyword.strip():
        return jsonify({"success": False, "message": "Please select at least one Category or enter a Custom Search Keyword."}), 400

    success, msg = manager.start_discovery(
        selected_states, selected_districts, selected_categories,
        custom_location, custom_keyword, search_engines=search_engines
    )
    return jsonify({"success": success, "message": msg})


# ── CONTROLS ─────────────────────────────────────────────────────────────────
@app.route('/api/pause', methods=['POST'])
def pause_extraction():
    success, msg = manager.pause_extraction()
    return jsonify({"success": success, "message": msg})


@app.route('/api/resume', methods=['POST'])
def resume_extraction():
    success, msg = manager.resume_extraction()
    return jsonify({"success": success, "message": msg})


@app.route('/api/stop', methods=['POST'])
def stop_extraction():
    success, msg = manager.stop_extraction()
    return jsonify({"success": success, "message": msg})


@app.route('/api/clear', methods=['POST'])
def clear_extraction():
    success, msg = manager.clear_results()
    return jsonify({"success": success, "message": msg})


# ── STATUS & LEADS ────────────────────────────────────────────────────────────
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(manager.get_status())


@app.route('/api/leads', methods=['GET'])
def get_leads():
    leads = manager.get_leads()
    query = request.args.get('search', '').lower().strip()
    if query:
        leads = [
            l for l in leads
            if query in l.get('business_name', '').lower()
            or query in l.get('district', '').lower()
            or query in l.get('category', '').lower()
            or query in l.get('mobile_numbers', '').lower()
            or query in l.get('email_addresses', '').lower()
        ]
    return jsonify({"total": len(leads), "leads": leads})


# ── EXPORTS ───────────────────────────────────────────────────────────────────
@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    leads = manager.get_leads()
    if not leads:
        return jsonify({"error": "No leads to export."}), 400
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"Civil_Leads_Export_{timestamp}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    generate_excel_export(leads, filepath)
    return send_file(filepath, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    leads = manager.get_leads()
    if not leads:
        return jsonify({"error": "No leads to export."}), 400
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"Civil_Leads_Export_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)
    generate_csv_export(leads, filepath)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="text/csv")


@app.route('/api/export/file/<path:filename>', methods=['GET'])
def download_export_file(filename):
    safe_name = os.path.basename(filename)
    filepath = os.path.join(BACKEND_EXPORTS_DIR, safe_name)
    if not os.path.isfile(filepath):
        filepath_leg = os.path.join(EXPORTS_DIR, safe_name)
        if os.path.isfile(filepath_leg):
            filepath = filepath_leg
        else:
            return jsonify({"error": f"File '{safe_name}' not found."}), 404

    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if safe_name.endswith('.xlsx') else "text/csv"
    return send_file(filepath, as_attachment=True, download_name=safe_name, mimetype=mime)


@app.route('/api/export/latest-master', methods=['GET'])
def download_latest_master():
    with manager.lock:
        master_file = manager.latest_master_file
    if not master_file:
        return jsonify({"error": "No Master State export file generated yet."}), 404
    filepath = os.path.join(BACKEND_EXPORTS_DIR, master_file)
    if not os.path.isfile(filepath):
        return jsonify({"error": "Master file not found on disk."}), 404
    return send_file(filepath, as_attachment=True, download_name=master_file,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/api/export/history', methods=['GET'])
def export_history():
    files = []
    if os.path.isdir(BACKEND_EXPORTS_DIR):
        for f in os.listdir(BACKEND_EXPORTS_DIR):
            if f.endswith('.xlsx') or f.endswith('.csv'):
                fpath = os.path.join(BACKEND_EXPORTS_DIR, f)
                stat = os.stat(fpath)
                files.append({
                    "filename": f,
                    "is_master": "MASTER" in f,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "download_url": f"/api/export/file/{f}"
                })
    files.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({"total": len(files), "files": files})


if __name__ == '__main__':
    print("Starting Pan-India Civil & Construction Lead Extraction Server on http://localhost:5000 ...")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
