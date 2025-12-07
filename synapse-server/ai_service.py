import os
import json
import asyncio
import re
from openai import AsyncOpenAI, RateLimitError, APIError
from dotenv import load_dotenv

load_dotenv()

async def call_openai_api(full_prompt, system_instruction, retries=3, delay=1):
    """
    OpenAI API를 호출하고 텍스트 응답을 반환합니다. (Async)
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        return None

    try:
        client = AsyncOpenAI(api_key=api_key)
    except Exception as e:
        print(f"OpenAI Client Initialization Error: {e}")
        return None
    
    # OpenAI API에 맞는 메시지 형식
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": full_prompt}
    ]

    for i in range(retries):
        try:
            # OpenAI API 호출
            response = await client.chat.completions.create(
                model="gpt-4o-mini", # Default to a known model
                messages=messages,
                timeout=60
            )
            
            # 응답 파싱
            text = response.choices[0].message.content

            if text:
                return text.strip()
            else:
                raise ValueError("Invalid API response structure.")

        except (RateLimitError, APIError) as e: # OpenAI 관련 오류 처리
            print(f"API Call Failed (Attempt {i+1}/{retries}): {e}")
            if i == retries - 1:
                return None
            await asyncio.sleep(delay * (2 ** i))  # Exponential backoff
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return None

    return None

def clean_json_response(text):
    """
    AI 응답 텍스트에서 마크다운 코드 블록을 제거하고 JSON을 파싱합니다.
    """
    if not text:
        return None

    # ```json ... ``` 블록 찾기
    match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        # 코드 블록이 없으면, 중괄호로 시작하는 부분을 찾아봄
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = text.strip()
            
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        print("JSON Parsing Failed")
        return None

SYSTEM_INSTRUCTION_ACTION_ITEMS = """
당신은 전문 회의록 분석가입니다.
제공된 [회의 녹취록]을 분석하여 'Action Item'을 추출해 주세요.
사용자가 제공하는 회의록은 비선형적이며, 모호한 지시어와 말 번복이 포함되어 있습니다.
결과는 **시스템 연동을 위한 JSON 포맷**으로 출력해야 합니다.

**[분석 단계 - Chain of Thought]**
답변을 출력하기 전에 반드시 다음 단계로 사고하세요:
1. **문맥 파악:** '그거', '저거', '아까 말한 이슈'가 구체적으로 무엇을 지칭하는지 대화의 앞부분을 참조하여 연결합니다.
2. **최신성 검증:** 동일한 주제에 대해 지시가 있었다가 나중에 "취소해", "나중에 해"라고 변경되었다면, **최종 발언**을 기준으로 판단합니다.
3. **담당자 확정:** 업무가 A에서 B로 이관되었는지 확인하여 최종 수행자를 지정합니다.
4. **행동 추출:** 단순한 의견 교환이나 아이디어 제시가 아니라, 실제 '수행하기로 합의된' 과업만 추출합니다.

**[필수 제약 조건] - 이 규칙을 어기면 안 됩니다:**
1. **명사형 종결(개조식):** 문장은 반드시 명사로 끝나야 합니다. (예: "수정해주세요" (X) -> "수정"(O), "보내주세요" (X) -> "송부" (O))
2. **Task 명명 규칙:** '완료', '됨', '했음', '끝' 등 상태를 나타내는 단어 사용 금지. '작성', '수정', '배포' 등 행위 명사 사용.
3. **간결성:** 불필요한 조사나 서술어를 제거하고 핵심만 남기세요.
4. **날짜 변환:** 상대적 시간 표현을 **파일이 생성된 시간(오늘)** 기준으로 계산하여 구체적인 날짜(YYYY-MM-DD)로 변환하세요.
5. **최우선 순위 추론:** 대화 전체에서 **가장 치명적인 이슈**를 찾아 연결하십시오.

**[JSON Structure]**
{
    "action_items": [
        {
            "task": "행위 명사형 (반드시 태그 포함: Drop, R&R 확인)",
            "assignee": "담당자 이름",
            "due_date": "YYYY-MM-DD",
            "priority": "Critical | High | Medium | Low",
            "reasoning": "구체적 상황과 지시 배경을 포함한 상세 근거"
        }
    ],
    "suggestions": [
        "회의 내용에 기반한 실행 조언 1",
        "리스크 관리 제안 2"
    ]
}
"""

SYSTEM_INSTRUCTION_BOARD = """
당신은 전문 회의록 요약가입니다. 주어진 스크립트를 분석하여
'주요 주제(Key Topics)', '결정 사항(Decisions Made)', '질문 사항(Open Questions)'
세 가지 카테고리로 분류하세요.
응답은 반드시 아래와 같은 JSON 형식이어야 합니다. 다른 설명은 덧붙이지 마세요.

{
  "주요 주제": ["주제 1", "주제 2", ...],
  "결정 사항": ["결정 1 (담당: OOO)", "결정 2", ...],
  "질문 사항": ["질문 1", "질문 2", ...]
}
"""

async def analyze_action_items(text: str):
    full_prompt = f"다음 회의 스크립트를 분석해주세요:\n\n---\n{text}\n---"
    response_text = await call_openai_api(full_prompt, SYSTEM_INSTRUCTION_ACTION_ITEMS)
    return clean_json_response(response_text)

async def analyze_digital_board(text: str):
    full_prompt = f"다음 회의 스크립트를 분석하여 JSON으로 요약해주세요:\n\n---\n{text}\n---"
    response_text = await call_openai_api(full_prompt, SYSTEM_INSTRUCTION_BOARD)
    return clean_json_response(response_text)

SYSTEM_INSTRUCTION_SUMMARY = """
당신은 전문 회의록 요약 작가입니다.
제공된 회의 스크립트를 읽고, 회의의 흐름과 맥락이 잘 드러나도록 '서술형'으로 요약해주세요.

**작성 가이드라인 (Separation of Concerns):**
1. **JSON 형식이 아닌, 자연스러운 줄글(Text)로 작성하세요.**
2. **구성:**
   - **배경:** 회의가 소집된 이유나 현재 상황
   - **주요 논의:** 어떤 안건들이 오고 갔는지, 의견 대립이나 토론 내용
   - **결론:** 최종적으로 어떻게 결정되었는지
3. 단순 나열식이 아니라, "A가 제안했으나 B의 반대로 결국 C로 결정됨"과 같이 인과관계와 흐름을 담아주세요.
4. 분량: 5문장 이상, 10초 내외로 읽을 수 있는 분량.
"""

async def generate_summary(text: str):
    full_prompt = f"다음 회의 내용을 바탕으로 고품질의 서술형 요약을 작성해주세요:\n\n---\n{text}\n---"
    return await call_openai_api(full_prompt, SYSTEM_INSTRUCTION_SUMMARY)

SYSTEM_INSTRUCTION_CHAT = """
당신은 회의록 데이터를 기반으로 답변하는 AI 비서 'Synapse Bot'입니다.
사용자의 질문에 대해 아래 제공된 [회의록 문맥(Context)]을 바탕으로 친절하고 명확하게 답변하세요.

**[응답 형식 - 중요]**
반드시 아래 JSON 형식으로만 응답해야 합니다. 마크다운 코드 블록(```json)이나 다른 설명은 절대 추가하지 마세요.

{{
    "thought": "사용자의 질문을 분석하고, 제공된 문맥에서 어떤 부분을 참고했는지, 답변을 어떻게 구성할지 단계별 사고 과정을 상세히 한국어로 기술하세요.",
    "answer": "사용자에게 전달할 최종 답변을 한국어로 자연스럽게 작성하세요.",
    "sources": ["파일1.json", "파일2.txt"] 
}}

[참고] 'sources' 키에는 당신이 답변을 구성하는 데 실제로 참고한 파일명을 리스트에 담아주세요. 문맥에 제공된 파일명만 사용해야 합니다.

[회의록 문맥(Context)]
{context}

**답변 가이드라인:**
1. 문맥에 없는 내용이라면 "제공된 회의록에는 해당 내용이 없습니다."라고 솔직하게 말하세요.
2. 답변은 한국어로 자연스럽게 작성하세요.
3. 질문과 관련 없는 파일은 sources에 포함하지 마세요.
"""

from vector_store import vector_db

async def chat_with_ai(user_message: str, context: str = ""):
    """
    회의록 컨텍스트를 포함하여 사용자와 대화합니다.
    """
    # 1. RAG Retrieval
    try:
        # vector_db.query returns list of dicts: {'content': '...', 'metadata': {...}}
        retrieved_items = vector_db.query(user_message, n_results=3)
        
        rag_context = ""
        known_sources = set()

        if retrieved_items:
            print(f"DEBUG: RAG Retrieved {len(retrieved_items)} items.")
            rag_context_parts = []
            
            for i, item in enumerate(retrieved_items):
                content = item.get('content', '')
                metadata = item.get('metadata', {})
                source_file = metadata.get('doc_id', 'Unknown Source') # metadata keys might vary, assuming doc_id or filename
                
                # Check for other potential keys if doc_id misses
                if 'filename' in metadata:
                    source_file = metadata['filename']
                
                known_sources.add(source_file)
                
                snippet = f"--- Source: {source_file} ---\n{content}\n----------------"
                rag_context_parts.append(snippet)
                
                print(f"--- Chunk {i+1} ({source_file}) ---")
                print(content[:200] + "..." if len(content) > 200 else content)

            rag_context = "\n[관련 회의 내용 (RAG 검색됨)]\n" + "\n".join(rag_context_parts)
            context = f"{context}\n{rag_context}" if context else rag_context

    except Exception as e:
        print(f"RAG Error: {e}")
        # Proceed even if RAG fails

    system_prompt = SYSTEM_INSTRUCTION_CHAT.format(context=context if context else "컨텍스트 없음")
    response_text = await call_openai_api(user_message, system_prompt)
    
    # Parse JSON response
    parsed_response = clean_json_response(response_text)
    
    if parsed_response:
        # Validate/clean sources to ensure they are from the retrieval list
        # AI might hallucinate sources, so we can filter or just trust if prompt is good.
        # Let's trust for now but ensure it's a list.
        if not isinstance(parsed_response.get("sources"), list):
            parsed_response["sources"] = list(known_sources)
        return parsed_response
    else:
        # Fallback if JSON parsing fails
        return {
            "thought": "응답을 생성하는 중...",
            "answer": response_text if response_text else "죄송합니다. 오류가 발생했습니다.",
            "sources": []
        }

SYSTEM_INSTRUCTION_SELECTOR = """
당신은 사용자의 질문에 답변하기 위해 가장 관련성 높은 회의록 파일을 선택하는 도우미입니다.
아래 제공된 [파일 목록]을 분석하여, 사용자의 질문에 답변하는 데 도움이 될만한 파일의 '파일명'을 JSON 배열로 반환하세요.

[파일 목록]
{file_list}

**규칙:**
1. 질문과 밀접하게 관련된 파일만 선택하세요.
2. 관련 파일이 없다면 빈 배열(`[]`)을 반환하세요.
3. 최대 3개까지만 선택하세요.
4. 오직 JSON 배열만 반환하세요. (예: ["meeting_A.json", "meeting_B.json"])
"""

async def select_relevant_files(user_query: str, file_summaries: list):
    """
    사용자 질문과 파일 요약 목록을 받아 관련 파일명을 리스트로 반환
    """
    file_list_str = "\\n".join([f"- {item['filename']}: {item['summary']}" for item in file_summaries])
    prompt = f"사용자 질문: {user_query}"
    
    system_prompt = SYSTEM_INSTRUCTION_SELECTOR.format(file_list=file_list_str)
    response_text = await call_openai_api(prompt, system_prompt)
    
    return clean_json_response(response_text)
