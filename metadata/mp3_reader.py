# metadata/mp3_reader.py
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from utils.helpers import safe_decode, debug_log, format_duration
from io import BytesIO
from PIL import Image

def _extract_cover(tags):
    """Return front-cover (type 3) bytes, regardless of key name."""
    for key in tags.keys():
        if key.startswith('APIC'):
            apic = tags[key]
            if getattr(apic, 'type', None) == 3:
                debug_log('Found front cover', key)
                return apic.data
    debug_log('No front cover found')
    return None

def read_mp3_metadata(file_path):
    try:
        audio = MP3(file_path)
        tags = audio.tags if audio.tags else ID3()

        cover = _extract_cover(tags)
        # Fallback for ancient files that only have plain APIC
        if cover is None and 'APIC' in tags:
            cover = tags['APIC'].data

        metadata = {
            'title': safe_decode(tags.get('TIT2', [b'Unknown'])[0]) if tags.get('TIT2') else 'Unknown',
            'artist': safe_decode(tags.get('TPE1', [b'Unknown'])[0]) if tags.get('TPE1') else 'Unknown',
            'album': safe_decode(tags.get('TALB', [b'Unknown'])[0]) if tags.get('TALB') else 'Unknown',
            'year': safe_decode(tags.get('TYER', [b'Unknown'])[0]) if tags.get('TYER') else 'Unknown',
            'genre': safe_decode(tags.get('TCON', [b'Unknown'])[0]) if tags.get('TCON') else 'Unknown',
            'track': safe_decode(tags.get('TRCK', [b'Unknown'])[0]) if tags.get('TRCK') else 'Unknown',
            'file_path': file_path,
            'duration_ms': int(audio.info.length * 1000),
            'duration': format_duration(int(audio.info.length * 1000)),
            'cover_art_data': cover,
        }

        return metadata
    except Exception as e:
        debug_log(f'Error reading MP3: {e}')
        raise