import { useState, useEffect } from "react";
import LMSLogin from "./components/LMS/LMSLogin";
import LMSDashboard from "./components/LMS/LMSDashboard";
import ChatWindow from "./components/ChatWindow";
import InputBar from "./components/InputBar";
import ChatWidget from "./components/ChatWidget";

export default function App() {

  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return !!localStorage.getItem("cbnu_lms_session");
  });

  const [userName, setUserName] = useState(() => localStorage.getItem("cbnu_lms_username") || "");
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

  const deleteChat = (targetId) => {
    const tid = Number(targetId);
    setChatHistory(prev => {
      const remaining = prev.filter(c => Number(c.id) !== tid);
      if (remaining.length === 0) {
        const newChat = { id: Date.now(), title: "새로운 채팅", messages: [] };
        setCurrentChatId(newChat.id);
        return [newChat];
      }
      if (tid === Number(currentChatId)) {
        setCurrentChatId(remaining[0].id);
      }
      return remaining;
    });
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

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let reply = "";
      let sources = [];
      let buffer = "";
      let isDone = false;

      while (!isDone) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // 마지막 불완전한 줄은 다음 청크를 위해 보존

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "token") {
              reply += event.value;
              setChatHistory(prev => prev.map(chat =>
                Number(chat.id) === Number(currentChatId)
                  ? { ...chat, messages: [...tempMessages, { role: "assistant", content: reply, sources: [] }] }
                  : chat
              ));
            } else if (event.type === "sources") {
              sources = event.value;
            } else if (event.type === "done") {
              isDone = true;
              break;
            } else if (event.type === "error") {
              reply = event.value;
              isDone = true;
              break;
            }
          } catch (e) {
            // 불완전한 JSON 라인 무시
          }
        }
      }

      setChatHistory(prev => {
        const updated = prev.map(chat =>
          Number(chat.id) === Number(currentChatId)
            ? { ...chat, messages: [...tempMessages, { role: "assistant", content: reply, sources }] }
            : chat
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

const handleLogout = () => {
    localStorage.removeItem("cbnu_lms_session");
    localStorage.removeItem("cbnu_lms_username");
    setIsLoggedIn(false);
    setUserName("");
    fetch("/api/lms/logout", { method: "POST" });
  };



  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        {/* onLoginSuccess에서 이름을 받아와 저장합니다 */}
        <LMSLogin onLoginSuccess={(name) => {
          localStorage.setItem("cbnu_lms_session", "true");
          if (name) {
            localStorage.setItem("cbnu_lms_username", name);
            setUserName(name);
          }
          setIsLoggedIn(true);
        }} />
      </div>
    );
  }

return (
    <div className="min-h-screen bg-gray-100 relative overflow-hidden flex flex-col">
      {/* 상단 네비게이션 바 (옵션) */}
      <header className="bg-white shadow-sm px-6 py-4 flex justify-between items-center z-10 relative">
        <h1 className="text-xl font-bold text-cbnu-blue flex-1">충북대학교 LMS Portal</h1>

        <div className="absolute left-1/2 transform -translate-x-1/2 font-bold text-lg text-gray-800">
          {userName ? `${userName}님, 안녕하세요!` : ""}
        </div>

        <button 
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-500"
        >
          로그아웃
        </button>
      </header>

      {/* 중앙 메인 영역 (팀원들 요구사항 구현부) */}
      <main className="flex-1 overflow-y-auto p-6">
        <LMSDashboard onLogout={handleLogout} />
      </main>

      {/* 우측 하단 플로팅 챗봇 (기존 채팅 UI) */}
      <ChatWidget
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        startNewChat={startNewChat}
        switchChat={switchChat}
        deleteChat={deleteChat}
        messages={messages}
        handleSend={handleSend}
        isLoading={isLoading}
        useSearch={useSearch}
        onToggleSearch={() => setUseSearch(v => !v)}
      />
    </div>
  );
}