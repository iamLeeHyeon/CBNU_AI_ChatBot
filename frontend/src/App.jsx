import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";

export default function App() {
  const [chatHistory, setChatHistory] = useState([
    { id: Date.now(), title: "새로운 채팅", messages: [] }
  ]);
  const [currentChatId, setCurrentChatId] = useState(chatHistory[0].id);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [useSearch, setUseSearch] = useState(false);

  const startNewChat = () => {
      const currentChat = chatHistory.find(c => c.id === currentChatId);
    
      if (currentChat && currentChat.messages.length === 0) return;

      const newId = Date.now();
      const newChat = { id: newId, title: "새로운 채팅", messages: [] };
    

      setChatHistory(prev => [newChat, ...prev].slice(0, 10));
      setCurrentChatId(newId);
      setMessages([]);
  };

  
    const switchChat = (targetId) => {
      if (targetId === currentChatId) return;

      setChatHistory(prev => {
      
        let updated = prev.map(chat => 
          chat.id === currentChatId ? { ...chat, messages: messages } : chat
        );

      
        const currentChat = updated.find(c => c.id === currentChatId);
        if (currentChat && currentChat.messages.length === 0) {
          updated = updated.filter(c => c.id !== currentChatId);
        }

      
        const targetChat = updated.find(c => c.id === targetId);
        const filtered = updated.filter(c => c.id !== targetId);
        return [targetChat, ...filtered].slice(0, 10);
      });

    
      const target = chatHistory.find(c => c.id === targetId);
      setMessages(target ? target.messages : []);
      setCurrentChatId(targetId);
  };


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
      const updatedMessages = [
        ...newMessages,
        { role: "assistant", content: data.reply, sources: data.sources },
      ];
      setMessages(updatedMessages);
      setChatHistory(prev => {
      const target = prev.find(chat => chat.id === currentChatId);
      const filtered = prev.filter(chat => chat.id !== currentChatId);
      
      const updatedChat = { 
        ...target, 
        messages: updatedMessages,
        
        title: updatedMessages.length <= 2 ? text.substring(0, 30) : target.title 
      };

        
        return [updatedChat, ...filtered].slice(0, 10);
      });
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
        <div className="p-5 border-b font-bold text-cbnu-blue bg-gray-50 flex justify-between items-center">
          <span>📂 채팅 기록</span>
          <button onClick={startNewChat} className="text-xl hover:text-blue-500 transition-colors">＋</button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {chatHistory.map((chat) => (
            <button 
              key={chat.id}
              onClick={() => switchChat(chat.id)}
              className={`w-full text-left p-4 rounded-xl text-sm transition-all border ${
                chat.id === currentChatId 
                ? "bg-blue-50 border-blue-200" 
                : "hover:bg-gray-50 border-transparent"
              }`}
            >
              <p className={`font-medium truncate ${chat.id === currentChatId ? "text-cbnu-blue" : "text-gray-700"}`}>
                📍 {chat.title}
              </p>
            </button>
          ))}
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
