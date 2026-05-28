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

    // 💡 [변경 1] 사용자 메시지와 함께 챗봇의 "빈 말풍선"을 미리 하나 만들어 둡니다.
    const emptyBotMsg = { role: "assistant", content: "", sources: [] };

    setChatHistory(prev => prev.map(chat => 
      Number(chat.id) === Number(currentChatId) 
        ? { 
            ...chat, 
            messages: [...tempMessages, emptyBotMsg], // 빈 말풍선 렌더링
            title: chat.messages.length === 0 ? text.substring(0, 20) : chat.title 
          } 
        : chat
    ));

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: tempMessages, use_search: useSearch }),
        // LMS 세션을 백엔드로 보내려면 credentials가 필요할 수 있습니다 (옵션)
        // credentials: "include" 
      });

      if (!res.ok) throw new Error("서버 응답 오류");

      // 💡 [변경 2] JSON을 한 번에 받지 않고 스트림 리더기를 켭니다.
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let botReply = "";
      let isFirstToken = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break; // 스트리밍 완전 종료

        // 청크(조각) 디코딩
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "");
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);

              // 🟢 토큰(글자) 수신 시: 실시간으로 글자 이어붙이기
              if (data.type === "token") {
                if (isFirstToken) {
                  setIsLoading(false); // 첫 글자가 도착하면 로딩 스피너를 끕니다!
                  isFirstToken = false;
                }
                botReply += data.value;

                // 현재 채팅방의 마지막 메시지(빈 말풍선)를 찾아서 텍스트를 업데이트
                setChatHistory(prev => prev.map(chat => {
                  if (Number(chat.id) === Number(currentChatId)) {
                    const updatedMsgs = [...chat.messages];
                    updatedMsgs[updatedMsgs.length - 1].content = botReply;
                    return { ...chat, messages: updatedMsgs };
                  }
                  return chat;
                }));
              } 
              // 🔵 출처(Sources) 수신 시: 해당 메시지에 출처 배열 추가
              else if (data.type === "sources") {
                setChatHistory(prev => prev.map(chat => {
                  if (Number(chat.id) === Number(currentChatId)) {
                    const updatedMsgs = [...chat.messages];
                    updatedMsgs[updatedMsgs.length - 1].sources = data.value;
                    return { ...chat, messages: updatedMsgs };
                  }
                  return chat;
                }));
              } 
              // 🔴 에러 수신 시: 에러 메시지 출력
              else if (data.type === "error") {
                setIsLoading(false);
                botReply += `\n\n⚠️ 오류: ${data.value}`;
                setChatHistory(prev => prev.map(chat => {
                  if (Number(chat.id) === Number(currentChatId)) {
                    const updatedMsgs = [...chat.messages];
                    updatedMsgs[updatedMsgs.length - 1].content = botReply;
                    return { ...chat, messages: updatedMsgs };
                  }
                  return chat;
                }));
              }
            } catch (err) {
              console.error("스트리밍 JSON 파싱 에러:", err, dataStr);
            }
          }
        }
      }
      
      // 채팅이 끝나면 최근 활성화된 채팅이 맨 위로 오도록 배열을 재정렬합니다 (기존 로직 유지)
      setChatHistory(prev => {
        const target = prev.find(c => Number(c.id) === Number(currentChatId));
        const filtered = prev.filter(c => Number(c.id) !== Number(currentChatId));
        return target ? [target, ...filtered].slice(0, 10) : prev.slice(0, 10);
      });

    } catch (err) {
      console.error("전송 오류:", err);
      // 네트워크 오류 시 사용자에게 알림
      setChatHistory(prev => prev.map(chat => {
        if (Number(chat.id) === Number(currentChatId)) {
          const updatedMsgs = [...chat.messages];
          updatedMsgs[updatedMsgs.length - 1].content = "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
          return { ...chat, messages: updatedMsgs };
        }
        return chat;
      }));
    } finally {
      setIsLoading(false); // 혹시라도 예외 상황에 대비해 스피너 끄기
    }
  }

const handleLogout = () => {
    localStorage.removeItem("cbnu_lms_session");
    localStorage.removeItem("cbnu_lms_username");
    setIsLoggedIn(false);
    setUserName("");
    // 백엔드에 로그아웃 API가 있다면 여기서 추가 호출
    // fetch("/api/lms/logout", { method: "POST" });
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
  messages={messages}
  handleSend={handleSend}
  isLoading={isLoading}
  useSearch={useSearch}
  onToggleSearch={() => setUseSearch(v => !v)}
      />
    </div>
  );
}