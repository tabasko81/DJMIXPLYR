# 🎵 DJMIXPLYR - Offline MP3 Player

**DJMIXPLYR** is a static offline MP3 player, developed in HTML/JavaScript with automatic updates via Python. Modern and minimalist interface, fully functional without a server.

## 📋 Features

- ✅ **Fully Offline** - Works without internet or server
- ✅ **Modern Interface** - Minimalist and responsive design
- ✅ **ID3 Metadata** - Extracts title, artist and album covers
- ✅ **Complete Controls** - Play, pause, seek, volume and navigation
- ✅ **Automatic Updates** - Python script regenerates HTML easily

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- Modern browser (Chrome, Firefox, Edge - latest 2 versions)

### 1. Install Python Dependencies

```bash
pip install mutagen
```

Or if using pip3:

```bash
pip3 install mutagen
```

### 2. Folder Structure

The project should have the following structure:

```
DJMIXPLYR/
├── index.html          # HTML Player (will be updated automatically)
├── update_player.py    # Update script
├── README.md          # This file
└── mp3/               # Folder with MP3 files
    ├── song1.mp3
    ├── song2.mp3
    └── ...
```

### 3. Add MP3 Files

Place your MP3 files in the `mp3/` folder. If the folder doesn't exist, the script will create it automatically.

## 📖 Usage

### Update the Player

Whenever you add, remove or modify MP3 files in the `mp3/` folder, run:

```bash
python update_player.py
```

Or:

```bash
python3 update_player.py
```

The script will:
1. Scan the `mp3/` folder for MP3 files
2. Extract ID3 metadata (title, artist, cover)
3. Update `index.html` with new tracks

### Open the Player

Open the `index.html` file in your browser. You can do this in several ways:

- **Double click** on `index.html`
- **Drag and drop** the file into the browser
- **Right click** → "Open with" → Browser

## 🎮 Controls

- **▶/⏸** - Play/Pause
- **⏮** - Previous track
- **⏭** - Next track
- **Progress bar** - Click to jump to a position
- **Volume slider** - Adjust volume
- **Track list** - Click a track to play it

## 🔧 Technical Features

### Supported Metadata

The script automatically extracts:
- **Title** (TIT2, TITLE, ©nam)
- **Artist** (TPE1, ARTIST, ©ART)
- **Album** (TALB, ALBUM, ©alb)
- **Album Cover** (APIC, PIC, covr)

If metadata is not available, the player shows the filename.

### Album Covers

Covers are extracted from MP3 files and embedded in HTML as base64 images, allowing them to work completely offline.

### Fallbacks

- If no metadata: shows the filename
- If no cover: shows 🎵 icon
- If no files: shows informative message

## 📝 Notes

- The player only works with local files (relative paths `mp3/...`)
- To work completely offline, all MP3 files must be in the `mp3/` folder
- HTML is regenerated every time you run `update_player.py`
- Manual changes to HTML may be lost when running the script

## 🐛 Troubleshooting

### "No MP3 files found"

Make sure:
- Files have `.mp3` or `.MP3` extension
- Files are in the `mp3/` folder (same directory as the script)

### Metadata doesn't appear

Some MP3 files may not have ID3 metadata. The player will show the filename in these cases.

### Covers don't appear

Not all MP3 files contain embedded covers. The player will show a default icon (🎵) when there's no cover.

### Error importing mutagen

Make sure you installed mutagen:
```bash
pip install mutagen
```

## 📄 License

Free project for personal use.

---

**Developed with ❤️ for offline music**
