import yt_dlp

url = "https://www.instagram.com/reel/C8qXYN5o1uA/"  # Sample IG reel
ydl_opts = {
    'quiet': True,
    'format': 'best',
    'no_check_certificate': True,
    'user_agent': 'Mozilla/5.0'
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(url, download=False)
    formats = info.get('formats', [])
    
    print("URL field:")
    print(info.get('url'))
    
    print("\nFormats dump:")
    for f in formats:
        print(f"ID: {f.get('format_id')}, Ext: {f.get('ext')}, vcodec: {f.get('vcodec')}, acodec: {f.get('acodec')}, url: len={len(f.get('url', ''))}")
