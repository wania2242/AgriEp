import datetime
import os

results = []

def log_success(step, source='workorder'):
    results.append({'step': step, 'status': 'success', 'error': '', 'timestamp': datetime.datetime.now(), 'source': source or ''})

def log_failure(step, error, source=None):
    results.append({'step': step, 'status': 'failure', 'error': str(error), 'timestamp': datetime.datetime.now(), 'source': source or ''})

def write_html_report():
    now = datetime.datetime.now()
    filename = f"testing_result_{now.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'success')
    failed = total - passed
    sources = ['bc', 'login', 'workorder']
    source_titles = {'bc': 'BC', 'login': 'Login', 'workorder': 'Workorder'}
    source_colors = {
        'bc': '#e3f2fd',
        'login': '#e8f5e9',
        'workorder': '#fff3e0',
        '': '#f5f5f5'
    }
    status_colors = {
        'success': '#43a047',
        'failure': '#e53935'
    }
    with open(filename, "w") as f:
        f.write(f"""
<html>
<head>
    <title>Test Report</title>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
        html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f7fa;
        }}
        body {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            width: 100vw;
            min-height: 100vh;
            box-sizing: border-box;
        }}
        h1 {{
            margin-top: 32px;
            color: #1565c0;
            font-size: 2.5rem;
            letter-spacing: 1px;
        }}
        .summary {{
            margin: 16px 0 32px 0;
            font-size: 1.2rem;
            color: #333;
        }}
        .section-title {{
            margin-top: 40px;
            margin-bottom: 10px;
            font-size: 1.5rem;
            color: #1976d2;
            letter-spacing: 0.5px;
        }}
        table {{
            border-collapse: collapse;
            width: 90vw;
            max-width: 1200px;
            background: #fff;
            box-shadow: 0 2px 16px rgba(0,0,0,0.08);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 32px;
        }}
        th, td {{
            padding: 14px 18px;
            text-align: left;
        }}
        th {{
            background: #1976d2;
            color: #fff;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
        }}
        tr {{
            transition: background 0.2s;
        }}
        tr:hover {{
            background: #f1f8ff;
        }}
        .status-success {{
            color: #fff;
            background: #43a047;
            border-radius: 6px;
            padding: 4px 12px;
            font-weight: 600;
            display: inline-block;
        }}
        .status-failure {{
            color: #fff;
            background: #e53935;
            border-radius: 6px;
            padding: 4px 12px;
            font-weight: 600;
            display: inline-block;
        }}
        .source-bc {{ background: #e3f2fd; }}
        .source-login {{ background: #e8f5e9; }}
        .source-workorder {{ background: #fff3e0; }}
        .source-unknown {{ background: #f5f5f5; }}
        .nowrap {{ white-space: nowrap; }}
        @media (max-width: 700px) {{
            table, th, td {{ font-size: 0.95rem; }}
            h1 {{ font-size: 1.5rem; }}
        }}
        pre {{
            margin: 0;
            font-size: 0.95em;
            color: #b71c1c;
            background: #fbe9e7;
            border-radius: 4px;
            padding: 6px 8px;
            max-width: 400px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class='container'>
        <h1>Test Report - {now.strftime('%Y-%m-%d %H:%M:%S')}</h1>
        <div class='summary'>
            <b>Total:</b> {total} &nbsp; <b>Passed:</b> <span style='color:#43a047'>{passed}</span> &nbsp; <b>Failed:</b> <span style='color:#e53935'>{failed}</span>
        </div>
""")
        for source in sources:
            source_results = [r for r in results if r['source'] == source]
            if not source_results:
                continue
            f.write(f"<div class='section-title'>{source_titles[source]} Results</div>")
            f.write("""
            <table>
                <tr>
                    <th>Step</th>
                    <th>Status</th>
                    <th>Error</th>
                    <th class='nowrap'>Time</th>
                </tr>
            """)
            for r in source_results:
                status_class = f"status-{r['status']}"
                f.write(f"<tr class='source-{source}'>")
                f.write(f"<td>{r['step']}</td>")
                f.write(f"<td><span class='{status_class}'>{r['status'].capitalize()}</span></td>")
                f.write(f"<td><pre>{r['error']}</pre></td>")
                f.write(f"<td class='nowrap'>{r['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</td>")
                f.write("</tr>\n")
            f.write("</table>")
        f.write("""
    </div>
</body>
</html>
""")
    print(f"Report written to {filename}") 