import pandas as pd
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS 
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
import isodate

# Flask
app = Flask(__name__)
# CORS'u etkinleştir
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})  # Tüm kaynaklar için CORS izinleri

# YouTube API Key
api_key = "AIzaSyDsb_k0odbbaDN2H1HjFJ0zy-TnORNtn8g"
youtube = build("youtube", "v3", developerKey=api_key)

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


api_key = "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"
groq_client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")



def extract_video_id(youtube_url):
    """Extract video ID from different YouTube URL formats"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and shared URLs
        r'(?:embed\/)([0-9A-Za-z_-]{11})',   # Embed URLs
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',  # Shortened URLs
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',   # YouTube Shorts
        r'^([0-9A-Za-z_-]{11})$'  # Just the video ID
    ]
    
    youtube_url = youtube_url.strip()
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError("Could not extract video ID from URL")

@app.route('/summarize', methods=['POST'])
def summarize_youtube_video():
    """Fetch transcript and summarize"""
    try:
        # Get YouTube URL from request
        data = request.json
        youtube_url = data.get('youtube_url')
        if not youtube_url:
            return jsonify({"error": "YouTube URL is required"}), 400
        
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        
        # Fetch transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["tr"])
        full_transcript = " ".join([entry["text"] for entry in transcript_list])
        
        # Summarize transcript
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=7000, chunk_overlap=1000, length_function=len)
        texts = text_splitter.split_text(full_transcript)
        
        intermediate_summaries = []
        for i, text_chunk in enumerate(texts):
            # system_prompt = f"""You are an expert content summarizer. Create a detailed summary of section {i+1}."""
            system_prompt = f"""Siz uzman bir video içerik özetleyicisiniz. Verdiğim bölümün ayrıntılı türkçe dilinde bir özetini oluşturun {i+1}."""
            user_prompt = f"Text: {text_chunk}"
            
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8000
            )
            intermediate_summaries.append(response.choices[0].message.content)
        video_details = get_video_details(video_id)
        title, url, duration, language = video_details
        combined_summary = "\n\n".join(intermediate_summaries)
        csv_file = "youtube_dataset.csv"
        new_data = {
            "Title": title,
            "URL": url,
            "Duration (seconds)": duration,
            "Language": language,
            "Transcript": texts,
            "Summary": combined_summary
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
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
