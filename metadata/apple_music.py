# metadata/apple_music.py
import requests
from utils.helpers import debug_log, compute_year, format_duration
from utils.confidence import calculate_confidence  # <-- ADD THIS LINE

def search_apple_music(title, artist, duration_ms=None, full_mp3_meta=None):
    query = f"{title} {artist}".strip()
    url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=50"
    debug_log('Apple Music API', url)

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        tracks = [
            r for r in data.get('results', [])
            if r.get('wrapperType') == 'track' and r.get('kind') == 'song'
        ]

        # Sort by duration match first
        if duration_ms is not None:
            tracks.sort(key=lambda x: abs(x.get('trackTimeMillis', 0) - duration_ms))

        # Use full metadata if provided, otherwise fallback to minimal
        mp3_for_conf = full_mp3_meta or {
            'title': title,
            'artist': artist,
            'duration_ms': duration_ms or 0,
            'album': '',
            'year': '',
            'genre': '',
            'track': ''
        }

        enriched = []
        for r in tracks[:50]:
            apple = format_apple_track(r)
            score, _ = calculate_confidence(mp3_for_conf, apple)
            apple['confidence'] = score
            enriched.append(apple)

        return enriched

    except Exception as e:
        debug_log(f'Apple Music error: {e}')
        return []

def format_apple_track(track):
    return {
        'title': track.get('trackName', 'Unknown'),
        'artist': track.get('artistName', 'Unknown'),
        'album': track.get('collectionName', 'Unknown'),
        'year': compute_year(track.get('releaseDate')),
        'genre': track.get('primaryGenreName', 'Unknown'),
        'track': track.get('trackNumber', 'Unknown'),
        'duration': format_duration(track.get('trackTimeMillis', 0)),
        'duration_ms': track.get('trackTimeMillis', 0),
        'album_art_url': track.get('artworkUrl100', '').replace('100x100', '600x600', 1)
    }