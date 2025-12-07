import requests
import time

BASE_URL = "http://localhost:8000"

def test_rag_flow():
    # 1. Analyze (Indexing)
    print("\n[Step 1] Analyzing Meeting Script...")
    script_text = """
    김철수: 이번 프로젝트 알파의 예산은 총 5천만원으로 확정되었습니다.
    이영희: 네, 알겠습니다. 디자인 팀에는 2천만원이 배정된 거죠?
    김철수: 맞습니다. 나머지는 개발과 마케팅에 사용됩니다.
    """
    
    try:
        resp = requests.post(f"{BASE_URL}/api/analyze", json={"text": script_text})
        if resp.status_code == 200:
            print("Analyze Success:", resp.json().get("saved_filename"))
        else:
            print("Analyze Failed:", resp.text)
            return
    except Exception as e:
        print(f"Connection Failed: {e}")
        return

    # Wait for indexing (although synchronous in code, safety buffer)
    time.sleep(2)

    # 2. Chat (Retrieval)
    print("\n[Step 2] Chatting with AI...")
    question = "프로젝트 알파의 총 예산은 얼마야?"
    
    try:
        chat_resp = requests.post(f"{BASE_URL}/api/chat", json={"message": question})
        if chat_resp.status_code == 200:
            answer = chat_resp.json().get("response")
            print("AI Answer:", answer)
            
            if "5천만" in answer or "5,000만" in answer:
                print("✅ RAG Verification PASSED!")
            else:
                print("❌ RAG Verification FAILED (Context missing?)")
        else:
            print("Chat Failed:", chat_resp.text)
    except Exception as e:
        print(f"Chat Connection Failed: {e}")

if __name__ == "__main__":
    test_rag_flow()
