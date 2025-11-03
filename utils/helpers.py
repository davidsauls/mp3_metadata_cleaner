# utils/helpers.py
import os
from datetime import datetime

DEBUG = True

def debug_log(message, data=None):
    if DEBUG:
        print(f"[DEBUG] {message}")
        if data:
            print(data)

def format_duration(ms):
    if not ms:
        return "0:00"
    seconds = ms // 1000
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

def safe_decode(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return str(value)

def compute_year(release_date):
    if release_date:
        try:
            return datetime.fromisoformat(release_date.replace('Z', '+00:00')).year
        except:
            return 'Unknown'
    return 'Unknown'

    