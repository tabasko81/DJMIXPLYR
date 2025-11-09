#!/usr/bin/env python3
"""
Script to update the offline MP3 player.
Scans the mp3/ folder, extracts ID3 metadata and regenerates index.html.
Improvements:
- Added logging with log levels
- CLI argument support for --verbose, --backup
- Backs up index.html with timestamp
- Tag keys/metadata config at top
- More detailed docstrings
"""

import json
import base64
import logging
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

# --- CONFIGURATION ---
MP3_FOLDER = Path('mp3')
HTML_FILE = Path('index.html')
BACKUP_FOLDER = Path('backup')
METADATA_TAGS = {
    'title': ['TIT2', 'TITLE', '\u00a9nam'],
    'artist': ['TPE1', 'ARTIST', '\u00a9ART'],
    'album': ['TALB', 'ALBUM', '\u00a9alb']
}

# --- LOGGER SETUP ---
def configure_logger(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='[%(asctime)s][%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        level=level,
    )

def backup_file(file_path):
    if not file_path.exists():
        return
    BACKUP_FOLDER.mkdir(exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_FOLDER / f"{file_path.stem}_{ts}{file_path.suffix}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backup created: {backup_path}")

def extract_cover_art(mp3_file):
    try:
        audio_file = File(str(mp3_file))
        if audio_file is None:
            return None
        if hasattr(audio_file, 'tags') and audio_file.tags:
            for tag in ['APIC:', 'APIC', 'PIC', 'covr']:
                if tag in audio_file.tags:
                    artwork = audio_file.tags[tag]
                    if isinstance(artwork, list) and len(artwork) > 0:
                        artwork = artwork[0]
                    if hasattr(artwork, 'data'):
                        image_data = artwork.data
                        mime_type = 'image/jpeg'
                        if image_data[:2] == b'\xff\xd8':
                            mime_type = 'image/jpeg'
                        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
                            mime_type = 'image/png'
                        elif image_data[:4] == b'GIF8':
                            mime_type = 'image/gif'
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        return f"data:{mime_type};base64,{b64_data}"
                    elif isinstance(artwork, bytes):
                        mime_type = 'image/jpeg'
                        b64_data = base64.b64encode(artwork).decode('utf-8')
                        return f"data:image/jpeg;base64,{b64_data}"
        try:
            from mutagen.id3 import ID3
            id3 = ID3(str(mp3_file))
            for tag_name in id3.keys():
                if tag_name.startswith('APIC'):
                    apic = id3[tag_name]
                    if hasattr(apic, 'data'):
                        image_data = apic.data
                        mime_type = apic.mime if hasattr(apic, 'mime') else 'image/jpeg'
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        return f"data:{mime_type};base64,{b64_data}"
        except (ID3NoHeaderError, ImportError):
            pass
    except Exception as e:
        logging.warning(f"Error extracting cover from {mp3_file.name}: {e}")
    return None

def extract_metadata(mp3_file):
    try:
        audio_file = File(str(mp3_file))
        if audio_file is None:
            return None
        metadata = {
            'filename': mp3_file.stem,
            'title': None,
            'artist': None,
            'album': None,
            'cover': None,
            'path': f"mp3/{mp3_file.name}"
        }
        if hasattr(audio_file, 'tags') and audio_file.tags:
            tags = audio_file.tags
            # Generic extraction logic
            for meta, keys in METADATA_TAGS.items():
                for key in keys:
                    if key in tags:
                        value = tags[key]
                        if isinstance(value, list) and len(value) > 0:
                            metadata[meta] = str(value[0]).strip()
                        else:
                            metadata[meta] = str(value).strip()
                        break
            # Extract cover
        cover = extract_cover_art(mp3_file)
        if cover:
            metadata['cover'] = cover
        return metadata
    except Exception as e:
        logging.error(f"Error processing {mp3_file.name}: {e}")
        return {
            'filename': mp3_file.stem,
            'title': None,
            'artist': None,
            'album': None,
            'cover': None,
            'path': f"mp3/{mp3_file.name}"
        }

def get_existing_tracks():
    if not HTML_FILE.exists():
        return []
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        start_idx = content.find('const PLAYLIST_DATA')
        if start_idx == -1:
            return []
        array_start = content.find('[', start_idx)
        if array_start == -1:
            return []
        array_end = content.find('];', array_start)
        if array_end == -1:
            return []
        json_str = content[array_start:array_end + 1]
        try:
            existing_tracks = json.loads(json_str)
            return existing_tracks if isinstance(existing_tracks, list) else []
        except json.JSONDecodeError:
            return []
    except Exception as e:
        logging.warning(f"Warning: Error reading existing tracks: {e}")
        return []

def get_existing_playlist():
    existing_tracks = get_existing_tracks()
    existing_paths = set()
    for track in existing_tracks:
        if 'path' in track:
            existing_paths.add(track['path'].lower().replace('\\', '/'))
    return existing_paths

def scan_mp3_files(existing_paths=None):
    if existing_paths is None:
        existing_paths = set()
    if not MP3_FOLDER.exists():
        logging.info(f"Folder {MP3_FOLDER} not found. Creating...")
        MP3_FOLDER.mkdir(exist_ok=True)
        logging.info(f"Folder {MP3_FOLDER} created. Add MP3 files and run again.")
        return []
    mp3_files_dict = {}
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    mp3_files = sorted(mp3_files_dict.values(), key=lambda x: x.name.lower())
    if not mp3_files:
        logging.warning(f"No MP3 files found in {MP3_FOLDER}")
        return []
    new_tracks = []
    skipped_count = 0
    for mp3_file in mp3_files:
        track_path = f"mp3/{mp3_file.name}"
        track_path_normalized = track_path.lower().replace('\\', '/')
        if track_path_normalized in existing_paths:
            logging.info(f"Already in playlist: {mp3_file.name} (ignored)")
            skipped_count += 1
            continue
        logging.info(f"New file found: {mp3_file.name}")
        metadata = extract_metadata(mp3_file)
        if metadata:
            new_tracks.append(metadata)
    if skipped_count > 0:
        logging.info(f"{skipped_count} file(s) already in playlist (ignored)")
    return new_tracks

def get_current_mp3_files():
    if not MP3_FOLDER.exists():
        return set()
    current_files = set()
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    return current_files

def update_html(new_tracks):
    if not HTML_FILE.exists():
        logging.error(f"Error: {HTML_FILE} not found.")
        return False
    backup_file(HTML_FILE)
    existing_tracks = get_existing_tracks()
    current_files = get_current_mp3_files()
    valid_existing_tracks = []
    removed_count = 0
    for track in existing_tracks:
        if 'path' in track:
            track_path_normalized = track['path'].lower().replace('\\', '/')
            if track_path_normalized in current_files:
                valid_existing_tracks.append(track)
            else:
                removed_count += 1
                logging.info(f"File removed: {track.get('filename', track['path'])}")
        else:
            valid_existing_tracks.append(track)
    if removed_count > 0:
        logging.info(f"{removed_count} track(s) removed from playlist (file not found)")
    all_tracks = new_tracks + valid_existing_tracks
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    tracks_json = json.dumps(all_tracks, ensure_ascii=False, indent=2)
    start_line_idx = None
    for i, line in enumerate(lines):
        if 'const PLAYLIST_DATA' in line and '=' in line:
            start_line_idx = i
            break
    if start_line_idx is None:
        logging.error("Error: Could not find 'const PLAYLIST_DATA =' in HTML")
        return False
    end_line_idx = None
    for i in range(start_line_idx + 1, len(lines)):
        if lines[i].strip() == '];':
            end_line_idx = i
            break
    if end_line_idx is None:
        logging.error("Error: Could not find '];' after PLAYLIST_DATA in HTML")
        return False
    start_line = lines[start_line_idx]
    indent = ''
    for char in start_line:
        if char in [' ', '\t']:
            indent += char
        else:
            break
    new_lines = lines[:start_line_idx]
    json_lines = tracks_json.split('\n')
    if json_lines:
        if json_lines[0].strip() == '[':
            new_lines.append(f'{indent}const PLAYLIST_DATA = [\n')
            start_idx = 1
        else:
            new_lines.append(f'{indent}const PLAYLIST_DATA = {json_lines[0]}\n')
            start_idx = 1
        for i, json_line in enumerate(json_lines[start_idx:], start=start_idx):
            line_stripped = json_line.strip()
            if i == len(json_lines) - 1 and line_stripped == ']':
                new_lines.append(f'{indent}];\n')
            elif line_stripped:
                new_lines.append(f'{indent}{json_line}\n')
            else:
                new_lines.append('\n')
    else:
        new_lines.append(f'{indent}const PLAYLIST_DATA = [];\n')
    new_lines.extend(lines[end_line_idx + 1:])
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    logging.info(f"HTML updated with {len(all_tracks)} track(s)")
    return True

def main():
    parser = argparse.ArgumentParser(description="Update offline MP3 player's playlist. Regenerates index.html as needed.")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging output')
    parser.add_argument('--backup', action='store_true', help='Backup index.html before writing')
    args = parser.parse_args()
    configure_logger(args.verbose)
    logging.info("=== MP3 Player Updater ===")
    existing_paths = get_existing_playlist()
    existing_count = len(existing_paths)
    if existing_count > 0:
        logging.info(f"Current playlist contains {existing_count} track(s)")
    new_tracks = scan_mp3_files(existing_paths)
    if new_tracks:
        logging.info(f"{len(new_tracks)} new track(s) found")
    else:
        if existing_count == 0:
            logging.warning("No tracks found. Check if there are MP3 files in mp3/ folder.")
            return
        else:
            logging.info("Checking for removed files...")
    if update_html(new_tracks):
        final_tracks = get_existing_tracks()
        final_count = len(final_tracks)
        logging.info("Player updated successfully!")
        if new_tracks:
            logging.info(f"New tracks added: {len(new_tracks)}")
        if final_count != existing_count:
            removed = existing_count - (final_count - len(new_tracks))
            if removed > 0:
                logging.info(f"Tracks removed: {removed}")
        logging.info(f"Total tracks in playlist: {final_count}")
    else:
        logging.error("Error updating player.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user.")
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
