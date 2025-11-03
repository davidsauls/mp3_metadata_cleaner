# metadata/tag_updater.py
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCON, TRCK, APIC
import requests
from utils.helpers import debug_log

def update_mp3_metadata(file_path, apple_meta):
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        tags = audio.tags

        # Text fields
        tags["TIT2"] = TIT2(encoding=3, text=apple_meta['title'])
        tags["TPE1"] = TPE1(encoding=3, text=apple_meta['artist'])
        tags["TALB"] = TALB(encoding=3, text=apple_meta['album'])
        tags["TYER"] = TYER(encoding=3, text=str(apple_meta['year']))
        tags["TCON"] = TCON(encoding=3, text=apple_meta['genre'])
        tags["TRCK"] = TRCK(encoding=3, text=str(apple_meta['track']))

        # Artwork
        # Artwork – REMOVE ALL APIC frames first
        if apple_meta.get('album_art_url'):
            art_data = requests.get(apple_meta['album_art_url'], timeout=10).content
            
            # ← FIX: Remove ALL APIC frames (there can be multiple!) # Remove ALL existing cover art
            for key in list(tags.keys()):
                if key.startswith('APIC'):
                    del tags[key]

            # Add new front cover
            tags['APIC'] = APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,  # 3 = front cover
                desc='Cover',
                data=art_data
            )

        audio.save()
        debug_log('Metadata updated', file_path)
        return True
    except Exception as e:
        debug_log(f'Update failed: {e}')
        return False