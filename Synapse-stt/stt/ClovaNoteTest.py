import requests
import json
import os
import time
from difflib import SequenceMatcher
import re
import itertools
from dotenv import load_dotenv

load_dotenv()

class ClovaSpeechClient:
    # Clova Speech invoke URL (앱 등록 시 발급받은 Invoke URL)
    invoke_url = os.getenv('CLOVA_INVOKE_URL')
    # Clova Speech secret key (앱 등록 시 발급받은 Secret Key)
    secret = os.getenv('CLOVA_API_KEY')

    def req_upload(self, file, completion, callback=None, userdata=None, forbiddens=None, boostings=None,
                   wordAlignment=True, fullText=True, diarization=None, sed=None):
        request_body = {
            'language': 'ko-KR',
            'completion': completion,
            'callback': callback,
            'userdata': userdata,
            'wordAlignment': wordAlignment,
            'fullText': fullText,
            'forbiddens': forbiddens,
            'boostings': boostings,
            'diarization': diarization,
            'sed': sed,
        }
        headers = {
            'Accept': 'application/json;UTF-8',
            'X-CLOVASPEECH-API-KEY': self.secret
        }
        # print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8')) #requestbody출력
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url + '/recognizer/upload', files=files)
        return response

diarization_settings = {
    "enable": True,
    "speakerCountMin": -1,
    "speakerCountMax": -1
}

audio_file_path = "../lsy_audio_2023_58s.mp3"
res = ClovaSpeechClient().req_upload(file=audio_file_path, completion='sync', diarization=diarization_settings)
res_json = res.json()

print(res_json)
print("=============================")
print(res_json['text'])