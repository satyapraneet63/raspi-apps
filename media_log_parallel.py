import os
import csv
import subprocess
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
MEDIA_DIR = "/media/media"
VALID_EXTENSIONS = (
    '.mkv', '.mp4', '.avi', '.mov', '.webm',
    '.m4b', '.mp3', '.flac', '.aac', '.ogg',
    '.opus', '.wav', '.mka', '.m4a'
)
TODAY = datetime.now().strftime("%Y-%m-%d")
CSV_FILE = f"media_log_{TODAY}.csv"
MAX_WORKERS = 4

# --- ffprobe logic ---
def get_ffprobe_data(filepath):
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration:format=bit_rate",
                "-show_entries", "stream=codec_type,codec_name,width,height",
                "-of", "json", filepath
            ],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)

        duration = float(data['format'].get('duration', 0))
        bitrate = int(data['format'].get('bit_rate', 0))
        vcodec = acodec = width = height = None

        for stream in data.get('streams', []):
            if stream['codec_type'] == 'video':
                vcodec = stream.get('codec_name')
                width = stream.get('width')
                height = stream.get('height')
            elif stream['codec_type'] == 'audio' and not acodec:
                acodec = stream.get('codec_name')

        return round(duration, 2), bitrate, vcodec or '', acodec or '', width or '', height or ''
    except Exception:
        return 0, 0, '', '', '', ''

# --- File processing function ---
def process_file(full_path, file):
    try:
        stat = os.stat(full_path)
        size_mb = round(stat.st_size / (1024 * 1024), 2)
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        duration, bitrate, vcodec, acodec, width, height = get_ffprobe_data(full_path)

        return [
            full_path, file, size_mb, mod_time,
            duration, bitrate, vcodec, acodec, width, height
        ]
    except FileNotFoundError:
        return None

# --- Walk media tree and collect targets ---
def collect_media_files(root_path):
    targets = []
    for dirpath, _, filenames in os.walk(root_path, followlinks=True):
        if '/books' in dirpath:
            continue  # Skip the books folder entirely
        for file in filenames:
            if file.lower().endswith(VALID_EXTENSIONS):
                full_path = os.path.join(dirpath, file)
                targets.append((full_path, file))
    return targets

# --- Main execution ---
def main():
    print(f"Scanning media in {MEDIA_DIR} ...")
    files = collect_media_files(MEDIA_DIR)
    print(f"Found {len(files)} media files. Processing with {MAX_WORKERS} threads...")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(process_file, fp, fn): (fp, fn) for fp, fn in files}
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                results.append(result)

    print(f"Writing results to {CSV_FILE} ...")
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'path', 'filename', 'size_mb', 'last_modified',
            'duration_sec', 'bitrate', 'video_codec', 'audio_codec', 'width', 'height'
        ])
        writer.writerows(results)

    print(f"✅ Done: {len(results)} entries written to {CSV_FILE}")

if __name__ == "__main__":
    main()

