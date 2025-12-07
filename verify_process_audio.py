
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from stt.STT_interface import STTResult

# Add server directory to path to import main
sys.path.append(os.path.join(os.getcwd(), 'synapse-server'))

# Import app from main
from main import app

client = TestClient(app)

def test_process_audio_pipeline():
    # Mock STT result
    mock_stt_result = STTResult(
        full_text="이번 프로젝트의 예산은 500만원입니다. 다음 주까지 기획안을 제출해주세요.",
        segments=[],
        duration=10.0
    )

    # Mock Analysis results
    mock_structure = {
        "action_items": [
            {"task": "기획안 제출", "assignee": "전체", "due_date": "다음 주"}
        ],
        "suggestions": ["예산 증액 검토"]
    }
    mock_summary = "프로젝트 예산 및 일정 논의"

    # Patch the functions in main module
    with patch('main.transcribe_audio_file', return_value=mock_stt_result) as mock_stt, \
         patch('main.analyze_action_items', return_value=mock_structure) as mock_analyze, \
         patch('main.generate_summary', return_value=mock_summary) as mock_summarize, \
         patch('main.save_and_index_analysis') as mock_save:

        # Create a dummy file
        with open("test_audio.mp3", "wb") as f:
            f.write(b"dummy audio content")

        with open("test_audio.mp3", "rb") as f:
            response = client.post(
                "/api/process_audio",
                files={"file": ("test_audio.mp3", f, "audio/mpeg")}
            )

        # Cleanup
        os.remove("test_audio.mp3")

        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())

        if response.status_code == 200:
            data = response.json()
            if data['raw_script'] == mock_stt_result.full_text:
                print("SUCCESS: Pipeline verification passed.")
            else:
                print("FAILURE: raw_script mismatch.")
        else:
            print("FAILURE: API returned error.")
            
if __name__ == "__main__":
    test_process_audio_pipeline()
