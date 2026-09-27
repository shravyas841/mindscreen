"""
HISTORICAL / INVALID PATH — DO NOT RUN OR CITE AS CURRENT EVIDENCE.

DAIC-WOZ COVAREP Feature Downloader
Downloads only the small acoustic feature CSV files (~300MB total)
NOT the huge raw audio/video files.

Run: python download_daicwoz.py --user YOUR_USERNAME --password YOUR_PASSWORD
"""
import os
import requests
import argparse
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://dcapswoz.ict.usc.edu/wwwedaic"
SAVE_DIR = r"c:\Users\shwet\OneDrive\Desktop\major project antigravity\daic_woz_features"

def get_participant_ids(session, label_csv_url):
    """Download train_split.csv to get participant IDs"""
    r = session.get(label_csv_url)
    r.raise_for_status()
    lines = r.text.strip().split('\n')
    ids = []
    for line in lines[1:]:  # skip header
        parts = line.split(',')
        if parts:
            try:
                ids.append(int(parts[0].strip()))
            except:
                pass
    return ids

def download_file(session, url, save_path):
    """Download a single file with progress bar"""
    r = session.get(url, stream=True)
    if r.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user',     required=True,  help='USC ICT username from approval email')
    parser.add_argument('--password', required=True,  help='USC ICT password from approval email')
    parser.add_argument('--max',      type=int, default=60, help='Max participants to download (default: 60)')
    args = parser.parse_args()

    session = requests.Session()
    session.auth = (args.user, args.password)  # HTTP Basic Auth

    print("🔐 Authenticating with USC ICT server...")
    test = session.get(f"{BASE_URL}/?dir=labels")
    if test.status_code == 401:
        print("❌ Authentication failed. Check your username and password.")
        return
    elif test.status_code != 200:
        print(f"❌ Server error: {test.status_code}")
        return
    print("✅ Authenticated successfully!")

    # Download label CSV files first
    print("\n📋 Downloading label files...")
    label_files = ['train_split.csv', 'dev_split.csv', 'Detailed_PHQ8_Labels.csv']
    for lf in label_files:
        url = f"{BASE_URL}/?dir=labels&file={lf}"
        save_path = os.path.join(SAVE_DIR, 'labels', lf)
        if download_file(session, url, save_path):
            print(f"  ✅ {lf}")
        else:
            # try alternate URL pattern
            url2 = f"{BASE_URL}/labels/{lf}"
            if download_file(session, url2, save_path):
                print(f"  ✅ {lf}")
            else:
                print(f"  ⚠️  Could not download {lf} — skipping")

    # Get participant IDs from train_split.csv
    train_csv_path = os.path.join(SAVE_DIR, 'labels', 'train_split.csv')
    participant_ids = []
    if os.path.exists(train_csv_path):
        with open(train_csv_path) as f:
            for line in f.readlines()[1:]:
                try:
                    participant_ids.append(int(line.split(',')[0].strip()))
                except:
                    pass
    
    if not participant_ids:
        # fallback: use known ID range from DAIC-WOZ
        participant_ids = list(range(300, 492))

    participant_ids = participant_ids[:args.max]
    print(f"\n🎙️  Downloading COVAREP features for {len(participant_ids)} participants...")
    print(f"💾 Saving to: {SAVE_DIR}\n")

    success_count = 0
    fail_count = 0

    for pid in tqdm(participant_ids, desc="Downloading"):
        folder = f"{pid}_P"
        covarep_file = f"{pid}_COVAREP.csv"
        
        # Try known URL patterns
        urls_to_try = [
            f"{BASE_URL}/data/{folder}/{covarep_file}",
            f"{BASE_URL}/?dir=data/{folder}&file={covarep_file}",
        ]
        
        save_path = os.path.join(SAVE_DIR, 'covarep', covarep_file)
        
        downloaded = False
        for url in urls_to_try:
            if download_file(session, url, save_path):
                downloaded = True
                success_count += 1
                break
        
        if not downloaded:
            fail_count += 1
            tqdm.write(f"  ⚠️  Could not download {pid} — may not exist or URL pattern differs")

    print(f"\n✅ Done! Downloaded {success_count} COVAREP files.")
    print(f"⚠️  Failed: {fail_count}")
    print(f"📁 Files saved to: {SAVE_DIR}")
    print("\n📌 Next step: Tell your AI assistant to train the model using these files!")

if __name__ == "__main__":
    main()
