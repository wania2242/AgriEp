import datetime
import os

results = []

def log_success(step):
    results.append({'step': step, 'status': 'success', 'error': '', 'timestamp': datetime.datetime.now()})

def log_failure(step, error):
    results.append({'step': step, 'status': 'failure', 'error': str(error), 'timestamp': datetime.datetime.now()})

def write_html_report():
    now = datetime.datetime.now()
    filename = f"testing_result_{now.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'success')
    failed = total - passed

    with open(filename, "w") as f:
        f.write(f"<html><head><title>Test Report</title></head><body>")
        f.write(f"<h1>Test Report - {now}</h1>")
        f.write(f"<p>Total: {total}, Passed: {passed}, Failed: {failed}</p>")
        # Optional: Add a bar chart here
        f.write("<table border='1'><tr><th>Step</th><th>Status</th><th>Error</th><th>Time</th></tr>")
        for r in results:
            color = "#cfc" if r['status'] == 'success' else "#fcc"
            f.write(f"<tr style='background:{color}'><td>{r['step']}</td><td>{r['status'].capitalize()}</td><td><pre>{r['error']}</pre></td><td>{r['timestamp']}</td></tr>")
        f.write("</table></body></html>")
    print(f"Report written to {filename}") 