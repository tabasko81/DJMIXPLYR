#!/usr/bin/env python3
"""
Script to update the offline MP3 player.
Scans the mp3/ folder, extracts ID3 metadata and regenerates index.html.
"""

import json
import base64
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

# Configuration
MP3_FOLDER = Path('mp3')
HTML_FILE = Path('index.html')


def extract_cover_art(mp3_file):
    """
    Extracts album cover from MP3 file and returns as base64 data URI.
    Returns None if no cover is found.
    """
    try:
        audio_file = File(str(mp3_file))
        if audio_file is None:
            return None

        # Try to extract image from different tags
        if hasattr(audio_file, 'tags') and audio_file.tags:
            for tag in ['APIC:', 'APIC', 'PIC', 'covr']:
                if tag in audio_file.tags:
                    artwork = audio_file.tags[tag]
                    if isinstance(artwork, list) and len(artwork) > 0:
                        artwork = artwork[0]
                    if hasattr(artwork, 'data'):
                        image_data = artwork.data
                        # Detect MIME type
                        mime_type = 'image/jpeg'
                        if image_data[:2] == b'\xff\xd8':
                            mime_type = 'image/jpeg'
                        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
                            mime_type = 'image/png'
                        elif image_data[:4] == b'GIF8':
                            mime_type = 'image/gif'
                        # Convert to base64 data URI
                        b64_data = base64.b64encode(image_data).decode('utf-8')
                        return f"data:{mime_type};base64,{b64_data}"
                    elif isinstance(artwork, bytes):
                        mime_type = 'image/jpeg'
                        b64_data = base64.b64encode(artwork).decode('utf-8')
                        return f"data:image/jpeg;base64,{b64_data}"

        # Try with mutagen ID3
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
        print(f"Error extracting cover from {mp3_file.name}: {e}")
    
    return None


def extract_metadata(mp3_file):
    """
    Extracts metadata from MP3 file.
    Returns dictionary with title, artist, cover and path.
    """
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

        # Extract title, artist and album
        if hasattr(audio_file, 'tags') and audio_file.tags:
            tags = audio_file.tags
            
            # Title
            for key in ['TIT2', 'TITLE', '©nam']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['title'] = str(value[0]).strip()
                    else:
                        metadata['title'] = str(value).strip()
                    break

            # Artist
            for key in ['TPE1', 'ARTIST', '©ART']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['artist'] = str(value[0]).strip()
                    else:
                        metadata['artist'] = str(value).strip()
                    break

            # Album
            for key in ['TALB', 'ALBUM', '©alb']:
                if key in tags:
                    value = tags[key]
                    if isinstance(value, list) and len(value) > 0:
                        metadata['album'] = str(value[0]).strip()
                    else:
                        metadata['album'] = str(value).strip()
                    break

        # Extract cover
        cover = extract_cover_art(mp3_file)
        if cover:
            metadata['cover'] = cover

        return metadata

    except Exception as e:
        print(f"Error processing {mp3_file.name}: {e}")
        return {
            'filename': mp3_file.stem,
            'title': None,
            'artist': None,
            'album': None,
            'cover': None,
            'path': f"mp3/{mp3_file.name}"
        }


def get_existing_tracks():
    """
    Reads existing tracks from HTML and returns as a list.
    """
    if not HTML_FILE.exists():
        return []
    
    try:
        with open(HTML_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find PLAYLIST_DATA constant
        start_idx = content.find('const PLAYLIST_DATA')
        if start_idx == -1:
            return []
        
        # Find the start of JSON array
        array_start = content.find('[', start_idx)
        if array_start == -1:
            return []
        
        # Find the end of array
        array_end = content.find('];', array_start)
        if array_end == -1:
            return []
        
        # Extract JSON
        json_str = content[array_start:array_end + 1]
        
        # Try to parse JSON
        try:
            existing_tracks = json.loads(json_str)
            return existing_tracks if isinstance(existing_tracks, list) else []
        except json.JSONDecodeError:
            return []
    except Exception as e:
        print(f"Warning: Error reading existing tracks: {e}")
        return []


def get_existing_playlist():
    """
    Reads current playlist from HTML and returns a set of normalized paths.
    """
    existing_tracks = get_existing_tracks()
    existing_paths = set()
    for track in existing_tracks:
        if 'path' in track:
            # Normalize path for comparison (lowercase)
            existing_paths.add(track['path'].lower().replace('\\', '/'))
    return existing_paths


def scan_mp3_files(existing_paths=None):
    """
    Scans the mp3/ folder and returns list of metadata.
    Avoids duplicates (important on Windows which is case-insensitive).
    If existing_paths is provided, only processes new files.
    """
    if existing_paths is None:
        existing_paths = set()
    
    if not MP3_FOLDER.exists():
        print(f"Folder {MP3_FOLDER} not found. Creating it...")
        MP3_FOLDER.mkdir(exist_ok=True)
        print(f"Folder {MP3_FOLDER} created. Add MP3 files and run again.")
        return []

    # Collect all MP3 files and avoid duplicates
    mp3_files_dict = {}  # {lowercase_name: Path}
    
    # Search for all .mp3 files (case-insensitive)
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    
    # Also search for .MP3 (in case there are uppercase extensions)
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        name_lower = mp3_file.name.lower()
        if name_lower not in mp3_files_dict:
            mp3_files_dict[name_lower] = mp3_file
    
    mp3_files = sorted(mp3_files_dict.values(), key=lambda x: x.name.lower())
    
    if not mp3_files:
        print(f"No MP3 files found in {MP3_FOLDER}")
        return []

    print(f"Found {len(mp3_files)} MP3 file(s)")
    
    new_tracks = []
    skipped_count = 0
    
    for mp3_file in mp3_files:
        # Check if already exists in playlist
        track_path = f"mp3/{mp3_file.name}"
        track_path_normalized = track_path.lower().replace('\\', '/')
        
        if track_path_normalized in existing_paths:
            print(f"Already in playlist: {mp3_file.name} (ignored)")
            skipped_count += 1
            continue
        
        print(f"New file found: {mp3_file.name}")
        metadata = extract_metadata(mp3_file)
        if metadata:
            new_tracks.append(metadata)
    
    if skipped_count > 0:
        print(f"\n{skipped_count} file(s) already in playlist (ignored)")
    
    return new_tracks


def get_current_mp3_files():
    """
    Returns a set of normalized paths of MP3 files currently in the folder.
    """
    if not MP3_FOLDER.exists():
        return set()
    
    current_files = set()
    
    # Search for all .mp3 files
    for mp3_file in MP3_FOLDER.glob('*.mp3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    
    # Search for .MP3 as well
    for mp3_file in MP3_FOLDER.glob('*.MP3'):
        path_normalized = f"mp3/{mp3_file.name}".lower().replace('\\', '/')
        current_files.add(path_normalized)
    
    return current_files


def update_html(new_tracks):
    """
    Updates index.html by adding new tracks at the top of the playlist
    and removing tracks whose files no longer exist.
    Replaces PLAYLIST_DATA content robustly.
    """
    if not HTML_FILE.exists():
        print(f"Error: {HTML_FILE} not found!")
        return False

    # Read existing tracks
    existing_tracks = get_existing_tracks()
    
    # Get MP3 files that currently exist in the folder
    current_files = get_current_mp3_files()
    
    # Filter existing tracks: keep only those that still have files
    valid_existing_tracks = []
    removed_count = 0
    
    for track in existing_tracks:
        if 'path' in track:
            track_path_normalized = track['path'].lower().replace('\\', '/')
            if track_path_normalized in current_files:
                valid_existing_tracks.append(track)
            else:
                removed_count += 1
                print(f"File removed: {track.get('filename', track['path'])}")
        else:
            # If no path, keep (shouldn't happen, but for safety)
            valid_existing_tracks.append(track)
    
    if removed_count > 0:
        print(f"\n{removed_count} track(s) removed from playlist (files not found)")
    
    # Combine: new tracks at top, then valid existing tracks
    all_tracks = new_tracks + valid_existing_tracks

    # Read existing HTML
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Create JSON from track data
    tracks_json = json.dumps(all_tracks, ensure_ascii=False, indent=2)
    
    # Find line containing "const PLAYLIST_DATA ="
    start_line_idx = None
    for i, line in enumerate(lines):
        if 'const PLAYLIST_DATA' in line and '=' in line:
            start_line_idx = i
            break
    
    if start_line_idx is None:
        print("Error: Could not find 'const PLAYLIST_DATA =' in HTML")
        return False
    
    # Find line containing "];" after start line
    # Search for first line after start_line_idx that contains only "];"
    end_line_idx = None
    for i in range(start_line_idx + 1, len(lines)):
        line_stripped = lines[i].strip()
        if line_stripped == '];':
            end_line_idx = i
            break
    
    if end_line_idx is None:
        print("Error: Could not find '];' after PLAYLIST_DATA in HTML")
        return False
    
    # Get indentation from original line
    start_line = lines[start_line_idx]
    indent = ''
    for char in start_line:
        if char in [' ', '\t']:
            indent += char
        else:
            break
    
    # Build new content
    # Replace everything between start_line_idx and end_line_idx
    new_lines = lines[:start_line_idx]
    
    # Create JSON with appropriate indentation
    # json.dumps already has indent=2
    json_lines = tracks_json.split('\n')
    
    if json_lines:
        # Check if first line is just '[' (empty array or start)
        if json_lines[0].strip() == '[':
            # First line: const PLAYLIST_DATA = [
            new_lines.append(f'{indent}const PLAYLIST_DATA = [\n')
            # Start from second line of JSON
            start_idx = 1
        else:
            # JSON in single line or different format
            new_lines.append(f'{indent}const PLAYLIST_DATA = {json_lines[0]}\n')
            start_idx = 1
        
        # Add JSON lines with base indentation
        # Check if last line is ']' to close correctly
        for i, json_line in enumerate(json_lines[start_idx:], start=start_idx):
            line_stripped = json_line.strip()
            
            # If last line and is ']', close with '];'
            if i == len(json_lines) - 1 and line_stripped == ']':
                new_lines.append(f'{indent}];\n')
            elif line_stripped:  # Non-empty lines
                new_lines.append(f'{indent}{json_line}\n')
            else:
                new_lines.append('\n')
    else:
        # If no data, just empty array
        new_lines.append(f'{indent}const PLAYLIST_DATA = [];\n')
    
    # Add rest after line with ];
    new_lines.extend(lines[end_line_idx + 1:])
    
    # Write updated HTML
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"HTML updated with {len(all_tracks)} track(s)")
    return True


def main():
    """
    Main function.
    """
    print("=== MP3 Player Updater ===\n")
    
    # Read existing playlist to identify new files
    existing_paths = get_existing_playlist()
    existing_count = len(existing_paths)
    
    if existing_count > 0:
        print(f"Current playlist contains {existing_count} track(s)\n")
    
    # Scan MP3 files (only new ones)
    new_tracks = scan_mp3_files(existing_paths)
    
    if new_tracks:
        print(f"\n{len(new_tracks)} new track(s) found")
    else:
        if existing_count == 0:
            print("\nNo tracks found. Check if there are MP3 files in mp3/ folder")
            return
        else:
            print("\nChecking for removed files...")

    # Update HTML (adds new ones at top and removes missing files)
    # Always update to check for removed files
    if update_html(new_tracks):
        # Get final count after update
        final_tracks = get_existing_tracks()
        final_count = len(final_tracks)
        
        print("\n✅ Player updated successfully!")
        if new_tracks:
            print(f"New tracks added: {len(new_tracks)}")
        if final_count != existing_count:
            removed = existing_count - (final_count - len(new_tracks))
            if removed > 0:
                print(f"Tracks removed: {removed}")
        print(f"Total tracks in playlist: {final_count}")
    else:
        print("\n❌ Error updating player")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
