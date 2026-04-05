import { useState } from "react";

export default function InputBar({ onSend, isLoading, useSearch, onToggleSearch }) {
  const [text, setText] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSend(text.trim());
    setText("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      handleSubmit(e);
    }
  }

  return (
    <div className="border-t border-gray-200 px-4 py-3 bg-white">
      <div className="flex items-center gap-2 mb-2">
        <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={useSearch}
            onChange={onToggleSearch}
            className="accent-cbnu-blue"
          />
          웹 검색 사용
        </label>
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-cbnu-blue transition-colors"
        />
        <button
          type="submit"
          disabled={isLoading || !text.trim()}
          className="bg-cbnu-blue text-white px-4 py-2 rounded-xl text-sm font-medium disabled:opacity-40 hover:bg-cbnu-light transition-colors"
        >
          전송
        </button>
      </form>
    </div>
  );
}
