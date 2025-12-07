from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import asyncio
import json
from models import Message, ChatResponse, AnalyzeRequest
from data import FOLDER_DATA
from transcribe import transcribe_audio_file
from ai_service import analyze_action_items, analyze_digital_board, chat_with_ai, select_relevant_files, generate_summary
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite default
    "*" # 개발 편의를 위해 전체 허용 (배포 시 수정 필요)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/folders")
async def get_folders():
    """폴더 및 파일 목록 데이터를 반환합니다."""
    # 기본 데이터 복사
    current_data = FOLDER_DATA.copy()
    
    # storage 폴더 스캔하여 '분석 기록' 폴더 동적 생성
    storage_dir = os.path.join(os.path.dirname(__file__), "storage")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
        
    history_files = []
    try:
        # 파일 목록 읽기 (내림차순 정렬)
        files = sorted(os.listdir(storage_dir), reverse=True)
        for idx, filename in enumerate(files):
            if filename.endswith(".json"):
                # 파일명에서 날짜 추출 시도 (텍스트분석_2025_12_07_...,json)
                date_str = "Unknown"
                date_str = "Unknown"
                if filename.startswith("텍스트분석_"):
                    # "텍스트분석_" 제거하고 확장자 제거
                    parts = filename.replace("텍스트분석_", "").replace(".json", "") 
                    # 가독성 좋게 변환 (2025_12_07_19시10분 -> 2025.12.07 19:10)
                    date_str = parts.replace("_", ".", 2).replace("_", " ") 
                elif filename.startswith("음성파일_"):
                    # "음성파일_" 제거
                    parts = filename.replace("음성파일_", "").replace(".json", "")
                    date_str = parts.replace("_", ".", 2).replace("_", " ")

                history_files.append({
                    "id": 1000 + idx, # 임시 ID
                    "title": filename, # 파일명 자체를 타이틀로 (또는 내부 json 읽어서 요약 표시 가능)
                    "date": date_str,
                    "type": "history" # 구분값
                })
    except Exception as e:
        print(f"Storage scan error: {e}")
        
    current_data["분석 기록"] = history_files
    
    return current_data

@app.get("/api/folders/{folder_name}/files")
async def get_folder_files(folder_name: str):
    """특정 폴더의 파일 목록을 반환합니다."""
    # get_folders 로직 재사용하거나 별도 로직 구현
    # 여기서는 get_folders 호출해서 필터링 (간단 구현)
    all_folders = await get_folders()
    files = all_folders.get(folder_name)
    
    if files is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return files

@app.get("/api/history/{filename}")
async def get_history_file(filename: str):
    """저장된 분석 결과 파일을 읽어서 반환합니다."""
    storage_dir = os.path.join(os.path.dirname(__file__), "storage")
    file_path = os.path.join(storage_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def chat_api(message: Message):
    """AI 채팅 응답 API (RAG 적용)"""
    user_msg = message.message
    
    # 1. 컨텍스트 로드
    context = ""
    storage_dir = os.path.join(os.path.dirname(__file__), "storage")
    
    target_files = []
    if message.context_files:
        if "auto" in message.context_files:
             # [Auto Mode] AI가 직접 파일 선택
             # 1. 모든 파일의 요약본 읽기
             file_summaries = []
             if os.path.exists(storage_dir):
                 for fname in os.listdir(storage_dir):
                     if fname.endswith(".json"):
                         try:
                            with open(os.path.join(storage_dir, fname), "r", encoding="utf-8") as f:
                                d = json.load(f)
                                file_summaries.append({
                                    "filename": fname,
                                    "summary": d.get("summary", "요약 없음"),
                                    "date": d.get("date", "날짜 없음") # date 필드는 없을 수도 있음
                                })
                         except: pass
             
             # 2. AI에게 관련 파일 추천받기
             if file_summaries:
                 try:
                    recommended_files = await select_relevant_files(user_msg, file_summaries)
                    # recommended_files는 ["file1.json", "file2.json"] 형태여야 함
                    if isinstance(recommended_files, list):
                        target_files = recommended_files
                 except Exception as e:
                     print(f"Auto selection failed: {e}")
            
        elif "none" in message.context_files:
             target_files = []
        else:
             # 사용자가 선택한 파일들 (리스트)
             for fname in message.context_files:
                 if fname == "latest": continue
                 if os.path.exists(os.path.join(storage_dir, fname)):
                     target_files.append(fname)
    
    is_auto_mode = "auto" in message.context_files
    is_none_mode = "none" in message.context_files

    if not target_files and not is_none_mode and not is_auto_mode and os.path.exists(storage_dir):
        files = sorted(os.listdir(storage_dir), reverse=True)
        if files:
            target_files = [files[0]]

    if target_files:
        context_list = []
        for fname in target_files:
            try:
                with open(os.path.join(storage_dir, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    summary = data.get("summary", "없음")
                    action_items = data.get("action_items", [])
                    suggestions = data.get("suggestions", [])
                    
                    file_context = f"""
                    [파일: {fname}]
                    - 요약: {summary}
                    - Action Items: {json.dumps(action_items, ensure_ascii=False)}
                    - AI 제안: {json.dumps(suggestions, ensure_ascii=False)}
                    """
                    context_list.append(file_context)
            except Exception as e:
                print(f"Context loading error for {fname}: {e}")
        
        context = "\n".join(context_list)

    # 2. AI 답변 생성
    ai_response = await chat_with_ai(user_msg, context)
    
    if not ai_response:
        return {
            "thought": None,
            "answer": "죄송합니다. AI 서비스에 연결할 수 없습니다.",
            "sources": []
        }
    
    return ai_response

@app.post("/api/analyze")
async def analyze_text(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """텍스트를 받아 Action Item 분석 결과를 반환하고 저장합니다."""
    text = request.text
    print(f"DEBUG: Starting Analysis for text (len={len(text)})")
    
    # [Pipeline Stage 1 & 2]: Run concurrently
    # Action Items(JSON)과 Summary(Text)를 동시에 요청
    structure_task = asyncio.create_task(analyze_action_items(text))
    summary_task = asyncio.create_task(generate_summary(text))
    
    structure_data, narrative_summary = await asyncio.gather(structure_task, summary_task)
    
    final_result = {}
    
    if structure_data:
        # 1. Action Items Parsing
        raw_actions = structure_data.get("action_items", [])
        
        action_strings = [
            f"{item['task']} (담당: {item['assignee']}, 기한: {item['due_date']})"
            for item in raw_actions
        ]
        
        # 2. Suggestions
        suggestions = structure_data.get("suggestions", [])

        # 3. Merge Results
        final_result = {
            "summary": narrative_summary if narrative_summary else "요약 생성에 실패했습니다.",
            "keywords": ["AI분석", "Pipeline", "Async"], 
            "action_items": action_strings,
            "suggestions": suggestions,
            "sentiment": "Neutral",
            "raw_json": raw_actions,
            "raw_script": text # [NEW] 원본 스크립트 저장
        }
    else:
        # Fallback
        summary = f"입력하신 텍스트({len(text)}자)에 대한 분석 결과입니다. (AI 호출 실패 -> 더미 데이터)"
        keywords = ["예산", "기획", "일정"] if "예산" in text else ["프로젝트", "디자인", "킥오프"]
        action_items = ["관련 부서와 일정 조율하기", "초안 문서 작성 완료하기"]

        final_result = {
            "summary": summary,
            "keywords": keywords,
            "action_items": action_items,
            "sentiment": "Positive"
        }
    
    # [파일 저장 및 인덱싱 로직]
    # BackgroundTasks를 사용하여 응답 속도 향상
    # [MODIFIED] 파일명을 미리 생성하여 반환 (source_type 반영)
    from datetime import datetime
    now = datetime.now()
    
    prefix = "텍스트분석_"
    if request.source_type == "audio":
        prefix = "음성파일_"
        
    filename = f"{prefix}{now.strftime('%Y_%m_%d_%H시%M분')}.json"
    
    background_tasks.add_task(save_and_index_analysis, final_result, text, filename)

    final_result["saved_filename"] = filename
    return final_result

def save_and_index_analysis(final_result, original_text, filename):
    """분석 결과를 저장하고 RAG를 위해 벡터 DB에 인덱싱합니다. (Background Task)"""
    try:
        # from datetime import datetime -> 상위로 이동됨
        # filename 생성 로직 상위로 이동됨 (인자로 받음)
        
        storage_dir = os.path.join(os.path.dirname(__file__), "storage")
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
        save_path = os.path.join(storage_dir, filename)
        
        # 1. JSON 파일 저장
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=4)
        print(f"DEBUG: Saved analysis to {filename}")

        # 2. RAG Indexing
        try:
            from vector_store import vector_db
            print(f"DEBUG: Indexing document {filename} to VectorDB...")
            vector_db.add_document(
                doc_id=filename,
                text=original_text,
                metadata={"date": datetime.now().strftime('%Y-%m-%d'), "title": filename}
            )
            print("DEBUG: Indexing successful.")
        except Exception as ve:
            print(f"VectorDB Indexing Error: {ve}")

    except Exception as e:
        print(f"Error in background save/index task: {e}")

@app.post("/api/analyze/board")
async def analyze_board(request: AnalyzeRequest):
    """텍스트를 받아 디지털 보드(주제/결정/질문) 데이터를 반환합니다."""
    # 이제 analyze_digital_board는 async 함수이므로 await 필요
    result = await analyze_digital_board(request.text)
    if not result:
        return {"error": "AI analysis failed"}
    return result

@app.post("/api/transcribe")
async def transcribe_api(file: UploadFile = File(...)):
    """오디오 파일을 업로드 받아 STT 변환 결과를 반환합니다."""
    temp_file = f"temp_{file.filename}"
    
    try:
        # 업로드된 파일을 임시 파일로 저장
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # STT 변환 수행
        result = transcribe_audio_file(temp_file)
        
        # 결과 반환 (JSON 직렬화 가능한 형태로 변환 필요할 수 있음)
        return {
            "full_text": result.full_text,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "speaker": seg.speaker
                } for seg in result.segments
            ],
            "duration": result.duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 임시 파일 삭제
        if os.path.exists(temp_file):
            os.remove(temp_file)

@app.post("/api/process_audio")
async def process_audio_api(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    오디오 파일을 업로드 받아 STT -> 텍스트 분석 -> 결과 저장 과정을 일괄 처리합니다.
    """
    temp_file = f"temp_process_{file.filename}"
    
    try:
        # 1. 파일 임시 저장
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. STT 변환
        print(f"DEBUG: Starting STT for {file.filename}")
        stt_result = transcribe_audio_file(temp_file)
        full_text = stt_result.full_text
        print(f"DEBUG: STT Complete. Length: {len(full_text)}")
        
        if not full_text:
             raise HTTPException(status_code=400, detail="STT returned empty text")

        # 3. 텍스트 분석 (Action Items & Summary)
        # analyze_text 로직과 유사하지만 여기서 직접 호출하여 통합
        structure_task = asyncio.create_task(analyze_action_items(full_text))
        summary_task = asyncio.create_task(generate_summary(full_text))
        
        structure_data, narrative_summary = await asyncio.gather(structure_task, summary_task)
        
        final_result = {}
        if structure_data:
            raw_actions = structure_data.get("action_items", [])
            action_strings = [
                f"{item['task']} (담당: {item['assignee']}, 기한: {item['due_date']})"
                for item in raw_actions
            ]
            suggestions = structure_data.get("suggestions", [])
            
            final_result = {
                "summary": narrative_summary if narrative_summary else "요약 생성 실패",
                "keywords": ["음성인식", "자동분석"], 
                "action_items": action_strings,
                "suggestions": suggestions,
                "sentiment": "Neutral",
                "raw_json": raw_actions,
                "raw_script": full_text
            }
        else:
            final_result = {
                "summary": "분석 실패",
                "keywords": [],
                "action_items": [],
                "sentiment": "Neutral",
                "raw_script": full_text
            }
            
        # 4. 결과 저장 및 인덱싱 (백그라운드)
        from datetime import datetime
        now = datetime.now()
        filename = f"음성파일_{now.strftime('%Y_%m_%d_%H시%M분')}.json"
        
        background_tasks.add_task(save_and_index_analysis, final_result, full_text, filename)
        
        final_result["saved_filename"] = filename
        return final_result

    except Exception as e:
        print(f"Process Audio Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
