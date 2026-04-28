import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useSearch, setUseSearch] = useState(false);

  async function handleSend(text) {
    const newMessages = [...messages, { role: "user", content: text }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages,
          use_search: useSearch,
        }),
      });

      if (!res.ok) throw new Error("서버 오류가 발생했습니다.");

      const data = await res.json();
      setMessages([
        ...newMessages,
        { role: "assistant", content: data.reply, sources: data.sources },
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        { role: "assistant", content: `오류: ${err.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">

    <aside className="w-72 h-[85vh] bg-white rounded-2xl shadow-lg flex-shrink-0 flex flex-col overflow-hidden border border-gray-100">
        <div className="p-5 border-b font-bold text-cbnu-blue bg-gray-50">
          <span className="flex items-center gap-2">
            📂 채팅 기록
          </span>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {/* 클릭 가능한 아이템들 (나중에 State와 연결) */}
          <button className="w-full text-left p-4 hover:bg-blue-50 rounded-xl text-sm transition-all border border-transparent hover:border-blue-100 group">
            <p className="font-medium text-gray-700 group-hover:text-cbnu-blue">📍 최근 대화 1</p>
            <p className="text-xs text-gray-400 mt-1">2026.04.29</p>
          </button>
          
          <button className="w-full text-left p-4 hover:bg-blue-50 rounded-xl text-sm transition-all border border-transparent hover:border-blue-100 group">
            <p className="font-medium text-gray-700 group-hover:text-cbnu-blue">📍 과거 대화 2</p>
            <p className="text-xs text-gray-400 mt-1">2026.04.28</p>
          </button>
        </div>

        <div className="p-4 bg-gray-50 border-t">
          <p className="text-[10px] text-gray-400 text-center uppercase tracking-widest">Chat History System</p>
        </div>
      </aside>


      <div className="w-full max-w-2xl h-[85vh] bg-white rounded-2xl shadow-lg flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-cbnu-blue text-white px-5 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-white flex items-center justify-center">
            <span className="text-cbnu-blue font-bold text-sm">AI</span>
          </div>
          <div>
            <p className="font-semibold text-sm">충북대학교 AI 챗봇</p>
            <p className="text-xs text-blue-200">Powered by Gemini Flash</p>
          </div>
          <button
            onClick={() => setMessages([])}
            className="ml-auto text-xs text-blue-200 hover:text-white transition-colors"
          >
            대화 초기화
          </button>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} />

        <InputBar
          onSend={handleSend}
          isLoading={isLoading}
          useSearch={useSearch}
          onToggleSearch={() => setUseSearch((v) => !v)}
        />
      </div>
    </div>
  );
}
