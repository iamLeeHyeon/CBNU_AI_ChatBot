async def stream_chat_response(messages, search_results=None, lms_context=""):
    """
    Gemini 응답을 토큰 단위로 스트리밍하는 비동기 제너레이터.
    router의 SSE 스트림에서 async for로 소비.
    """
    import asyncio as _asyncio

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    system_instruction = f"{SYSTEM_PROMPT}\n\n[시스템 정보]\n현재 일시: {now}"
    
    # 🚨 HEAD 브랜치의 LMS 컨텍스트 주입 로직 병합
    if lms_context:
        system_instruction += f"\n\n[LMS 연동 정보]\n{lms_context}"

    try:
        model = get_model(GEMINI_CHAT_CONFIG, system_instruction)
        history = _build_history(messages)

        total_tokens = model.count_tokens(str(history)).total_tokens
        print(f"현재 전송 토큰 수: {total_tokens}")

        chat = model.start_chat(history=history)
        user_message = _build_user_message(
            messages[-1].content,
            search_results or [],
        )

        queue = _asyncio.Queue()
        loop = _asyncio.get_event_loop()

        def _run_stream():
            try:
                for chunk in chat.send_message(user_message, stream=True):
                    if chunk.text:
                        loop.call_soon_threadsafe(queue.put_nowait, chunk.text)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        import threading as _threading
        thread = _threading.Thread(target=_run_stream, daemon=True)
        thread.start()

        while True:
            item = await queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            
            words = item.split(" ")
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                await _asyncio.sleep(0.03)

    except Exception as e:
        print(f"[스트리밍 오류] {e}")
        yield "죄송합니다. 현재 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요."