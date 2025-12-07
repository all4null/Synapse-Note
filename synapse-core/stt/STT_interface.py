from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Iterator


# [1] 표준화된 결과 데이터 모델

# 문장 하나에 대한 정보 ex) start:0.00 / end: 6.30 / text: 안녕하세요, 이강의는 GPT API로.. 다루는 강의입니다.(한문장)
@dataclass
class STTSegment:
    start: float # 시작 시간(초 단위)
    end: float # 끝시간(초단위)
    text: str #문장 내용
    speaker: str # 화자
    #speaker_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class STTResult:
    full_text: str #전체 텍스트
    segments: list[STTSegment] #STTSegment들을 원소로 가짐
    duration: float = 0.0 #전체오디오길이
# [2] 추상 인터페이스 (설계도)
class STTProvider(ABC):
    @abstractmethod
    def transcribe_stream(self, audio_stream: Iterator[bytes]) -> Generator[STTResult, None, None]:
        """
        오디오 파일을 쪼개서 입력받아
        표준화된 STTResult를 반환(yield)해야 함.
        """
        pass

    @abstractmethod
    def transcribe_from_file(self, audio_file_path:str):
        """
        오디오 파일경로를 입력받아 표준화된 STTResult를 반환
        """
        pass


