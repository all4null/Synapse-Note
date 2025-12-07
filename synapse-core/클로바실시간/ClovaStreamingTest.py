import grpc
import json

import nest_pb2
import nest_pb2_grpc

import requests
import json
import os
import time
from difflib import SequenceMatcher
import re
import itertools
from dotenv import load_dotenv

load_dotenv()

AUDIO_PATH = "./lsy_audio_2023_58s.pcm"   #인식할 오디오 파일이 위치한 경로를 입력해 주십시오. (16kHz, 1channel, 16 bits per sample의 PCM (헤더가 없는 raw wave) 형식)
CLIENT_SECRET = os.getenv('CLOVA_API_KEY')
#print(CLIENT_SECRET)
def generate_requests(audio_path):
    # 초기 설정 요청: 음성 인식 설정
    yield nest_pb2.NestRequest(
        type=nest_pb2.RequestType.CONFIG,
        config=nest_pb2.NestConfig(
            config=json.dumps({"transcription": {"language": "ko"}})
        )
    )

    # 오디오 파일을 열고 32,000 바이트씩 읽음
    seq_id = 0
    with open(audio_path, "rb") as audio_file:
        while True:
            chunk = audio_file.read(16000)  # 오디오 파일의 청크를 읽음
            if not chunk:
                break  # 데이터가 더 이상 없으면 루프 종료
            yield nest_pb2.NestRequest(
                type=nest_pb2.RequestType.DATA,
                data=nest_pb2.NestData(
                    chunk=chunk,
                    extra_contents=json.dumps({"seqId": seq_id, "epFlag": False})
                )
            )
            seq_id += 1
            time.sleep(0.9)

import sys # 상단에 추가 필요

def main():
    channel = grpc.secure_channel(
        "clovaspeech-gw.ncloud.com:50051",
        grpc.ssl_channel_credentials()
    )
    stub = nest_pb2_grpc.NestServiceStub(channel)
    metadata = (("authorization", f"Bearer {CLIENT_SECRET}"),)

    try:
        print("Streaming started... (말씀하시는 내용이 실시간으로 표시됩니다)")
        responses = stub.recognize(generate_requests(AUDIO_PATH), metadata=metadata)
        
        for response in responses:
            if not response.contents:
                continue
            
            try:
                resp_dict = json.loads(response.contents)
            except json.JSONDecodeError:
                continue 

            if "transcription" in resp_dict:
                transcription = resp_dict["transcription"]
                text = transcription.get("text", "")
                
                if not text:
                    continue

                # epFlag 확인
                is_final = transcription.get("epFlag", False)

                # 시간 계산
                start_ms = transcription.get("startTimestamp", 0)
                seconds = start_ms / 1000
                time_stamp = f"[{int(seconds // 60):02d}:{int(seconds % 60):02d}]"
                
                speaker = transcription.get("speaker", {}).get("label", "1")

                if is_final:
                    # [확정] 문장이 끝났으면 줄바꿈(\n)을 해서 고정시킴
                    # \033[K 는 커서 위치부터 줄 끝까지 지우는 특수코드 (잔상 제거)
                    print(f"\r\033[K{time_stamp} 화자 {speaker} : {text}")
                else:
                    # [진행중] 아직 문장이 안 끝났으면 같은 줄에 덮어쓰기 (end="")
                    # \r 은 커서를 줄 맨 앞으로 돌리는 기능
                    print(f"{time_stamp} 화자 {speaker} : {text} ...", end="")

    except grpc.RpcError as e:
        print(f"\nError: {e.details()}")
    finally:
        channel.close()

if __name__ == "__main__":
    main()