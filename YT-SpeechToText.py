from pytube import YouTube 
import os
import math
import ffmpeg
import openai
import warnings
from pydub import AudioSegment
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send

# berk - 2023 - Youtube SpeechToText v2

program_active = True

# Close warnings
warnings.filterwarnings("ignore")

# Define paths
script_directory = os.path.dirname(os.path.abspath(__file__))
video_output_path = os.path.join(script_directory, 'tempfiles')
audio_output_path = os.path.join(script_directory, 'tempfiles')

# OpenAI API Key
openai.api_key = '#############################################'  

app = Flask(__name__)
CORS(app, support_credentials=True)

# Start of Functions #

# Downloading video (pytube)
def download_video(url, output_path):
    youtube = YouTube(url)
    video = youtube.streams.get_highest_resolution()
    video.download(output_path, filename="video.mp4")

# Convertion MP4->WAV (ffmpeg)
def convert_video_to_audio(video_path, audio_path):
    ffmpeg.input(video_path).output(audio_path, format='wav', y='-y').run()

# Splitting audio file to 25 MB parts (needed for OpenAI)
def split_audio_file(audio_path):
    MAX_SIZE = 25 * 1024 * 1024  # 25 MB (as bytes)

    audio = AudioSegment.from_wav(audio_path)
    file_size = len(audio.raw_data)

    num_parts = math.ceil(file_size / MAX_SIZE)

    parts = []
    for i in range(num_parts):
        start = int(i * len(audio) / num_parts)
        end = int((i + 1) * len(audio) / num_parts)
        part = audio[start:end]

        part_file_path = os.path.splitext(audio_path)[0] + f"_part{i}.wav"
        parts.append(part_file_path)
        part.export(part_file_path, format="wav")
        
    return parts

# Transcribe audio to text (OpenAI)
def transcribe_audio_openai_new(audio_parts):
    transcriptions = []
    for part in audio_parts:
        audio_file = open(part, "rb")
        response = openai.Audio.transcribe(
            file=audio_file,
            content_type='audio/wav',
            model = "whisper-1",
            response_format="text",
            language="tr"
        )

        transcription = response
        transcriptions.append(transcription)

    transcribed_text = ' '.join(transcriptions)
    txt_file = open('output.txt', 'w', encoding="utf-8")
    txt_file.write(transcribed_text)
    return transcribed_text

# Summarize text (OpenAI - inactive)
def generate_summary_openai(text):

    text = 'Bu metnin özetini çıkar: '+text
    response = openai.Completion.create(
        engine='text-davinci-003',  
        prompt=text,
        max_tokens=100,  
        temperature=0.3,  
        n=1,
        stop=None
    )
    summary = response.choices[0].text.strip()
    return summary

# Main function
def speechToText(link):

    download_video(link, video_output_path)
    
    print("1")
    
    if __name__ == '__main__':
        video_path = os.path.join(script_directory, 'tempfiles', 'video.mp4')
        audio_path = os.path.join(script_directory, 'tempfiles', 'video.wav')
        convert_video_to_audio(video_path, audio_path)
        
    print("2")
    
    audio_parts = split_audio_file(audio_path)
    
    print("3")

    transcribed_text = transcribe_audio_openai_new(audio_parts)
    
    print("4")

    return transcribed_text

@app.route('/')
def homepage():
    return 'YT-SpeechToText-v2'

@app.route('/speechToText', methods=['POST'])
@cross_origin(supports_credentials=True)
def process_data():
    gelenLink = request.form['LINK']
    print(gelenLink)
    transcribedText = speechToText(gelenLink)
    result = {'metin': transcribedText, 'link': gelenLink}
    return jsonify(result)

#@socketio.on('speechToText')
#def handle_message(message):
#    print(message)
#    transcribedText = speechToText(message)
#    result = {'metin': transcribedText, 'link': gelenLink}
#    send(jsonify(result), broadcast=True)

# End of Functions #



# Start of Program #

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=3440, threaded=True)
    #socketio.run(app,host='0.0.0.0',port=3440)
    
# End of Program
