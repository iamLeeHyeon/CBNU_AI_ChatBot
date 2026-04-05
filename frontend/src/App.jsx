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
