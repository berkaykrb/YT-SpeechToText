from pytube import YouTube 
import os
import math
import ffmpeg
import openai
import warnings
import string
import random
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

# Generate random key (inactive)
def key_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# Delete temp files
def delete_files_with_prefix(directory, prefix):
    file_list = os.listdir(directory)

    for filename in file_list:
        if filename.startswith(prefix):
            file_path = os.path.join(directory, filename)
            os.remove(file_path)

# Downloading video (pytube)
def download_video(url, output_path, randomKey):
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
def transcribe_audio_openai_new(audio_parts, randomKey):
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
    txt_file = open(randomKey+'_output.txt', 'w', encoding="utf-8")
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
def speechToText(link, randomKey):

    download_video(link, video_output_path, randomKey)
    
    print("1")
    
    if __name__ == '__main__':
        video_path = os.path.join(script_directory, 'tempfiles', randomKey+'video.mp4')
        audio_path = os.path.join(script_directory, 'tempfiles', randomKey+'video.wav')
        convert_video_to_audio(video_path, audio_path)
        
    print("2")
    
    audio_parts = split_audio_file(audio_path)
    
    print("3")

    transcribed_text = transcribe_audio_openai_new(audio_parts, randomKey)
    
    print("4")

    delete_files_with_prefix(video_output_path,randomKey)

    return transcribed_text

@app.route('/')
def homepage():
    return 'YT-SpeechToText-v2.1'

@app.route('/speechToText', methods=['POST'])
@cross_origin(supports_credentials=True)
def process_data():
    gelenLink = request.form['LINK']
    randomKey = request.form['RANDOM_KEY']
    print(gelenLink)
    print(randomKey)
    transcribedText = speechToText(gelenLink, randomKey)
    result = {'metin': transcribedText, 'link': gelenLink, 'randomKey': randomKey}
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
