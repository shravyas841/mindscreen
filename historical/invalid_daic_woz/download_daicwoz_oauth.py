"""
HISTORICAL / INVALID PATH — DO NOT RUN OR CITE AS CURRENT EVIDENCE.

DAIC-WOZ COVAREP Downloader — cookies.txt version
Uses the exported cookies.txt file from Chrome extension.
"""
import os, sys, requests, http.cookiejar
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from tqdm import tqdm

COOKIE_FILE = r"c:\Users\shwet\OneDrive\Desktop\major project antigravity\dcapswoz.ict.usc.edu_cookies.txt"
SAVE_DIR    = r"c:\Users\shwet\OneDrive\Desktop\major project antigravity\daic_woz_features"
BASE_URL    = "https://dcapswoz.ict.usc.edu/wwwedaic"

def load_cookies(cookie_file):
    jar = http.cookiejar.MozillaCookieJar()
    # The extension may add a header line we need to handle
    with open(cookie_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    # Ensure proper Netscape header
    if '# Netscape HTTP Cookie File' not in content:
        content = '# Netscape HTTP Cookie File\n' + content
    # Write fixed version to temp file
    tmp = cookie_file + '.fixed'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    jar.load(tmp, ignore_discard=True, ignore_expires=True)
    os.remove(tmp)
    return jar

def try_download(session, url, save_path):
    try:
        r = session.get(url, stream=True, timeout=30)
        if r.status_code == 200 and len(r.content) > 100:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
    except Exception as e:
        pass
    return False

def main():
    print("Loading cookies from file...")
    jar = load_cookies(COOKIE_FILE)
    session = requests.Session()
    session.cookies = jar
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'

    # Test auth
    print("Testing connection...")
    r = session.get(f"{BASE_URL}/?dir=data", timeout=15)
    print(f"Status: {r.status_code}")
    if r.status_code == 403:
        print("ERROR: Still getting 403. Cookies may be expired. Please re-export them from Chrome.")
        return
    if r.status_code != 200:
        print(f"ERROR: Unexpected status {r.status_code}")
        return
    print("Authenticated successfully!\n")

    # Download label files
    print("Downloading label CSV files...")
    label_files = {
        'train_split.csv':          f"{BASE_URL}/labels/train_split.csv",
        'dev_split.csv':            f"{BASE_URL}/labels/dev_split.csv",
        'Detailed_PHQ8_Labels.csv': f"{BASE_URL}/labels/Detailed_PHQ8_Labels.csv",
    }
    for fname, url in label_files.items():
        save_path = os.path.join(SAVE_DIR, 'labels', fname)
        if os.path.exists(save_path):
            print(f"  SKIP (exists): {fname}")
            continue
        if try_download(session, url, save_path):
            print(f"  OK: {fname}")
        else:
            # try alternate URL
            alt_url = f"{BASE_URL}/?dir=labels&file={fname}"
            if try_download(session, alt_url, save_path):
                print(f"  OK (alt): {fname}")
            else:
                print(f"  WARN: Could not download {fname}")

    # Get participant IDs
    train_path = os.path.join(SAVE_DIR, 'labels', 'train_split.csv')
    participant_ids = []
    if os.path.exists(train_path):
        with open(train_path) as f:
            for line in f.readlines()[1:]:
                try:
                    participant_ids.append(int(line.split(',')[0].strip()))
                except:
                    pass
    if not participant_ids:
        participant_ids = list(range(300, 492))

    participant_ids = participant_ids[:60]
    print(f"\nDownloading COVAREP features for {len(participant_ids)} participants...")
    print(f"Saving to: {SAVE_DIR}\n")

    # Probe first participant to find correct URL pattern
    test_pid = participant_ids[0]
    url_patterns = [
        f"{BASE_URL}/data/{test_pid}_P/{test_pid}_COVAREP.csv",
        f"{BASE_URL}/?dir=data/{test_pid}_P&file={test_pid}_COVAREP.csv",
        f"https://dcapswoz.ict.usc.edu/wwwedaic/data/{test_pid}_P/{test_pid}_COVAREP.csv",
    ]
    working_pattern = None
    for pat in url_patterns:
        r = session.get(pat, timeout=10)
        print(f"  Probing: {pat} -> {r.status_code} ({len(r.content)} bytes)")
        if r.status_code == 200 and len(r.content) > 100:
            working_pattern = pat.replace(str(test_pid), '{pid}').replace(f"{test_pid}_P", '{pid}_P')
            print(f"  Working pattern found: {working_pattern}")
            break

    if not working_pattern:
        print("\nERROR: Could not find a working URL pattern for COVAREP files.")
        print("Please share a direct file URL from the DAIC-WOZ portal.")
        return

    success, failed_ids = 0, []
    for pid in tqdm(participant_ids, desc="Downloading"):
        save_path = os.path.join(SAVE_DIR, 'covarep', f"{pid}_COVAREP.csv")
        if os.path.exists(save_path):
            success += 1
            continue
        url = working_pattern.replace('{pid}', str(pid)).replace('{pid}_P', f'{pid}_P')
        if try_download(session, url, save_path):
            success += 1
        else:
            failed_ids.append(pid)

    print(f"\n{'='*50}")
    print(f"Downloaded: {success} COVAREP files")
    print(f"Failed:     {len(failed_ids)}")
    if failed_ids:
        print(f"Failed IDs: {failed_ids[:10]}")
    print(f"\nFiles saved to:\n   {SAVE_DIR}")
    if success > 0:
        print("\nNEXT STEP: Ask your AI assistant to train the audio model on these files!")

if __name__ == "__main__":
    main()
