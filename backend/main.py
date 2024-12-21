from flask import Flask, request, jsonify
from flask_cors import CORS 
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import isodate
from transformers import pipeline  # Hugging Face summarization pipeline
import os
import os
if not os.path.exists("./models"):
    os.makedirs("./models")

# Flask uygulamasını başlat
app = Flask(__name__)

# CORS'u etkinleştir
CORS(app)

# YouTube API Key
api_key = "AIzaSyDsb_k0odbbaDN2H1HjFJ0zy-TnORNtn8g"
youtube = build("youtube", "v3", developerKey=api_key)

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
# Hugging Face çeviri modeli
translator = pipeline("translation", model="Helsinki-NLP/opus-tatoeba-en-tr")


# Video detaylarını alacak fonksiyon
def get_video_details(video_id):
    try:
        request = youtube.videos().list(part="snippet,contentDetails", id=video_id)
        response = request.execute()
        if len(response["items"]) > 0:
            video_info = response["items"][0]
            title = video_info["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            iso_duration = video_info["contentDetails"]["duration"]
            duration = isodate.parse_duration(iso_duration).total_seconds()
            language = video_info["snippet"].get("defaultAudioLanguage", "N/A")
            return title, url, duration, language
    except Exception as e:
        print(f"Error fetching video details: {e}")
    return None

# Altyazı bilgilerini alacak fonksiyon
def get_video_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
    return None

# Flask API Endpoint: Video detayları ve özeti al
@app.route("/add_video", methods=["POST"])
def add_video():
    data = request.json
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "YouTube URL is required."}), 400

    video_id = youtube_url.split("v=")[-1]
    video_details = get_video_details(video_id)
    if not video_details:
        return jsonify({"error": "Could not fetch video details."}), 500

    title, url, duration, language = video_details
    transcript = get_video_transcript(video_id)
    if not transcript:
        return jsonify({"error": "Transcript not available."}), 500

    # Altyazıyı özetle
    summary = summarizer(transcript[:1000], max_length=300, min_length=30, do_sample=False)[0]["summary_text"]
    translated_summary = translator(summary)[0]["translation_text"]
    # Veriyi CSV'ye ekle
    csv_file = "youtube_dataset.csv"
    new_data = {
        "Title": title,
        "URL": url,
        "Duration (seconds)": duration,
        "Language": language,
        "Transcript": transcript,
        "Summary": translated_summary
    }

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=new_data.keys())

    # Yeni satırı eklemek için pd.concat() kullanılıyor
    new_row = pd.DataFrame([new_data])  # Yeni veriyi DataFrame olarak oluştur
    df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(csv_file, index=False)

    return jsonify({"message": "Video added successfully!", "data": new_data})

if __name__ == "__main__":
    app.run(debug=True)
