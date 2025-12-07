from stt.Clova import ClovaSpeechClient, STTResult

provider = ClovaSpeechClient()
audio_file_path2 = "../lsy_audio_2023_58s.mp3"
audio_file_path ="../싼기타_비싼기타.mp3"


stt_result: STTResult = provider.transcribe_from_file(audio_file_path)

print("==== 전체 텍스트 ====")
print(stt_result.full_text)
print("=====================\n")


# ====================================
# 2) 간단한 요약 처리 (예시)
# ====================================
# 여기서는 간단히 첫 100글자만 보여주는 요약
summary_text = stt_result.full_text[:100] + "..." if len(stt_result.full_text) > 100 else stt_result.full_text
print("==== 요약 ====")
print(summary_text)
print("================\n")

print("==== 문장 단위 세그먼트 ====")
for seg in stt_result.segments:
    print(f"[{seg.start:.2f} ~ {seg.end:.2f}] ({seg.speaker}) {seg.text}")
print("==============================")

