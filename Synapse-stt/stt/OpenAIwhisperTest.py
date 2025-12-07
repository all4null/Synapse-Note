from openai import OpenAI# OpenAI 라이브러리 임포트
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI()
audio_file_path = "./lsy_audio_2023_58s.mp3"

with open(audio_file_path, 'rb') as audio_file:
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

print(transcription)
#transcription