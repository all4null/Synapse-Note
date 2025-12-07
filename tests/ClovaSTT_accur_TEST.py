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
        # print(json.dumps(request_body, ensure_ascii=False).encode('UTF-8'))
        files = {
            'media': open(file, 'rb'),
            'params': (None, json.dumps(request_body, ensure_ascii=False).encode('UTF-8'), 'application/json')
        }
        response = requests.post(headers=headers, url=self.invoke_url + '/recognizer/upload', files=files)
        return response

def calculate_similarity(text1, text2):
    """두 텍스트 간의 유사도를 0~100%로 계산합니다."""
    return SequenceMatcher(None, text1, text2).ratio() * 100

def generate_all_ground_truths(flexible_gt):
    """
    (A)/(B) 형태의 유연한 정답지에서 가능한 모든 고정 정답지를 생성합니다.
    예: "오신 것 (같아요)/(같애요)" -> ["오신 것 같아요", "오신 것 같애요"]
    """
    # 1. (A)/(B) 패턴을 찾기 위한 정규식
    pattern = re.compile(r'\((.*?)\)/\((.*?)\)')
    
    parts = []
    last_end = 0
    for match in pattern.finditer(flexible_gt):
        parts.append([flexible_gt[last_end:match.start()]])
        parts.append([match.group(1), match.group(2)])
        last_end = match.end()
    parts.append([flexible_gt[last_end:]])

    # 2. 모든 조합 생성
    all_combinations = [''.join(comb) for comb in itertools.product(*parts)]
    return all_combinations

def get_best_similarity(flexible_gt, recognized_text):
    """
    인식된 텍스트를 가능한 모든 정답지 조합과 비교하여 가장 높은 유사도와 그 때의 정답지를 반환합니다.
    """
    possible_gts = generate_all_ground_truths(flexible_gt)
    best_score = 0
    best_gt = ""

    for gt in possible_gts:
        score = calculate_similarity(gt, recognized_text)
        if score > best_score:
            best_score = score
            best_gt = gt
            
    return best_score, best_gt

def run_dataset_test(audio_root, label_root):
    total_files = 0
    total_similarity = 0
    success_count = 0

    print(f"🚀 테스트 시작: {audio_root} 폴더 탐색 중...\n")

    for root, dirs, files in os.walk(audio_root):
        for file in files:
            if file.lower().endswith('.wav'):
                total_files += 1
                wav_path = os.path.join(root, file)
                
                relative_path = os.path.relpath(wav_path, audio_root)
                label_path = os.path.join(label_root, os.path.splitext(relative_path)[0] + '.txt')

                print(f"[{total_files}] 처리 중: {relative_path}")

                if not os.path.exists(label_path):
                    print(f"⚠️ 경고: 정답 파일을 찾을 수 없음 ({label_path})")
                    continue
                
                with open(label_path, 'r', encoding='utf-8') as f:
                    ground_truth = f.read().strip()

                try:
                    res = ClovaSpeechClient().req_upload(file=wav_path, completion='sync')
                    res_json = res.json()

                    if res.status_code == 200 and res_json.get('result') == 'COMPLETED':
                        recognized_text = res_json['text']
                        
                        # 수정된 부분: 튜플 언패킹
                        similarity_score, best_gt_text = get_best_similarity(ground_truth, recognized_text)
                        total_similarity += similarity_score
                        success_count += 1

                        print(f"   ✅ 원본 정답: {ground_truth}")
                        # print(f"   ✨ 최적 정답: {best_gt_text}") # 필요시 주석 해제
                        print(f"   🗣️ 인식 결과: {recognized_text}")
                        print(f"   📊 유사도: {similarity_score:.2f}%")
                        print("-" * 50)
                    else:
                        print(f"❌ API 오류: {res_json.get('message', '알 수 없는 오류')}")

                except Exception as e:
                    print(f"❌ 시스템 오류 발생: {e}")

                time.sleep(0.5)

    if success_count > 0:
        avg_similarity = total_similarity / success_count
        print(f"\n🎉 테스트 완료!")
        print(f"총 시도: {total_files}개 / 성공: {success_count}개")
        print(f"⭐ 평균 정확도(유사도): {avg_similarity:.2f}%")
    else:
        print("\n⚠️ 테스트된 파일이 없습니다. 경로를 확인해주세요.")

if __name__ == '__main__':
    AUDIO_DIR = './음성파일'
    LABEL_DIR = './정답지'
    run_dataset_test(AUDIO_DIR, LABEL_DIR)