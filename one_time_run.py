import shutil, tempfile, pathlib
import os  # needed for directory walking
from seleniumwire import webdriver

# ───────────────────────────────────────────────
# 1)  CONFIGURE WHERE THE SOURCE PROFILE LIVES
# ───────────────────────────────────────────────
SRC_ROOT      = pathlib.Path(
    r"C:\Users\waniaaslam\AppData\Local\Google\Chrome\User Data"
)
PROFILE_NAME  = "Profile 1"                # the folder that already trusts Selenium-Wire’s CA
# ───────────────────────────────────────────────
# 2)  BUILD A CLEAN TEMPORARY COPY (no sockets)
# ───────────────────────────────────────────────
DST_ROOT = pathlib.Path(tempfile.mkdtemp(prefix="sw-user-data-"))
print("Creating isolated user-data dir at:", DST_ROOT)

# 2-A. Copy the top-level “Local State” file (it holds profile list, prefs, etc.)
shutil.copy2(SRC_ROOT / "Local State", DST_ROOT / "Local State")

# 2-B. Copy only the chosen profile folder, *ignoring* caches + lockfiles
src_profile = SRC_ROOT / PROFILE_NAME
dst_profile = DST_ROOT / PROFILE_NAME

ignore_these = shutil.ignore_patterns(
    "Cache*", "Code Cache", "GPUCache", "Media Cache",
    "Singleton*", "RunningChromeVersion"
)

# Manually copy profile to skip locked files
dst_profile.mkdir(parents=True, exist_ok=True)
for root, dirs, files in os.walk(src_profile):
    root_path = pathlib.Path(root)
    rel = root_path.relative_to(src_profile)
    dest_dir = dst_profile / rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    names = dirs + files
    ignored = ignore_these(root, names)
    # modify dirs in-place to skip ignored subdirectories
    dirs[:] = [d for d in dirs if d not in ignored]
    for f in files:
        if f in ignored:
            continue
        src_file = root_path / f
        dest_file = dest_dir / f
        try:
            shutil.copy2(src_file, dest_file)
        except PermissionError:
            print(f"[WARN] Skipping locked file {src_file}")
        except Exception:
            raise

# ───────────────────────────────────────────────
# 3)  LAUNCH SELENIUM-WIRE WITH THE CLONED PROFILE
# ───────────────────────────────────────────────
chrome_opts = webdriver.ChromeOptions()
chrome_opts.add_argument(f"--user-data-dir={DST_ROOT}")       # ← unique dir (no lock clash)
chrome_opts.add_argument(f"--profile-directory={PROFILE_NAME}")
chrome_opts.add_argument("--start-maximized")
chrome_opts.add_argument("--disable-popup-blocking")

driver = webdriver.Chrome(
    options=chrome_opts,
    seleniumwire_options={"verify_ssl": False}                 # ignore upstream SSL errors
)

print("✓ WebDriver started — HTTPS padlock should be green, requests capturable.")
