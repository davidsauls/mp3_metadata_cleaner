# utils/confidence.py
import difflib
from utils.helpers import debug_log

def normalize(s):
    """Lowercase, strip, remove common noise"""
    if not s:
        return ""
    return s.lower().strip().replace(" - remastered", "").replace(" (remaster)", "")

def string_similarity(a, b):
    """Return 0–100 similarity score using difflib"""
    a_norm = normalize(a)
    b_norm = normalize(b)
    return int(difflib.SequenceMatcher(None, a_norm, b_norm).ratio() * 100)

def duration_match(mp3_ms, apple_ms, tolerance_ms=5000):
    """Return 0–100 score based on duration diff"""
    if not mp3_ms or not apple_ms:
        return 0
    diff = abs(mp3_ms - apple_ms)
    if diff <= 1000:
        return 100
    elif diff <= tolerance_ms:
        return max(0, 100 - int((diff / tolerance_ms) * 100))
    else:
        return 0

def calculate_confidence(mp3_meta, apple_meta):
    """
    Returns: (score: int 0–100, breakdown: dict)
    """
    weights = {
        'duration': 0.40,
        'title': 0.30,
        'artist': 0.20,
        'album': 0.10
    }

    scores = {
        'duration': duration_match(mp3_meta['duration_ms'], apple_meta['duration_ms']),
        'title': string_similarity(mp3_meta['title'], apple_meta['title']),
        'artist': string_similarity(mp3_meta['artist'], apple_meta['artist']),
        'album': string_similarity(mp3_meta['album'], apple_meta['album'])
    }

    total_score = sum(scores[k] * weights[k] for k in weights)
    total_score = round(total_score)

    debug_log("Confidence breakdown", scores)
    debug_log(f"Final confidence: {total_score}%")

    return total_score, scores