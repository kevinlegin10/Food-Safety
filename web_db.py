from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os
import sys
import threading

# Ensure current directory is in Python path to import agent.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import audit_sop_compliance

app = Flask(__name__)
DB_NAME = 'food_safety_test.db'

def init_db():
    """Initializes the SQLite database schema and imports master_qa_log.csv data if empty."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if table exists and has the correct schema (check for a new column like 'line_name')
    try:
        cursor.execute("SELECT line_name FROM shift_logs LIMIT 1")
    except sqlite3.OperationalError:
        print("Schema outdated or table missing. Re-creating shift_logs table...")
        cursor.execute("DROP TABLE IF EXISTS shift_logs")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shift_logs (
            batch_id TEXT PRIMARY KEY,
            timestamp TEXT,
            line_name TEXT,
            material_id TEXT,
            vendor_cert_status TEXT,
            material_storage_status TEXT,
            is_allergen TEXT,
            allergen_storage_compliant TEXT,
            freezer_id TEXT,
            freezer_temp_c REAL,
            cip_equip TEXT,
            cip_step TEXT,
            cip_temp_c REAL,
            micro_swab_result TEXT,
            status TEXT DEFAULT 'PENDING',
            agent_feedback TEXT
        )
    ''')
    conn.commit()

    # Auto-ingestion from master_qa_log.csv if table is empty
    csv_path = 'master_qa_log.csv'
    if os.path.exists(csv_path):
        cursor.execute("SELECT COUNT(*) FROM shift_logs")
        if cursor.fetchone()[0] == 0:
            print("Database empty. Ingesting from master_qa_log.csv...")
            import csv
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT OR IGNORE INTO shift_logs (
                            batch_id, timestamp, line_name, material_id, 
                            vendor_cert_status, material_storage_status, 
                            is_allergen, allergen_storage_compliant, 
                            freezer_id, freezer_temp_c, 
                            cip_equip, cip_step, cip_temp_c, 
                            micro_swab_result, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
                    ''', (
                        row.get('Batch_ID'), 
                        row.get('Timestamp'), 
                        row.get('Line_Name'), 
                        row.get('Material_ID'),
                        row.get('Vendor_Cert_Status'), 
                        row.get('Material_Storage_Status'),
                        row.get('Is_Allergen'), 
                        row.get('Allergen_Storage_Compliant'),
                        row.get('Freezer_ID'), 
                        float(row.get('Freezer_Temp_C')) if row.get('Freezer_Temp_C') else None,
                        row.get('CIP_Equip'), 
                        row.get('CIP_Step'), 
                        float(row.get('CIP_Temp_C')) if row.get('CIP_Temp_C') else None,
                        row.get('Micro_Swab_Result')
                    ))
            conn.commit()
    conn.close()

# HTML & CSS UI Design (Premium Glassmorphism Dashboard for Master QA Logs)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Food Safety QA Audit Dashboard</title>
    <!-- Outfit Font for Modern and Premium Typography -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #070a13 0%, #0f1423 100%);
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(255, 255, 255, 0.07);
            --card-hover-border: rgba(99, 102, 241, 0.35);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-glow: rgba(99, 102, 241, 0.25);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            --input-bg: rgba(255, 255, 255, 0.02);
            --input-border: rgba(255, 255, 255, 0.08);
            --input-focus-border: #6366f1;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 1280px;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1.5rem;
        }

        header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(to right, #a5b4fc, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        header p {
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }

        .btn-header-container {
            display: flex;
            gap: 1rem;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
        }

        @media (max-width: 900px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            border-color: var(--card-hover-border);
            transform: translateY(-2px);
        }

        .stat-val {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-total .stat-val { color: #fff; }
        .stat-pass .stat-val { color: var(--success); }
        .stat-fail .stat-val { color: var(--danger); }
        .stat-pending .stat-val { color: var(--warning); }

        /* Collapsible Form Styling */
        .collapsible-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .collapsible-header {
            padding: 1.5rem 2rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 1.2rem;
            background: rgba(255, 255, 255, 0.01);
            user-select: none;
        }

        .collapsible-header:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .collapsible-content {
            padding: 0 2rem 2rem 2rem;
            display: none;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
        }

        @media (max-width: 900px) {
            .collapsible-content {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 600px) {
            .collapsible-content {
                grid-template-columns: 1fr;
            }
        }

        .form-group {
            margin-bottom: 0.5rem;
        }

        .form-group label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 0.4rem;
            font-weight: 500;
        }

        .form-control {
            width: 100%;
            padding: 0.65rem 0.9rem;
            font-size: 0.95rem;
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 8px;
            color: var(--text-primary);
            transition: all 0.2s ease;
            outline: none;
        }

        .form-control:focus {
            border-color: var(--input-focus-border);
            box-shadow: 0 0 0 3px var(--primary-glow);
            background: rgba(255, 255, 255, 0.04);
        }

        .btn {
            padding: 0.75rem 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--primary);
            color: #fff;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .btn-primary:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        .btn-warning {
            background: var(--warning);
            color: #111;
            box-shadow: 0 4px 12px var(--warning-glow);
        }

        .btn-warning:hover {
            background: #d97706;
            transform: translateY(-1px);
        }

        /* History Logs Table */
        .logs-section {
            width: 100%;
        }

        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }

        .logs-header h2 {
            font-size: 1.4rem;
            font-weight: 600;
        }

        .logs-table-container {
            border: 1px solid var(--card-border);
            border-radius: 16px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.01);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: rgba(255, 255, 255, 0.02);
            padding: 1.1rem 1.5rem;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--card-border);
        }

        td {
            padding: 1.1rem 1.5rem;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.95rem;
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        .tr-log-row {
            cursor: pointer;
            transition: background 0.2s ease;
        }

        .tr-log-row:hover {
            background: rgba(255, 255, 255, 0.015);
        }

        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .badge-pass {
            background: var(--success-glow);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.25);
        }
        .badge-pass::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 6px var(--success);
        }

        .badge-fail {
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.25);
        }
        .badge-fail::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--danger);
            box-shadow: 0 0 6px var(--danger);
        }

        .badge-pending {
            background: var(--warning-glow);
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, 0.25);
        }
        .badge-pending::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--warning);
            box-shadow: 0 0 6px var(--warning);
            animation: pulse-dot 1.5s infinite;
        }

        .badge-auditing {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .badge-auditing::before {
            content: '';
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #818cf8;
            box-shadow: 0 0 6px #818cf8;
            animation: pulse-dot 1.5s infinite;
        }

        .spinner-mini {
            display: inline-block;
            width: 10px;
            height: 10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin-mini 1s ease-in-out infinite;
            margin-right: 4px;
        }

        @keyframes spin-mini {
            to { transform: rotate(360deg); }
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
        }

        /* Action buttons */
        .btn-audit {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #c7d2fe;
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-audit:hover {
            background: var(--primary);
            color: #fff;
        }

        .btn-view-report {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn-view-report:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        /* Sub-grid Expanded Details */
        .detail-row {
            display: none;
            background: rgba(0, 0, 0, 0.25);
        }

        .detail-wrapper {
            padding: 1.75rem 2rem;
            border-bottom: 1px solid var(--card-border);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            animation: slideDown 0.25s ease-out;
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 900px) {
            .detail-wrapper {
                grid-template-columns: 1fr;
            }
        }

        .detail-column-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
        }

        /* Parameters List */
        .params-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem 1.5rem;
        }

        .param-item {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .param-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
        }

        .param-value {
            font-size: 0.95rem;
            color: var(--text-primary);
            font-weight: 500;
        }

        .feedback-box {
            background: rgba(255, 255, 255, 0.02);
            border-left: 3px solid var(--primary);
            padding: 1.25rem;
            border-radius: 0 12px 12px 0;
            font-size: 0.9rem;
            line-height: 1.6;
            white-space: pre-wrap;
            color: #d1d5db;
            max-height: 350px;
            overflow-y: auto;
        }

        .feedback-pending {
            border-left-color: var(--warning);
            color: var(--text-secondary);
            font-style: italic;
        }

        /* Loading Overlay Overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(7, 10, 19, 0.9);
            backdrop-filter: blur(10px);
            z-index: 9999;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 1.5rem;
        }

        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(99, 102, 241, 0.1);
            border-left-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            100% { transform: rotate(360deg); }
        }

        .loading-text {
            font-size: 1.3rem;
            font-weight: 600;
            color: #fff;
        }

        .loading-subtext {
            font-size: 0.95rem;
            color: var(--text-secondary);
            animation: pulse-text 2s infinite;
        }

        /* Empty State */
        .empty-state {
            padding: 4rem 2rem;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <div class="loading-text" id="loadingText">Running QA Audit Compliance...</div>
        <div class="loading-subtext" id="loadingSubtext">Connecting to local DeepSeek model...</div>
    </div>

    <div class="container">
        <header>
            <div>
                <h1>🛡️ Food Safety QA Auditor</h1>
                <p>Master QA Log compliance checker powered by Chroma RAG & DeepSeek-R1</p>
            </div>
            <div class="btn-header-container">
                <button class="btn btn-warning" id="btnAuditAll" onclick="auditAllPending()">
                    ⚡ Audit All Pending
                </button>
            </div>
        </header>

        <!-- Stats Overview -->
        <div class="stats-grid">
            <div class="stat-card stat-total">
                <div class="stat-val" id="statTotal">0</div>
                <div class="stat-label">Total Batches</div>
            </div>
            <div class="stat-card stat-pass">
                <div class="stat-val" id="statPass">0</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card stat-fail">
                <div class="stat-val" id="statFail">0</div>
                <div class="stat-label">Failed / Quarantine</div>
            </div>
            <div class="stat-card stat-pending">
                <div class="stat-val" id="statPending">0</div>
                <div class="stat-label">Pending Audit</div>
            </div>
        </div>

        <!-- Add Manual Record Card -->
        <div class="collapsible-card">
            <div class="collapsible-header" onclick="toggleForm()">
                <span>➕ Add New QA Record</span>
                <span id="formToggleIcon">▼</span>
            </div>
            <form id="addRecordForm" onsubmit="submitForm(event)">
                <div class="collapsible-content" id="formContent">
                    <div class="form-group">
                        <label for="batchId">Batch ID</label>
                        <input type="text" id="batchId" class="form-control" placeholder="e.g. B-105" required>
                    </div>
                    <div class="form-group">
                        <label for="timestamp">Timestamp</label>
                        <input type="datetime-local" id="timestamp" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="lineName">Production Line Name</label>
                        <input type="text" id="lineName" class="form-control" placeholder="e.g. Line-1" required>
                    </div>
                    <div class="form-group">
                        <label for="materialId">Material ID</label>
                        <input type="text" id="materialId" class="form-control" placeholder="e.g. MAT-A" required>
                    </div>
                    <div class="form-group">
                        <label for="vendorCert">Vendor Certification</label>
                        <select id="vendorCert" class="form-control">
                            <option value="Certified">Certified</option>
                            <option value="Uncertified">Uncertified</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="materialStorage">Material Storage Status</label>
                        <select id="materialStorage" class="form-control">
                            <option value="Approved">Approved</option>
                            <option value="Rejected">Rejected</option>
                            <option value="Quarantined">Quarantined</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="isAllergen">Contains Allergen?</label>
                        <select id="isAllergen" class="form-control">
                            <option value="False">No</option>
                            <option value="True">Yes</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="allergenCompliant">Allergen Storage Compliant?</label>
                        <select id="allergenCompliant" class="form-control">
                            <option value="Yes">Yes</option>
                            <option value="No">No</option>
                            <option value="N/A">N/A</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="freezerId">Freezer/Fridge ID</label>
                        <input type="text" id="freezerId" class="form-control" placeholder="e.g. FRZ-20" required>
                    </div>
                    <div class="form-group">
                        <label for="freezerTemp">Freezer Temp (°C)</label>
                        <input type="number" step="0.1" id="freezerTemp" class="form-control" placeholder="e.g. -20.5" required>
                    </div>
                    <div class="form-group">
                        <label for="cipEquip">CIP Equipment</label>
                        <input type="text" id="cipEquip" class="form-control" placeholder="e.g. Silo-1" required>
                    </div>
                    <div class="form-group">
                        <label for="cipStep">CIP Cleaning Step</label>
                        <input type="text" id="cipStep" class="form-control" placeholder="e.g. Lye Circulation" required>
                    </div>
                    <div class="form-group">
                        <label for="cipTemp">CIP Temp (°C)</label>
                        <input type="number" step="0.1" id="cipTemp" class="form-control" placeholder="e.g. 75.0" required>
                    </div>
                    <div class="form-group">
                        <label for="microSwab">Microbial Swab Result</label>
                        <select id="microSwab" class="form-control">
                            <option value="Negative">Negative</option>
                            <option value="Positive_Salmonella">Positive (Salmonella)</option>
                            <option value="Positive_Listeria">Positive (Listeria)</option>
                            <option value="Positive_Coliforms">Positive (Coliforms)</option>
                        </select>
                    </div>
                    <div class="form-group" style="display: flex; align-items: flex-end;">
                        <button type="submit" class="btn btn-primary" style="width: 100%;">
                            Save Record
                        </button>
                    </div>
                </div>
            </form>
        </div>

        <!-- Historical Logs Table -->
        <div class="logs-section">
            <div class="logs-header">
                <h2>📋 Operational Logs & Compliance Audits</h2>
            </div>
            <div class="logs-table-container">
                <table id="logsTable">
                    <thead>
                        <tr>
                            <th>Batch ID</th>
                            <th>Timestamp</th>
                            <th>Line</th>
                            <th>Micro Swab</th>
                            <th>Freezer Temp</th>
                            <th>Status</th>
                            <th>Actions</th>
                            <th style="text-align: right;">Delete</th>
                        </tr>
                    </thead>
                    <tbody id="logsBody">
                        <!-- Populated dynamically via JS -->
                    </tbody>
                </table>
                <div class="empty-state" id="emptyState" style="display: none;">
                    No safety records found. Ingest the CSV or add a record to get started.
                </div>
            </div>
        </div>
    </div>

    <script>
        // DOM Elements
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        const loadingSubtext = document.getElementById('loadingSubtext');
        const logsBody = document.getElementById('logsBody');
        const emptyState = document.getElementById('emptyState');
        const formContent = document.getElementById('formContent');
        const formToggleIcon = document.getElementById('formToggleIcon');
        const addRecordForm = document.getElementById('addRecordForm');
        const btnAuditAll = document.getElementById('btnAuditAll');

        // Stats
        const statTotal = document.getElementById('statTotal');
        const statPass = document.getElementById('statPass');
        const statFail = document.getElementById('statFail');
        const statPending = document.getElementById('statPending');

        // Dynamic status transition messages during the RAG pipeline call
        const loadingPhases = [
            "Querying Chroma vector database...",
            "Retrieving safety guidelines and limit regulations...",
            "Evaluating CIP steps and allergen controls...",
            "Running compliance agent with DeepSeek-R1 reasoning...",
            "Formulating PASS/FAIL safety assessment..."
        ];

        let phaseInterval;
        let globalLogs = [];

        // Set default timestamp on load
        document.getElementById('timestamp').value = new Date().toISOString().substring(0, 16);

        function showLoading(title = "Running QA Audit Compliance...") {
            loadingOverlay.style.display = 'flex';
            loadingText.textContent = title;
            let phaseIndex = 0;
            loadingSubtext.textContent = loadingPhases[phaseIndex];
            phaseInterval = setInterval(() => {
                phaseIndex = (phaseIndex + 1) % loadingPhases.length;
                loadingSubtext.textContent = loadingPhases[phaseIndex];
            }, 3000);
        }

        function hideLoading() {
            clearInterval(phaseInterval);
            loadingOverlay.style.display = 'none';
        }

        function toggleForm() {
            if (formContent.style.display === 'grid') {
                formContent.style.display = 'none';
                formToggleIcon.textContent = '▼';
            } else {
                formContent.style.display = 'grid';
                formToggleIcon.textContent = '▲';
            }
        }

        let pollingInterval = null;

        function startPolling() {
            if (pollingInterval) return;
            pollingInterval = setInterval(async () => {
                await loadLogs();
                const stillAuditing = globalLogs.some(log => log[14] === 'AUDITING');
                if (!stillAuditing) {
                    stopPolling();
                }
            }, 5000);
        }

        function stopPolling() {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }

        // Fetch logs and update the table
        async function loadLogs() {
            try {
                const res = await fetch('/api/logs');
                const data = await res.json();
                globalLogs = data.logs;
                renderLogs(data.logs);
                
                const isAuditing = data.logs.some(log => log[14] === 'AUDITING');
                if (isAuditing) {
                    startPolling();
                } else {
                    stopPolling();
                }
            } catch (err) {
                console.error("Error fetching logs:", err);
            }
        }

        function renderLogs(logs) {
            logsBody.innerHTML = '';
            
            if (logs.length === 0) {
                emptyState.style.display = 'block';
                statTotal.textContent = 0;
                statPass.textContent = 0;
                statFail.textContent = 0;
                statPending.textContent = 0;
                btnAuditAll.style.display = 'none';
                return;
            }

            emptyState.style.display = 'none';
            let passedCount = 0;
            let failedCount = 0;
            let pendingCount = 0;
            let actualPendingCount = 0;

            logs.forEach(log => {
                const [
                    batchId, timestamp, lineName, materialId, vendorCert, materialStorage,
                    isAllergen, allergenCompliant, freezerId, freezerTemp,
                    cipEquip, cipStep, cipTemp, microSwab, status, feedback
                ] = log;

                if (status === 'PASS') passedCount++;
                else if (status === 'FAIL') failedCount++;
                else {
                    pendingCount++;
                    if (status === 'PENDING') {
                        actualPendingCount++;
                    }
                }

                // Main Row
                const mainRow = document.createElement('tr');
                mainRow.className = 'tr-log-row';
                mainRow.onclick = (e) => {
                    // Check if they clicked action buttons or icons
                    if (e.target.closest('button') || e.target.closest('.btn-icon')) return;
                    toggleDetails(batchId);
                };

                let badgeClass = 'badge-pending';
                if (status === 'PASS') badgeClass = 'badge-pass';
                else if (status === 'FAIL') badgeClass = 'badge-fail';
                else if (status === 'AUDITING') badgeClass = 'badge-auditing';

                // Display key fields
                const formattedTemp = freezerTemp !== null ? `${freezerTemp}°C` : 'N/A';
                const formattedTime = timestamp ? timestamp.replace('T', ' ') : 'N/A';

                let actionHtml = '';
                if (status === 'PENDING') {
                    actionHtml = `<button class="btn-audit" onclick="runAudit('${batchId}')">🔍 Run Audit</button>`;
                } else if (status === 'AUDITING') {
                    actionHtml = `<button class="btn-audit" disabled style="opacity: 0.65; cursor: not-allowed; background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%); border-color: rgba(99, 102, 241, 0.4);"><span class="spinner-mini"></span> Auditing...</button>`;
                } else {
                    actionHtml = `<button class="btn-view-report" onclick="toggleDetails('${batchId}')">Report</button>`;
                }

                mainRow.innerHTML = `
                    <td style="font-weight: 600; color: #fff;">${batchId}</td>
                    <td>${formattedTime}</td>
                    <td>${lineName}</td>
                    <td>${microSwab}</td>
                    <td>${formattedTemp}</td>
                    <td><span class="badge ${badgeClass}">${status}</span></td>
                    <td>${actionHtml}</td>
                    <td style="text-align: right;">
                        <button class="btn-icon btn-icon-delete" onclick="deleteLog('${batchId}')" title="Delete record" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; padding: 0.4rem; border-radius: 6px; transition: all 0.2s ease;">
                            <svg width="15" height="15" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                            </svg>
                        </button>
                    </td>
                `;

                // Details Row
                const detailRow = document.createElement('tr');
                detailRow.id = `row-detail-${batchId}`;
                detailRow.className = 'detail-row';

                const isAllergenLabel = isAllergen === 'True' ? 'Yes' : 'No';
                const feedbackContent = feedback ? feedback : (status === 'AUDITING' ? "Compliance audit is in progress... DeepSeek-R1 is analyzing standard operating procedures and verifying compliance. Please wait." : "Pending safety audit. Click 'Run Audit' above to generate compliance analysis using vector store guidelines.");
                const feedbackClass = (feedback || status === 'AUDITING') ? "" : "feedback-pending";

                detailRow.innerHTML = `
                    <td colspan="8">
                        <div class="detail-wrapper">
                            <!-- Left: Detailed Params Grid -->
                            <div>
                                <div class="detail-column-title">📋 Operational Parameters</div>
                                <div class="params-list">
                                    <div class="param-item">
                                        <span class="param-label">Material ID</span>
                                        <span class="param-value">${materialId}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">Vendor Certification</span>
                                        <span class="param-value">${vendorCert}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">Material Storage</span>
                                        <span class="param-value">${materialStorage}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">Is Allergen</span>
                                        <span class="param-value">${isAllergenLabel}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">Allergen Compliant</span>
                                        <span class="param-value">${allergenCompliant}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">Freezer Unit</span>
                                        <span class="param-value">${freezerId}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">CIP Equipment</span>
                                        <span class="param-value">${cipEquip}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">CIP Step</span>
                                        <span class="param-value">${cipStep}</span>
                                    </div>
                                    <div class="param-item">
                                        <span class="param-label">CIP Temp</span>
                                        <span class="param-value">${cipTemp !== null ? `${cipTemp}°C` : 'N/A'}</span>
                                    </div>
                                </div>
                            </div>
                            <!-- Right: AI Reasoning Feedback -->
                            <div>
                                <div class="detail-column-title">🤖 AI QA Auditor Report</div>
                                <div class="feedback-box ${feedbackClass}">${feedbackContent}</div>
                            </div>
                        </div>
                    </td>
                `;

                logsBody.appendChild(mainRow);
                logsBody.appendChild(detailRow);
            });

            // Update Header Buttons
            if (actualPendingCount > 0) {
                btnAuditAll.style.display = 'inline-flex';
                btnAuditAll.textContent = `⚡ Audit All Pending (${actualPendingCount})`;
            } else {
                btnAuditAll.style.display = 'none';
            }

            // Update stats
            statTotal.textContent = logs.length;
            statPass.textContent = passedCount;
            statFail.textContent = failedCount;
            statPending.textContent = pendingCount;
        }

        function toggleDetails(batchId) {
            const detailRow = document.getElementById(`row-detail-${batchId}`);
            if (detailRow.style.display === 'table-row') {
                detailRow.style.display = 'none';
            } else {
                // Close other open detail rows
                document.querySelectorAll('.detail-row').forEach(row => {
                    row.style.display = 'none';
                });
                detailRow.style.display = 'table-row';
            }
        }

        // Audits a single batch
        async function runAudit(batchId) {
            try {
                const res = await fetch('/api/audit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ batch_id: batchId })
                });
                const data = await res.json();
                if (data.success) {
                    await loadLogs();
                } else {
                    alert("Audit failed to start: " + data.error);
                }
            } catch (err) {
                console.error("Error submitting audit:", err);
                alert("An error occurred during safety audit.");
            }
        }

        // Audits all pending batches in parallel (non-blocking)
        async function auditAllPending() {
            const pendingBatches = globalLogs.filter(log => log[14] === 'PENDING').map(log => log[0]);
            if (pendingBatches.length === 0) return;

            const promises = pendingBatches.map(batchId => 
                fetch('/api/audit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ batch_id: batchId })
                }).then(res => res.json())
            );

            try {
                await Promise.all(promises);
            } catch (err) {
                console.error("Error auditing all pending batches:", err);
            }

            await loadLogs();
        }

        // Handle Add Record Form
        async function submitForm(e) {
            e.preventDefault();
            const record = {
                batch_id: document.getElementById('batchId').value,
                timestamp: document.getElementById('timestamp').value,
                line_name: document.getElementById('lineName').value,
                material_id: document.getElementById('materialId').value,
                vendor_cert_status: document.getElementById('vendorCert').value,
                material_storage_status: document.getElementById('materialStorage').value,
                is_allergen: document.getElementById('isAllergen').value,
                allergen_storage_compliant: document.getElementById('allergenCompliant').value,
                freezer_id: document.getElementById('freezerId').value,
                freezer_temp_c: parseFloat(document.getElementById('freezerTemp').value),
                cip_equip: document.getElementById('cipEquip').value,
                cip_step: document.getElementById('cipStep').value,
                cip_temp_c: parseFloat(document.getElementById('cipTemp').value),
                micro_swab_result: document.getElementById('microSwab').value
            };

            showLoading("Saving Record...");

            try {
                const res = await fetch('/api/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(record)
                });
                const data = await res.json();
                if (data.success) {
                    addRecordForm.reset();
                    document.getElementById('timestamp').value = new Date().toISOString().substring(0, 16);
                    toggleForm(); // collapse form
                    await loadLogs();
                } else {
                    alert("Failed to save record: " + data.error);
                }
            } catch (err) {
                console.error("Error saving record:", err);
            } finally {
                hideLoading();
            }
        }

        // Delete Log
        async function deleteLog(batchId) {
            if (!confirm(`Delete record for Batch ${batchId}?`)) return;
            try {
                const res = await fetch('/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ batch_id: batchId })
                });
                const data = await res.json();
                if (data.success) {
                    await loadLogs();
                } else {
                    alert("Delete failed: " + data.error);
                }
            } catch (err) {
                console.error("Error deleting:", err);
            }
        }

        // Custom styling for delete buttons hover
        document.addEventListener('mouseover', (e) => {
            const btn = e.target.closest('.btn-icon-delete');
            if (btn) {
                btn.style.color = 'var(--danger)';
                btn.style.background = 'var(--danger-glow)';
            }
        });
        document.addEventListener('mouseout', (e) => {
            const btn = e.target.closest('.btn-icon-delete');
            if (btn) {
                btn.style.color = 'var(--text-secondary)';
                btn.style.background = 'none';
            }
        });

        // Load initially
        loadLogs();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/logs')
def get_logs():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                batch_id, timestamp, line_name, material_id, vendor_cert_status, material_storage_status, 
                is_allergen, allergen_storage_compliant, freezer_id, freezer_temp_c, 
                cip_equip, cip_step, cip_temp_c, micro_swab_result, status, agent_feedback 
            FROM shift_logs
        ''')
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"logs": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def perform_audit_async(batch_id):
    try:
        # Fetch full batch data from database
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shift_logs WHERE batch_id = ?", (batch_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        # Serialize full batch data into a clear QA report string
        query = (
            f"Audit Shift Log for Batch {row['batch_id']}:\n"
            f"- Timestamp: {row['timestamp']}\n"
            f"- Production Line: {row['line_name']}\n"
            f"- Material: {row['material_id']} (Vendor Certification: {row['vendor_cert_status']}, Storage Status: {row['material_storage_status']})\n"
            f"- Allergen Content: {'Yes' if row['is_allergen'].lower() in ['true', 'yes', '1'] else 'No'} (Storage Compliant: {row['allergen_storage_compliant']})\n"
            f"- Freezer Unit: {row['freezer_id']} (Recorded Temperature: {row['freezer_temp_c']}°C)\n"
            f"- CIP Cleaning Equipment: {row['cip_equip']} (Cleaning Step: {row['cip_step']}, Recorded Temperature: {row['cip_temp_c']}°C)\n"
            f"- Microbiological Swab Pathogen Test Result: {row['micro_swab_result']}\n\n"
            f"Please audit this operational data against the Food Safety SOPs in the vector store. Identify any compliance violations.\n"
            f"IMPORTANT FORMATTING INSTRUCTION: Begin your response with either 'STATUS: PASS' or 'STATUS: FAIL' "
            f"on a line by itself, then explain your reasoning step-by-step. If any critical limit is violated, state the required corrective action."
        )

        # Call RAG compliance auditor from agent.py
        agent_feedback = audit_sop_compliance.invoke(query)

        # Parse agent feedback to decide status
        if "STATUS: PASS" in agent_feedback:
            status = "PASS"
        elif "STATUS: FAIL" in agent_feedback:
            status = "FAIL"
        else:
            agent_lower = agent_feedback.lower()
            if "fail" in agent_lower or "quarantine" in agent_lower or "reprocess" in agent_lower or "violation" in agent_lower:
                if "does not fail" in agent_lower or "no action is required" in agent_lower or "met the critical limit" in agent_lower:
                    status = "PASS"
                else:
                    status = "FAIL"
            else:
                status = "PASS"

        # Update SQLite database with status and feedback
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE shift_logs SET status = ?, agent_feedback = ? WHERE batch_id = ?",
            (status, agent_feedback, batch_id)
        )
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error auditing batch {batch_id}: {e}")
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shift_logs SET status = 'FAIL', agent_feedback = ? WHERE batch_id = ?",
                (f"Error during safety audit: {str(e)}", batch_id)
            )
            conn.commit()
            conn.close()
        except Exception as db_err:
            print(f"Failed to update database after error: {db_err}")

@app.route('/api/audit', methods=['POST'])
def run_audit():
    try:
        data = request.json
        batch_id = str(data.get('batch_id'))

        # Fetch full batch data from database to check existence
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shift_logs WHERE batch_id = ?", (batch_id,))
        exists = cursor.fetchone()[0] > 0
        conn.close()

        if not exists:
            return jsonify({"success": False, "error": f"Batch {batch_id} not found."}), 404

        # Set status to AUDITING in database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE shift_logs SET status = 'AUDITING', agent_feedback = NULL WHERE batch_id = ?",
            (batch_id,)
        )
        conn.commit()
        conn.close()

        # Spawn asynchronous thread for the compliance agent
        thread = threading.Thread(target=perform_audit_async, args=(batch_id,))
        thread.start()

        return jsonify({"success": True, "status": "AUDITING"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/add', methods=['POST'])
def add_record():
    try:
        data = request.json
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO shift_logs (
                batch_id, timestamp, line_name, material_id, vendor_cert_status, 
                material_storage_status, is_allergen, allergen_storage_compliant, 
                freezer_id, freezer_temp_c, cip_equip, cip_step, cip_temp_c, 
                micro_swab_result, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
        ''', (
            str(data.get('batch_id')),
            str(data.get('timestamp')),
            str(data.get('line_name')),
            str(data.get('material_id')),
            str(data.get('vendor_cert_status')),
            str(data.get('material_storage_status')),
            str(data.get('is_allergen')),
            str(data.get('allergen_storage_compliant')),
            str(data.get('freezer_id')),
            float(data.get('freezer_temp_c')) if data.get('freezer_temp_c') is not None else None,
            str(data.get('cip_equip')),
            str(data.get('cip_step')),
            float(data.get('cip_temp_c')) if data.get('cip_temp_c') is not None else None,
            str(data.get('micro_swab_result'))
        ))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_log():
    try:
        data = request.json
        batch_id = data.get('batch_id')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shift_logs WHERE batch_id = ?", (batch_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
    app.run(debug=True, port=5000)
