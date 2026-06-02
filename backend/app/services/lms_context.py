from datetime import datetime, timezone


def build_lms_context(data: dict) -> str:
    """
    _sessions의 data dict → Gemini 시스템 프롬프트에 주입할 자연어 컨텍스트 반환.
    LMS 로그인이 안 됐거나 데이터가 없으면 빈 문자열 반환.
    """
    sections = []
    now = datetime.now(timezone.utc).timestamp()

    courses = data.get("courses", [])
    if courses:
        names = ", ".join(c.get("short_name") or c.get("full_name", "") for c in courses)
        sections.append(f"수강 중인 과목: {names}")

    upcoming: list[tuple[float, str]] = []
    overdue: list[str] = []

    for a in data.get("assignments", []):
        if a.get("submitted") or not a.get("due_date"):
            continue
        diff_days = (a["due_date"] - now) / 86400

        if diff_days < 0:
            overdue.append(f"  - [{a['course_name']}] {a['name']} (기한 초과)")
        elif diff_days <= 7:
            d_label = "D-DAY" if diff_days < 1 else f"D-{int(diff_days)}"
            upcoming.append((diff_days, f"  - [{a['course_name']}] {a['name']} ({d_label})"))

    upcoming.sort(key=lambda x: x[0])

    if upcoming:
        sections.append("이번 주 마감 과제 (미제출):\n" + "\n".join(t for _, t in upcoming))
    if overdue:
        sections.append("기한 초과 과제:\n" + "\n".join(overdue))

    grades = data.get("grades", [])
    if grades:
        grade_lines = []
        for g in grades[:5]:
            grade_val = g.get("grade")
            max_val = g.get("max_grade")
            if grade_val and max_val:
                score = f"{grade_val} / {max_val}점"
            elif grade_val:
                score = f"{grade_val}점"
            else:
                score = "미공개"
            grade_lines.append(f"  - [{g.get('course_name', '')}] {g.get('item_name', '성적')}: {score}")
        sections.append("최근 성적:\n" + "\n".join(grade_lines))

    if not sections:
        return ""

    return "[현재 학생 LMS 정보]\n" + "\n\n".join(sections)