import requests
import json
import os
from dotenv import load_dotenv
from stt.STT_interface import STTProvider, STTSegment, STTResult
from typing import Iterator, Generator

load_dotenv()

class ClovaSpeechClient(STTProvider):
    # Clova Speech invoke URL (앱 등록 시 발급받은 Invoke URL)
    invoke_url = os.getenv('CLOVA_INVOKE_URL')
    # Clova Speech secret key (앱 등록 시 발급받은 Secret Key)
    secret = os.getenv('CLOVA_API_KEY')

    diarization_settings = {
        "enable": True,
        "speakerCountMin": -1,
        "speakerCountMax": -1
    }

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

    # file path만 받아서 사용
    def transcribe_from_file(self, audio_file_path:str):
        res = self.req_upload(file=audio_file_path,completion='sync',diarization=self.diarization_settings)
        res_json = res.json()
        full_text = res_json.get("text","")

        segments = []
        for seg in res_json.get("segments",[]):
            speaker_data = seg.get("speaker", {})
            segments.append(
                STTSegment(
                    start=seg.get("start",0.0)/1000, #ms기준이므로 보기쉽게 초(second)단위로 변환
                    end=seg.get("end",0.0)/1000,
                    text=seg.get("text", ""),
                    speaker = speaker_data,
                    #speaker = speaker_data.get("name", "Unknown")
                )
            )
        result = STTResult(
            segments=segments,
            duration=res_json.get("duration",0.0),
            full_text= full_text
        )
        return result
    
    # 파일을 쪼개 받아온뒤 합쳐서 사용 #현재는 사용하지않음
    def transcribe_stream(self, audio_stream: Iterator[bytes]) -> Generator[STTResult, None, None]:
        audio_bytes = b"".join(chunk for chunk in audio_stream)
        response = self._upload_audio(audio_bytes)
        res_json = response.json()

        if response.status_code != 200:
            raise RuntimeError(f"Clova API 오류: {response.status_code} / {res_json}")

        full_text = res_json.get("text", "")
        segments = []
        for seg in res_json.get("segments", []):
            speaker_data = seg.get("speaker", {})
            segments.append(
                STTSegment(
                    start=seg.get("start", 0.0)/1000,
                    end=seg.get("end", 0.0)/1000,
                    text=seg.get("text", ""),
                    speaker_info = speaker_data,
                    speaker = speaker_data.get("name", "Unknown")
                )
            )

        yield STTResult(
            full_text=full_text,
            segments=segments,
            duration=res_json.get("duration", 0.0)
        )
