import { useState } from "react";

export default function LMSLogin({ onLoginSuccess }) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/lms/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // 백엔드 스키마에 맞게 필드명 설정 (보통 username이나 student_id)
        body: JSON.stringify({ student_id: studentId, password: password }),
      });

      const data = await res.json();

      if (res.ok && data.success !== false) {
        // 로그인 성공 시 백엔드에서 받아온 이름을 부모 컴포넌트로 전달
        onLoginSuccess(data.user_name || "학우");
      } else {
        // 실패 시 요구하신 에러 메시지 출력
        setError("로그인에 실패하였습니다, 다시 시도해 보세요");
      }
    } catch (err) {
      setError("서버와 통신할 수 없습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-center">
      <h1 className="text-5xl font-black text-cbnu-blue mb-4">환영합니다</h1>
      <p className="text-gray-500 mb-8">충북대학교 통합 AI 학습 시스템입니다.</p>
      
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-2xl shadow-xl w-96 mx-auto flex flex-col gap-4">
        <input 
          type="text" 
          placeholder="학번" 
          className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          value={studentId} onChange={(e) => setStudentId(e.target.value)}
          required
        />
        <input 
          type="password" 
          placeholder="LMS 비밀번호" 
          className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          value={password} onChange={(e) => setPassword(e.target.value)}
          required
        />
        
        {/* 로그인 실패 시 나타나는 빨간색 에러 메시지 */}
        {error && (
          <div className="bg-red-50 text-red-500 text-sm p-3 rounded-lg border border-red-100 text-left animate-pulse">
            ⚠️ {error}
          </div>
        )}
        
        <button 
          type="submit" 
          disabled={isLoading}
          className={`text-white p-3 rounded-lg font-bold transition-colors mt-2 ${
            isLoading ? "bg-gray-400 cursor-not-allowed" : "bg-cbnu-blue hover:bg-blue-800"
          }`}
        >
          {isLoading ? "로그인 중..." : "LMS 연동 로그인"}
        </button>
      </form>
    </div>
  );
}