import { useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";

export default function App() {
  const [chatHistory, setChatHistory] = useState(() => {
    try {
      const saved = localStorage.getItem("cbnu_chat_history");
      return saved ? JSON.parse(saved) : [{ id: Date.now(), title: "새로운 채팅", messages: [] }];
    } catch (e) {
      return [{ id: Date.now(), title: "새로운 채팅", messages: [] }];
    }
  });


  const [currentChatId, setCurrentChatId] = useState(() => {
    const savedId = localStorage.getItem("cbnu_current_chat_id");

    return savedId ? Number(savedId) : (chatHistory[0]?.id || Date.now());
  });

  const [isLoading, setIsLoading] = useState(false);
  const [useSearch, setUseSearch] = useState(false);


  const currentChat = chatHistory.find(c => Number(c.id) === Number(currentChatId));
  const messages = currentChat ? currentChat.messages : [];


  useEffect(() => {
    localStorage.setItem("cbnu_chat_history", JSON.stringify(chatHistory));
    localStorage.setItem("cbnu_current_chat_id", currentChatId.toString());
  }, [chatHistory, currentChatId]);


  const startNewChat = () => {
    if (currentChat && currentChat.messages.length === 0) return;
    const newId = Date.now();
    const newChat = { id: newId, title: "새로운 채팅", messages: [] };
    setChatHistory(prev => [newChat, ...prev].slice(0, 10));
    setCurrentChatId(newId);
  };

  const switchChat = (targetId) => {
    const tid = Number(targetId);
    if (tid === Number(currentChatId)) return;
    
    setChatHistory(prev => {
      const active = prev.find(c => Number(c.id) === Number(currentChatId));
      let updated = (active && active.messages.length === 0) 
        ? prev.filter(c => Number(c.id) !== Number(currentChatId)) 
        : prev;

      const target = updated.find(c => Number(c.id) === tid);
      const filtered = updated.filter(c => Number(c.id) !== tid);
      return target ? [target, ...filtered] : updated;
    });
    setCurrentChatId(tid);
  };

  async function handleSend(text) {
    if (!text.trim()) return;
    setIsLoading(true);

    const userMsg = { role: "user", content: text };
    const tempMessages = [...messages, userMsg];


    setChatHistory(prev => prev.map(chat => 
      Number(chat.id) === Number(currentChatId) 
        ? { 
            ...chat, 
            messages: tempMessages, 
            title: chat.messages.length === 0 ? text.substring(0, 20) : chat.title 
          } 
        : chat
    ));

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: tempMessages, use_search: useSearch }),
      });

      if (!res.ok) throw new Error("서버 응답 오류");
      const data = await res.json();

      const assistantMsg = { role: "assistant", content: data.reply, sources: data.sources };
      

      setChatHistory(prev => {
        const updated = prev.map(chat => 
          Number(chat.id) === Number(currentChatId) ? { ...chat, messages: [...tempMessages, assistantMsg] } : chat
        );
        const target = updated.find(c => Number(c.id) === Number(currentChatId));
        const filtered = updated.filter(c => Number(c.id) !== Number(currentChatId));

        return target ? [target, ...filtered].slice(0, 10) : updated.slice(0, 10);
      });
    } catch (err) {
      console.error("전송 오류:", err);

    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-6 gap-6">
      <aside className="w-72 h-[85vh] bg-white rounded-2xl shadow-xl flex-shrink-0 flex flex-col overflow-hidden border border-gray-200">
        <div className="p-5 border-b font-bold text-cbnu-blue bg-gray-50 flex justify-between items-center">
          <span>📂 채팅 기록</span>
          <button onClick={startNewChat} className="w-8 h-8 flex items-center justify-center rounded-full bg-blue-50 text-cbnu-blue hover:bg-cbnu-blue hover:text-white transition-all text-xl">＋</button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {chatHistory.map((chat) => (
            <button 
              key={chat.id}
              onClick={() => switchChat(chat.id)}
              className={`w-full text-left p-4 rounded-xl text-sm transition-all border ${
                Number(chat.id) === Number(currentChatId) ? "bg-blue-50 border-blue-200" : "hover:bg-gray-50 border-transparent"
              }`}
            >
              <p className={`font-semibold truncate ${Number(chat.id) === Number(currentChatId) ? "text-cbnu-blue" : "text-gray-700"}`}>📍 {chat.title}</p>
            </button>
          ))}
        </div>
      </aside>

      <div className="w-full max-w-2xl h-[85vh] bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden border border-gray-200">
        <header className="bg-cbnu-blue text-white px-6 py-5 flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center">
            <span className="text-cbnu-blue font-black text-xs">AI</span>
          </div>
          <div className="flex-1">
            <p className="font-bold text-base leading-tight">충북대학교 AI 챗봇</p>
            <p className="text-[10px] text-blue-200">Stable Connection • Gemini 1.5 Flash</p>
          </div>
        </header>
        <ChatWindow messages={messages} isLoading={isLoading} />
        <InputBar onSend={handleSend} isLoading={isLoading} useSearch={useSearch} onToggleSearch={() => setUseSearch(v => !v)} />
      </div>
    </div>
  );
}