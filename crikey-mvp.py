import os
import tkinter as tk
from tkinter import filedialog, messagebox
from functools import partial
from threading import Thread
from googleapiclient.discovery import build
import openai
import whisper

# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# Backend functions
def fetch_youtube_captions(video_url):
    try:
        video_id = video_url.split("v=")[-1].split("&")[0]
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        captions = youtube.captions().list(videoId=video_id, part="snippet").execute()
        for item in captions.get("items", []):
            if "en" in item["snippet"]["language"]:
                caption_id = item["id"]
                return download_caption_text(youtube, caption_id)
        return "No English captions available for this video."
    except Exception as e:
        return f"Error fetching YouTube captions: {e}"


def download_caption_text(youtube, caption_id):
    try:
        caption_response = youtube.captions().download(id=caption_id).execute()
        return caption_response.decode("utf-8")
    except Exception as e:
        return f"Error downloading caption text: {e}"


def transcribe_audio(file_path):
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        return result['text']
    except Exception as e:
        return f"Error transcribing audio: {e}"


def generate_blog_content(transcript, style, audience):
    try:
        prompt = (
            f"Transform the following transcript into a blog post. "
            f"Style: {style}. Audience: {audience}. "
            f"Transcript: {transcript}"
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error generating blog content: {e}"


def process_video(video_url=None, file_path=None, style="informative", audience="general"):
    transcript = None
    if video_url:
        transcript = fetch_youtube_captions(video_url)
    elif file_path:
        transcript = transcribe_audio(file_path)
    else:
        return "No valid input provided."

    if not transcript or "Error" in transcript:
        return transcript

    return generate_blog_content(transcript, style, audience)


# Tkinter GUI
def generate_blog(video_url_entry, audio_path_var, style_entry, audience_entry, result_text):
    video_url = video_url_entry.get()
    audio_path = audio_path_var.get()
    style = style_entry.get()
    audience = audience_entry.get()

    if not (video_url or audio_path):
        messagebox.showerror("Input Error", "Please provide a YouTube URL or select an audio file.")
        return

    def run_processing():
        result = process_video(video_url, audio_path, style, audience)
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, result)
        result_text.config(state=tk.DISABLED)

    Thread(target=run_processing).start()


def browse_file(audio_path_var):
    file_path = filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.mp3;*.wav"), ("All Files", "*.*")]
    )
    audio_path_var.set(file_path)


def create_gui():
    root = tk.Tk()
    root.title("YouTube to Blog Generator")

    # YouTube URL
    tk.Label(root, text="YouTube Video URL:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
    video_url_entry = tk.Entry(root, width=50)
    video_url_entry.grid(row=0, column=1, padx=10, pady=5)

    # Audio File
    tk.Label(root, text="Audio File:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
    audio_path_var = tk.StringVar()
    audio_path_entry = tk.Entry(root, textvariable=audio_path_var, width=40)
    audio_path_entry.grid(row=1, column=1, padx=10, pady=5)
    tk.Button(root, text="Browse", command=partial(browse_file, audio_path_var)).grid(row=1, column=2, padx=5, pady=5)

    # Blog Style
    tk.Label(root, text="Blog Style:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
    style_entry = tk.Entry(root, width=50)
    style_entry.grid(row=2, column=1, padx=10, pady=5)

    # Audience
    tk.Label(root, text="Audience:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
    audience_entry = tk.Entry(root, width=50)
    audience_entry.grid(row=3, column=1, padx=10, pady=5)

    # Generate Button
    result_text = tk.Text(root, height=15, width=70, state=tk.DISABLED)
    result_text.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

    tk.Button(
        root,
        text="Generate Blog",
        command=partial(generate_blog, video_url_entry, audio_path_var, style_entry, audience_entry, result_text),
    ).grid(row=4, column=1, pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()