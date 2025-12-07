import sys
import os

# synapse-core를 sys.path에 추가하여 모듈을 임포트할 수 있게 함
# synapse-server와 synapse-core가 같은 상위 디렉토리에 있다고 가정
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.abspath(os.path.join(current_dir, "../synapse-core"))
if core_dir not in sys.path:
    sys.path.append(core_dir)

try:
    from stt.Clova import ClovaSpeechClient
except ImportError as e:
    print(f"Error importing synapse-core modules: {e}")
    # 가짜 클라이언트 또는 에러 처리를 위한 fallback을 고려할 수 있음
    raise e

def transcribe_audio_file(file_path: str):
    """
    오디오 파일을 받아서 STT 결과를 반환하는 함수
    """
    client = ClovaSpeechClient()
    # transcribe_from_file은 STTResult 객체를 반환
    result = client.transcribe_from_file(file_path)
    return result
