import { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  Folder,
  Settings,
  MessageSquare,
  Upload,
  Search,
  Database,
  Menu,
  X,
  Send,
  Plus,
  FileText,
  ChevronLeft,
  Home,
  History,
  Bot,
  User
} from 'lucide-react';

import './App.css'
import './ChatPage.css';
import MindMap from './MindMap'; // [NEW] MindMap 컴포넌트 추가


// FOLDER_DATA removed - Fetching from API


function App() {

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [folderData, setFolderData] = useState({});

  useEffect(() => {
    fetch('http://localhost:8000/api/folders')
      .then(res => res.json())
      .then(data => setFolderData(data))
      .catch(err => console.error("Failed to fetch folders:", err));
  }, []);

  // ▼▼▼  모바일 주소창 높이 계산 로직 ▼▼▼
  useEffect(() => {
    const setScreenSize = () => {
      let vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    // 1. 처음 켜질 때 실행
    setScreenSize();

    // 2. 화면 크기 바뀔 때마다 실행
    window.addEventListener('resize', setScreenSize);

    // 3. 청소(Clean-up)
    return () => window.removeEventListener('resize', setScreenSize);
  }, []);
  // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

  return (
    <BrowserRouter>
      <div className="app-container">

        {/* --- 회전하는 화살표 버튼 (App 컴포넌트 최상단에 하나만 존재) --- */}
        {/* --- 회전하는 화살표 버튼 (App 컴포넌트 최상단에 하나만 존재) --- */}
        <button
          className={`toggle-btn ${isSidebarOpen ? 'open' : 'closed'}`}
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          title={isSidebarOpen ? "사이드바 닫기" : "사이드바 열기"}
        >
          <ChevronLeft size={26} /> {/* 항상 ChevronLeft 아이콘을 사용하고 CSS로 회전 */}
        </button>

        {/* --- 사이드바 --- */}
        <aside className={`sidebar ${isSidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            Synapse Note
          </div>

          <div className="new-chat-btn">+ 새로운 분석</div>

          <nav style={{ flexGrow: 1, overflowY: 'auto' }}>
            <Link to="/" className="menu-item"><Home size={20} /> 홈</Link>
            <Link to="/chat" className="menu-item"><MessageSquare size={20} /> AI 채팅</Link>
            <Link to="/demo" className="menu-item"><FileText size={20} /> 텍스트 분석 (Demo)</Link>
            <Link to="/upload" className="menu-item"><Upload size={20} /> 업로드</Link>

            <div style={{ marginTop: '20px', paddingLeft: '20px', fontSize: '14px', color: '#888', marginBottom: '10px' }}>
              폴더 목록
            </div>

            {Object.keys(folderData).map((folderName) => (
              <Link key={folderName} to={`/folder/${folderName}`} className="menu-item">
                <Folder size={18} /> {folderName}
              </Link>
            ))}
            <div style={{ borderTop: '1px solid #444', paddingTop: '10px' }}>
              <div className="menu-item"><History size={18} /> 최근 기록</div>
            </div>
          </nav>
        </aside>

        {/* --- 메인 컨텐츠 --- */}
        <main className={`main-content ${isSidebarOpen ? 'shifted' : 'full'}`}>

          {/* header-row에 조건부 클래스 추가! */}
          <header className={`header ${isSidebarOpen ? '' : 'expanded'}`}>

            {/* 제목은 이제 버튼을 피해 도망갑니다 */}
            <CurrentPageTitle />

          </header>

          <div style={{ padding: "20px", height: 'calc(100% - var(--header-height))', overflowY: 'auto' }}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/demo" element={<DemoPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/file/:fileId" element={<div>파일 뷰어 (준비중)</div>} />
              <Route path="/report/:filename" element={<ReportPage />} />
              <Route path="/folder/:folderName" element={<FolderPage folderData={folderData} />} />
            </Routes>
          </div>

        </main>
      </div>
    </BrowserRouter>
  );
}

//header title 제목 
function CurrentPageTitle() {
  const location = useLocation();
  const path = location.pathname;

  let title = "Synapse Note";

  const pageTitles = {
    "/": "홈 (메인 화면)",
    "/upload": "새 회의록 업로드",
    "/chat": "AI 회의록 분석 채팅",
    "/demo": "텍스트 기반 분석 (Demo)",
    "/history": "최근 기록"
  };

  // 위의 PageTitles와 비교해서 주소가 정확히 일치하면 그 제목을 반환
  if (pageTitles[path]) {
    return <h2 className="page-title">{pageTitles[path]}</h2>;
  }

  if (path.startsWith('/folder/')) {
    const folderName = decodeURIComponent(path.split('/')[2]);
    title = `${folderName} 목록`;
  }



  return <h2 className="page-title">{title}</h2>;
}

function HomePage() {
  return (
    <div>
      <p style={{ color: '#666' }}>
        홈입니다
      </p>
    </div>
  );
}


function ChatPage() {
  const [messages, setMessages] = useState([
    { id: 1, text: "안녕하세요! 회의록을 분석해드릴까요?", sender: 'ai' }
  ]);

  const [folderData, setFolderData] = useState({});
  const [selectedFiles, setSelectedFiles] = useState([]); // [NEW] 다중 선택을 위한 배열로 변경
  const chatContainerRef = useRef(null);
  const [inputText, setInputText] = useState("");
  const [isThinking, setIsThinking] = useState(false); // [NEW] 사고 중 상태


  useEffect(() => {
    fetch('http://localhost:8000/api/folders')
      .then(res => res.json())
      .then(data => {
        setFolderData(data);
      })
      .catch(err => console.error(err));
  }, []);

  // "분석 기록" 폴더에 있는 파일들만 추출
  const historyFiles = folderData["분석 기록"] || [];

  // 메세지가 추가도리때마다 스크롤 맨아래로내리는 이벤트
  useEffect(() => {
    if (chatContainerRef.current) {
      const chatContainer = chatContainerRef.current;

      // "스크롤 바의 위치"를 "전체 내용의 높이"로 설정 -> 즉, 맨 아래로!
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }, [messages]);

  //메세지 전송 함수
  const handleSendMessage = async () => {
    if (!inputText.trim()) return // 입력이 빈 경우 전송 X 

    const newUserMsg = { id: Date.now(), text: inputText, sender: 'user' };
    setMessages((prev) => [...prev, newUserMsg]);
    setInputText("") //입력창 비우기

    // [NEW] 로딩(사고) 상태 시작
    setIsThinking(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: inputText,
          context_files: selectedFiles.length > 0 ? selectedFiles : ["latest"] // 선택된 게 없으면 "latest"
        })
      });
      const data = await response.json();

      // [NEW] 응답 구조 변경 대응 (JSON: { thought, answer, sources })
      // 기존 문자열 응답과 호환성 유지
      const answerText = data.answer || data.response || "응답이 없습니다.";
      const thoughtText = data.thought || null;
      const sources = data.sources || [];

      const newAiMsg = {
        id: Date.now() + 1,
        text: answerText,
        thought: thoughtText,
        sources: sources,
        sender: 'ai'
      };
      setMessages((prev) => [...prev, newAiMsg]);
    } catch (error) {
      console.error("Chat Error:", error);
      const errorMsg = {
        id: Date.now() + 1,
        text: "서버 연결에 실패했습니다.",
        sender: 'ai'
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  //엔터키 반응
  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  //화면 송출
  return (
    <div className="chat-container">

      {/* [NEW] 다중 파일 선택 UI (칩 스타일) */}
      <div style={{ padding: '15px 20px', backgroundColor: '#f9f9f9', borderBottom: '1px solid #eee' }}>
        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '10px' }}>참고할 회의록 선택 (다중 선택 가능):</div>
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '5px' }}>
          {/* -1. AI 자동 선택 */}
          <button
            onClick={() => setSelectedFiles(["auto"])}
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              border: `1px solid ${selectedFiles.includes("auto") ? '#8b5cf6' : '#ddd'}`,
              backgroundColor: selectedFiles.includes("auto") ? '#f3e8ff' : 'white',
              color: selectedFiles.includes("auto") ? '#8b5cf6' : '#555',
              cursor: 'pointer',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            🤖 AI 자동 선택
          </button>

          {/* 0. 문맥 없음 (일반 대화) */}
          <button
            onClick={() => setSelectedFiles(["none"])}
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              border: `1px solid ${selectedFiles.includes("none") ? '#3b82f6' : '#ddd'}`,
              backgroundColor: selectedFiles.includes("none") ? '#eff6ff' : 'white',
              color: selectedFiles.includes("none") ? '#3b82f6' : '#555',
              cursor: 'pointer',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            일반 대화 (문맥 없음)
          </button>

          {/* 1. 최신 (기본) 옵션 */}
          <button
            onClick={() => setSelectedFiles([])}
            style={{
              padding: '6px 12px',
              borderRadius: '20px',
              border: `1px solid ${selectedFiles.length === 0 ? '#3b82f6' : '#ddd'}`,
              backgroundColor: selectedFiles.length === 0 ? '#eff6ff' : 'white',
              color: selectedFiles.length === 0 ? '#3b82f6' : '#555',
              cursor: 'pointer',
              fontSize: '13px',
              whiteSpace: 'nowrap'
            }}
          >
            기본 (최신 파일만)
          </button>

          {/* 2. 개별 파일 리스트 */}
          {historyFiles.map(file => {
            const isSelected = selectedFiles.includes(file.title);
            return (
              <button
                key={file.id}
                onClick={() => {
                  if (isSelected) {
                    setSelectedFiles(selectedFiles.filter(f => f !== file.title));
                  } else {
                    // "none" 또는 "auto"가 선택되어 있었다면 제거하고 선택
                    const newSelection = selectedFiles.filter(f => f !== "none" && f !== "auto");
                    setSelectedFiles([...newSelection, file.title]);
                  }
                }}
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  border: `1px solid ${isSelected ? '#3b82f6' : '#ddd'}`,
                  backgroundColor: isSelected ? '#eff6ff' : 'white',
                  color: isSelected ? '#3b82f6' : '#555',
                  cursor: 'pointer',
                  fontSize: '13px',
                  whiteSpace: 'nowrap'
                }}
              >
                {file.title} {isSelected && '✓'}
              </button>
            )
          })}
        </div>
      </div>

      {/* --- 메시지 목록 영역 --- */}
      <div className="message-list" ref={chatContainerRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row${msg.sender ? ` ${msg.sender}` : ''}`}>

            {/* 프로필 아이콘 (AI면 로봇, 나면 사람) */}
            <div className={`avatar ${msg.sender}`}>
              {msg.sender === 'ai' ? <Bot size={20} /> : <User size={20} />}
            </div>

            <div className="message-content-wrapper">
              {/* [NEW] 사고 과정 (Chain of Thought) */}
              {msg.thought && (
                <div className="thought-bubble">
                  <div className="thought-label">🤔 사고 과정</div>
                  {msg.thought}
                </div>
              )}

              {/* 말풍선 */}
              <div className="bubble">
                {msg.text}
              </div>

              {/* [NEW] 출처 (Citations) */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="citation-container">
                  {msg.sources.map((src, idx) => (
                    <span key={idx} className="citation-tag">
                      🔍 {src.replace('.json', '')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {/* [NEW] 사고 중 로딩 표시 */}
        {isThinking && (
          <div className="message-row ai">
            <div className="avatar ai"><Bot size={20} /></div>
            <div className="bubble thinking-bubble-anim">
              <span>.</span><span>.</span><span>.</span>
              <span style={{ marginLeft: '8px', fontSize: '13px' }}>문서를 검색하고 생각 중입니다...</span>
            </div>
          </div>
        )}
      </div>

      {/* --- 하단 입력창 영역 --- */}
      <div className="input-area">
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="메시지를 입력하세요..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button className="send-btn" onClick={handleSendMessage} disabled={!inputText.trim()}>
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}


function FolderPage({ folderData }) {
  const { folderName } = useParams();
  const navigate = useNavigate();
  const files = folderData[folderName] || [];

  const handleItemClick = (file) => {
    if (file.type === 'history') {
      navigate(`/report/${file.title}`);
    } else {
      // 일반 폴더 아이템 클릭 시 동작 (아직 없음)
      console.log("Clicked file:", file);
    }
  };

  return (
    <div style={{ marginTop: '10px' }}>
      {files.length === 0 && <div style={{ padding: '20px', color: '#999' }}>파일이 없습니다.</div>}
      {files.map(file => (
        <div
          key={file.id}
          onClick={() => handleItemClick(file)}
          style={{
            padding: '15px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            justifyContent: 'space-between',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {file.type === 'history' ? <FileText size={18} color="#666" /> : <FileText size={18} color="#ccc" />}
            <strong>{file.title}</strong>
          </div>
          <span style={{ color: '#999' }}>{file.date}</span>
        </div>
      ))}
    </div>
  );
}

// 스피너 컴포넌트
function LoadingSpinner({ text }) {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
      <div className="loading-text">{text || "처리 중..."}</div>
    </div>
  );
}

// Action Item 카드 컴포넌트
function ActionItemCard({ item }) {
  const priority = item.priority || "Low";
  const priorityLower = priority.toLowerCase();

  // 아이콘 매핑
  let icon = "☕";
  if (priority === 'Critical') icon = "🚨";
  else if (priority === 'High') icon = "🔥";
  else if (priority === 'Medium') icon = "✅";

  return (
    <div className="action-card">
      <div className="card-header">
        <div className="card-title">
          <span style={{ marginRight: '6px' }}>{icon}</span>
          {item.task}
        </div>
        <div className={`priority - badge priority - ${priorityLower} `}>
          {priority}
        </div>
      </div>

      <div className="card-details">
        <div className="detail-item">
          <span className="detail-label">담당자</span>
          <strong>{item.assignee}</strong>
        </div>
        <div className="detail-item">
          <span className="detail-label">마감 기한</span>
          <strong>{item.due_date}</strong>
        </div>
      </div>

      <div className="card-reasoning">
        <span className="reasoning-label">💡 선정 근거</span>
        {item.reasoning}
      </div>
    </div>
  );
}

function DemoPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setResult(null); // 이전 결과 초기화
    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
      alert("분석에 실패했습니다.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '10px' }}>텍스트 기반 분석 (Demo)</h3>
        <p style={{ marginBottom: '15px', color: '#666', fontSize: '14px' }}>
          회의 내용을 텍스트로 붙여넣으면 AI가 Action Item을 추출해줍니다.
        </p>
        <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>회의록 내용 입력</label>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="분석할 회의록 텍스트를 입력해주세요..."
          style={{
            width: '100%',
            height: '200px',
            padding: '10px',
            borderRadius: '8px',
            border: '1px solid #ccc',
            resize: 'vertical'
          }}
        />
      </div>

      <div style={{ textAlign: 'right' }}>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            padding: '10px 25px',
            backgroundColor: loading ? '#ccc' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '16px'
          }}
        >
          {loading ? "분석 요청 중..." : "분석 시작"}
        </button>
      </div>

      {loading && <LoadingSpinner text="AI가 회의록을 분석하고 있습니다. 잠시만 기다려주세요..." />}

      {result && (
        <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
          <h3 style={{ marginBottom: '15px' }}>분석 결과</h3>

          <div style={{ backgroundColor: '#f9f9f9', padding: '20px', borderRadius: '10px', marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>요약</h4>
            <p style={{ margin: 0, lineHeight: '1.5' }}>{result.summary}</p>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
            {result.keywords.map((kw, i) => (
              <span key={i} style={{ backgroundColor: '#e0f2fe', color: '#0369a1', padding: '5px 10px', borderRadius: '15px', fontSize: '14px' }}>
                #{kw}
              </span>
            ))}
          </div>

          <div>
            <h4 style={{ marginBottom: '10px' }}>액션 아이템</h4>
            {result.raw_json ? (
              <div className="action-grid">
                {result.raw_json.map((item, idx) => (
                  <ActionItemCard key={idx} item={item} />
                ))}
              </div>
            ) : (
              <ul style={{ paddingLeft: '20px' }}>
                {result.action_items.map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '5px' }}>{item}</li>
                ))}
              </ul>
            )}
          </div>

          {/* [NEW] AI 제안/조언 섹션 */}
          {result.suggestions && result.suggestions.length > 0 && (
            <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
              <h4 style={{ marginBottom: '10px' }}>💡 AI 제안 & 조언</h4>
              <ul style={{ paddingLeft: '20px', color: '#555' }}>
                {result.suggestions.map((suggestion, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Raw JSON Debug View */}
          {result.raw_json && (
            <details style={{ marginTop: '20px', color: '#888' }}>
              <summary style={{ cursor: 'pointer' }}>원본 JSON 데이터 보기</summary>
              <pre style={{ background: '#eee', padding: '10px', borderRadius: '5px', overflowX: 'auto' }}>
                {JSON.stringify(result.raw_json, null, 2)}
              </pre>
            </details>
          )}

          {/* [NEW] Original Script View - Demo Page */}
          {result.raw_script && (
            <details style={{ marginTop: '10px', color: '#888' }}>
              <summary style={{ cursor: 'pointer' }}>원본 회의록 스크립트 보기</summary>
              <div style={{
                background: '#fcfcfc',
                padding: '15px',
                borderRadius: '5px',
                border: '1px solid #eee',
                marginTop: '10px',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.6',
                color: '#333',
                maxHeight: '300px',
                overflowY: 'auto'
              }}>
                {result.raw_script}
              </div>
            </details>
          )}




        </div>
      )}
    </div>
  );
}


// Report Page (저장된 분석 결과 보기) - DemoPage 디자인 재사용
function ReportPage() {
  const { filename } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'

  useEffect(() => {
    fetch(`http://localhost:8000/api/history/${filename}`)
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, [filename]);

  if (loading) return <LoadingSpinner text="기록을 불러오는 중..." />;
  if (!data) return <div style={{ padding: 20 }}>데이터를 찾을 수 없습니다.</div>;

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h3 style={{ marginBottom: '10px' }}>📄 분석 기록 리포트</h3>
      <div style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
        파일: {filename}
      </div>

      {/* 탭 버튼 (리스트 보기 vs 마인드맵 보기) */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setViewMode('list')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: 'none',
            backgroundColor: viewMode === 'list' ? '#3b82f6' : '#e5e7eb',
            color: viewMode === 'list' ? 'white' : '#374151',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          📋 리스트 보기
        </button>
        <button
          onClick={() => setViewMode('map')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: 'none',
            backgroundColor: viewMode === 'map' ? '#3b82f6' : '#e5e7eb',
            color: viewMode === 'map' ? 'white' : '#374151',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          🧠 마인드맵 보기
        </button>
      </div>

      {viewMode === 'list' ? (
        <>
          {/* 요약 섹션 */}
          <div style={{ backgroundColor: '#f9f9f9', padding: '20px', borderRadius: '10px', marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>요약</h4>
            <p style={{ margin: 0, lineHeight: '1.5' }}>{data.summary}</p>
          </div>

          {/* 키워드 */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
            {data.keywords && data.keywords.map((kw, i) => (
              <span key={i} style={{ backgroundColor: '#e0f2fe', color: '#0369a1', padding: '5px 10px', borderRadius: '15px', fontSize: '14px' }}>
                #{kw}
              </span>
            ))}
          </div>

          {/* 액션 아이템 */}
          <div>
            <h4 style={{ marginBottom: '10px' }}>액션 아이템</h4>
            {data.raw_json ? (
              <div className="action-grid">
                {data.raw_json.map((item, idx) => (
                  <ActionItemCard key={idx} item={item} />
                ))}
              </div>
            ) : (
              <ul style={{ paddingLeft: '20px' }}>
                {data.action_items && data.action_items.map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '5px' }}>{item}</li>
                ))}
              </ul>
            )}
          </div>

          {/* [NEW] AI 제안/조언 섹션 */}
          {data.suggestions && data.suggestions.length > 0 && (
            <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
              <h4 style={{ marginBottom: '10px' }}>💡 AI 제안 & 조언</h4>
              <ul style={{ paddingLeft: '20px', color: '#555' }}>
                {data.suggestions.map((suggestion, idx) => (
                  <li key={idx} style={{ marginBottom: '8px' }}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Raw JSON Debug View */}
          {data.raw_json && (
            <details style={{ marginTop: '20px', color: '#888' }}>
              <summary style={{ cursor: 'pointer' }}>원본 JSON 데이터 보기</summary>
              <pre style={{ background: '#eee', padding: '10px', borderRadius: '5px', overflowX: 'auto' }}>
                {JSON.stringify(data.raw_json, null, 2)}
              </pre>
            </details>
          )}

          {/* [NEW] Original Script View */}
          {data.raw_script && (
            <details style={{ marginTop: '10px', color: '#888' }}>
              <summary style={{ cursor: 'pointer' }}>원본 회의록 스크립트 보기</summary>
              <div style={{
                background: '#fcfcfc',
                padding: '15px',
                borderRadius: '5px',
                border: '1px solid #eee',
                marginTop: '10px',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.6',
                color: '#333',
                maxHeight: '300px',
                overflowY: 'auto'
              }}>
                {data.raw_script}
              </div>
            </details>
          )}

        </>
      ) : (
        /* 마인드맵 뷰 */
        <div>
          <MindMap markdown={generateMindMapMarkdown(data, filename)} />
        </div>
      )}
    </div>
  );
}

// 마인드맵용 마크다운 생성 함수
function generateMindMapMarkdown(data, filename) {
  let md = `# ${filename.replace('.json', '')}\n`;

  // 1. 개요
  md += `## 개요\n- ${data.summary || "요약 없음"}\n`;

  // 2. 주요 논의 내용 (키워드 활용)
  if (data.keywords && data.keywords.length > 0) {
    md += `## 주요 논의 내용\n`;
    data.keywords.forEach(kw => {
      md += `- ${kw}\n`;
    });
  }

  // 3. 실행 항목 (Action Items)
  if (data.raw_json && data.raw_json.length > 0) {
    md += `## 실행 항목\n`;
    data.raw_json.forEach(item => {
      md += `- **${item.task}**\n`;
      md += `  - 담당: ${item.assignee}\n`;
      md += `  - 기한: ${item.due_date}\n`;
      // md += `  - 상태: ${item.priority}\n`;
    });
  } else if (data.action_items && data.action_items.length > 0) {
    md += `## 실행 항목\n`;
    data.action_items.forEach(item => {
      md += `- ${item}\n`;
    });
  }

  // 4. [NEW] AI 제안/조언
  if (data.suggestions && data.suggestions.length > 0) {
    md += `## AI 조언\n`;
    data.suggestions.forEach(suggestion => {
      md += `- ${suggestion}\n`;
    });
  }

  return md;
}

function UploadPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false); // 로딩 상태
  const navigate = useNavigate(); // 페이지 이동 훅
  const [processingStatus, setProcessingStatus] = useState(""); // 현재 진행 상태 메시지

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return alert("파일을 선택해주세요!");

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsProcessing(true); // 로딩 시작
    setProcessingStatus("음성 인식 중... (텍스트 변환)");

    try {
      // 1단계: 음성 인식 (STT) - /api/transcribe
      const transRes = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData
      });

      if (!transRes.ok) {
        const err = await transRes.json();
        throw new Error(err.detail || "STT failed");
      }

      const transData = await transRes.json();
      const fullText = transData.full_text;

      if (!fullText) throw new Error("Audio is empty or STT failed");

      // 2단계: 내용 분석 - /api/analyze
      setProcessingStatus("내용 분석 중... (주요 안건 및 요약 추출)");

      const analyzeRes = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: fullText,
          source_type: "audio"
        })
      });

      if (!analyzeRes.ok) {
        const err = await analyzeRes.json();
        throw new Error(err.detail || "Analysis failed");
      }

      const analyzeData = await analyzeRes.json();
      console.log("Analysis result:", analyzeData);

      // 결과 페이지로 이동 (saved_filename 활용)
      if (analyzeData.saved_filename) {
        navigate(`/report/${analyzeData.saved_filename}`);
      } else {
        alert("분석은 완료되었으나 파일명을 찾을 수 없습니다.");
        setIsProcessing(false);
      }

    } catch (e) {
      console.error(e);
      alert("분석 실패: " + e.message);
      setIsProcessing(false);
    }
    // 성공 시에는 navigate 하므로 finally에서 false로 돌리지 않음 (화면 유지)
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '50px' }}>
      <h2 style={{ marginBottom: '20px' }}>새 회의록 업로드</h2>

      {/* 로딩 중일 때 시각적 효과 표시 */}
      {isProcessing ? (
        <div className="processing-container">
          <div className="sonic-wave"></div>
          <div className="processing-text">
            AI가 회의록을 분석하고 있습니다...
          </div>
          <p style={{ color: '#888', marginTop: '10px', fontSize: '14px' }}>
            {processingStatus}
          </p>
        </div>
      ) : (
        <>
          {/* 업로드 박스 디자인 */}
          <div style={{
            border: '2px dashed #ccc',
            borderRadius: '10px',
            padding: '40px',
            textAlign: 'center',
            backgroundColor: '#fafafa',
            cursor: 'pointer'
          }}>
            <Upload size={48} color="#ccc" style={{ marginBottom: '10px' }} />
            <p style={{ color: '#666', marginBottom: '20px' }}>
              여기로 파일을 끌어다 놓거나 클릭하세요
            </p>

            {/* 실제 파일 입력창 */}
            <input
              type="file"
              id="fileInput"
              accept="audio/*,video/*"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <label
              htmlFor="fileInput"
              style={{
                padding: '10px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '5px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              파일 선택하기
            </label>
          </div>

          {/* 선택된 파일이 있으면 보여주기 */}
          {selectedFile && (
            <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #eee', borderRadius: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>📄 {selectedFile.name}</span>
              <button
                onClick={handleUpload}
                style={{
                  padding: '8px 15px',
                  backgroundColor: '#10a37f',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                분석 시작
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;