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
        {message.content}
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
