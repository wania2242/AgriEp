from pathlib import Path
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
import sqlite3
import pathlib

def clear_chrome_session(user_data_dir: str | pathlib.Path, profile_name: str):
    """
    Remove all per-site session data (cookies, local-storage, caches …) from the
    given Chrome profile but keep preferences, extensions and certificates.
    Call this *before* you launch WebDriver.
    """
    root = pathlib.Path(user_data_dir) / profile_name

    # ── FOLDERS ───────────────────────────────────────────────────────────────
    for folder in [
        "Session Storage",
        "Local Storage",
        "IndexedDB",
        "File System",
        "GPUCache",
        "Code Cache",
        "Cache",
        "Network/Cache",          # new Chrome layout
    ]:
        path = root / folder
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    # ── SQLITE FILES ─────────────────────────────────────────────────────────
    for file_ in [
        "Cookies",
        "Cookies-journal",
        "Login Data",
        "Login Data-journal",
        "Web Data",
        "Web Data-journal",
        "Network/Cookies",
        "Network/Cookies-journal",
    ]:
        path = root / file_
        if path.exists():
            try:
                path.unlink()
            except PermissionError:
                # If Chrome crashed, WAL/SHM may be open—truncate instead
                try:
                    with sqlite3.connect(path) as db:
                        db.execute("VACUUM;")
                except sqlite3.OperationalError:
                    pass

    # ── OPTIONAL:  quota tracker ─────────────────────────────────────────────
    for file_ in ["QuotaManager", "QuotaManager-journal"]:
        (root / file_).unlink(missing_ok=True)

    print(f"✓ Cleared session data in {root}")

USER_DATA_DIR = Path(r"/var/folders/8x/ry2vbrc56wv9tqqtfp0bdww80000gp/T/sw-user-data-pq3khzrl")
PROFILE_NAME  = "Profile 2"          # the same folder you copied earlier

driver_instance = None
clear_chrome_session(USER_DATA_DIR, PROFILE_NAME)
def get_driver():
    global driver_instance
    if driver_instance is None:
        opts = webdriver.ChromeOptions()
        opts.add_argument(f'--user-data-dir={USER_DATA_DIR}')
        opts.add_argument(f'--profile-directory={PROFILE_NAME}')
        opts.add_argument('--start-maximized')
        opts.add_argument('--disable-popup-blocking')
        opts.add_argument('--disable-http2')
        opts.add_argument('--disable-quic')           # turns off H3
        # ⬇ make Chrome talk plain HTTP/1.1 over the proxy
        opts.add_argument('--enable-features=NetworkServiceInProcess')
        # Add Windows compatibility flags to avoid DevToolsActivePort errors
        opts.add_argument('--disable-gpu')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--remote-debugging-port=9222')

        driver_instance = webdriver.Chrome(
            options=opts,
            seleniumwire_options={
            'disable_http2': True,                # <─ NEW in 5.x, mirrors the Chrome flag
            'request_storage': 'memory',          # speeds things up, optional
            })

        # network settings
        cdp = driver_instance.execute_cdp_cmd
        cdp('Network.setCacheDisabled',      {'cacheDisabled': True})
        cdp('Network.setBypassServiceWorker',{'bypass': True})
        driver_instance.scopes = ['.*']              # capture absolutely everything
        driver_instance.ignore_http_methods = []     # include OPTIONS, HEAD, etc.
        driver_instance.capture_content = True
    return driver_instance

def close_driver():
    global driver_instance
    if driver_instance is not None:
        driver_instance.quit()
        driver_instance = None 