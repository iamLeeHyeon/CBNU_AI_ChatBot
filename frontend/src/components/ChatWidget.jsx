import { useState } from "react";
// 파일 경로가 다르면 본인 프로젝트 구조에 맞게 수정하세요.
import ChatWindow from "./ChatWindow";
import InputBar from "./InputBar";

export default function ChatWidget({ 
  chatHistory, 
  currentChatId, 
  startNewChat, 
  switchChat, 
  messages, 
  handleSend, 
  isLoading, 
  useSearch, 
  onToggleSearch 
}) {
  // 챗봇 창을 열고 닫는 토글 상태
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      
      {/* 챗봇 창 본체 (isOpen이 true일 때만 렌더링) */}
      {isOpen && (
        // 가로 길이를 750px로 늘려 2단 레이아웃이 답답하지 않게 조절
        <div className="w-[750px] h-[600px] bg-white rounded-2xl shadow-2xl border border-gray-200 mb-4 flex flex-col overflow-hidden animate-fade-in-up">
          
          {/* 전체 공통 헤더 */}
          <div className="bg-cbnu-blue text-white p-3 flex justify-between items-center z-10 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center text-cbnu-blue font-black text-xs">AI</div>
              <span className="font-bold">충북대학교 AI 조교</span>
            </div>
            <button 
              onClick={() => setIsOpen(false)} 
              className="text-white hover:text-red-300 font-bold text-xl transition-colors"
            >
              ✖
            </button>
          </div>

          {/* 내부 2단 분할 영역 */}
          <div className="flex-1 flex flex-row overflow-hidden bg-gray-50">
            
            {/* 왼쪽: 대화 기록 사이드바 (가로 250px 고정) */}
            <div className="w-[250px] bg-white border-r border-gray-100 flex flex-col flex-shrink-0">
              <div className="p-3 border-b flex justify-between items-center bg-gray-50">
                <span className="font-bold text-sm text-gray-700">📂 이전 대화</span>
                {/* 새 채팅 시작 버튼 복구 */}
                <button 
                  onClick={startNewChat} 
                  className="text-cbnu-blue hover:text-blue-700 font-bold text-lg transition-transform hover:scale-110" 
                  title="새 채팅 시작"
                >
                  ＋
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {chatHistory.map((chat) => (
                  <button 
                    key={chat.id}
                    onClick={() => switchChat(chat.id)}
                    className={`w-full text-left p-3 rounded-xl text-xs transition-all border ${
                      Number(chat.id) === Number(currentChatId)
                      ? "bg-blue-50 border-blue-200 text-cbnu-blue font-bold shadow-sm" 
                      : "hover:bg-gray-50 border-transparent text-gray-600"
                    }`}
                  >
                    <p className="truncate">📍 {chat.title}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* 오른쪽: 실제 채팅창 및 입력 폼 */}
            <div className="flex-1 flex flex-col overflow-hidden relative">
              <div className="flex-1 overflow-y-auto relative bg-gray-50">
                <ChatWindow messages={messages} isLoading={isLoading} />
              </div>
              <div className="bg-white border-t border-gray-100">
                <InputBar 
                  onSend={handleSend} 
                  isLoading={isLoading} 
                  useSearch={useSearch} 
                  onToggleSearch={onToggleSearch} 
                />
              </div>
            </div>

          </div>
        </div>
      )}

      {/* 동그란 플로팅 챗봇 버튼 */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-16 h-16 bg-cbnu-blue rounded-full shadow-2xl flex items-center justify-center text-white text-3xl hover:scale-110 hover:bg-blue-800 transition-all duration-300"
      >
        {isOpen ? "⬇️" : "💬"}
      </button>
    </div>
  );
}