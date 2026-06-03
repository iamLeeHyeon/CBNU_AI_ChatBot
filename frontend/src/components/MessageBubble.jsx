// 볼드체(**)를 <strong> 태그로 변환해 주는 파싱 함수
const parseMarkdownBold = (text) => {
  if (!text) return "";

  const parts = text.split(/(\*\*.*?\*\*)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        // AI 말풍선은 배경이 회색이므로 글씨를 검은색(text-black)으로 뚜렷하게 줍니다.
        <strong key={index} className="font-bold text-black">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={index}>{part}</span>;
  });
};

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-cbnu-blue flex items-center justify-center text-white text-xs font-bold mr-2 shrink-0">
          AI
        </div>
      )}
      <div
        className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-cbnu-blue text-white rounded-br-sm"
            : "bg-gray-100 text-gray-800 rounded-bl-sm"
        }`}
      >
        {/* 👇 여기가 핵심입니다: 유저면 그대로, AI면 파싱 함수를 통과시킵니다 👇 */}
        {isUser ? message.content : parseMarkdownBold(message.content)}

        {/* 출처 표시 영역 */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-300 text-xs text-gray-500">
            <p className="font-semibold mb-1">출처</p>
            {message.sources.map((url, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="block truncate hover:underline text-cbnu-light"
              >
                {url}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}