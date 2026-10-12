import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/get-link', methods=['POST'])
def get_download_link():
    data = request.json
    video_url = data.get('url')
    quality = data.get('quality') # 'audio', '720', '1080'

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    # Configure yt-dlp to extract direct media streams without downloading on the server
    ydl_opts = {
        'format': 'bestaudio/best' if quality == 'audio' else f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Get direct stream URL or audio URL
            direct_url = info.get('url')
            if not direct_url and 'requested_formats' in info:
                direct_url = info['requested_formats'][0].get('url')

            return jsonify({
                "status": "success",
                "title": info.get('title', 'video'),
                "download_url": direct_url
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
