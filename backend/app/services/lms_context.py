from datetime import datetime, timezone
from app.models.schemas import LMSDataResponse


def build_lms_context(lms_data: LMSDataResponse) -> str:
    """
    LMSDataResponse → Gemini 시스템 프롬프트에 주입할 자연어 컨텍스트 반환.
    LMS 로그인이 안 됐거나 데이터가 없으면 빈 문자열 반환.
    """
    sections = []
    now = datetime.now(timezone.utc).timestamp()

    # ── 1. 수강 중인 과목 ──────────────────────────────────────
    if lms_data.courses:
        course_list = ", ".join(c.short_name for c in lms_data.courses)
        sections.append(f"수강 중인 과목: {course_list}")

    # ── 2. 미제출 과제 (마감 임박순 정렬) ─────────────────────
    upcoming: list[tuple[float, str]] = []
    overdue:  list[str] = []

    for a in lms_data.assignments:
        if a.submitted or not a.due_date:
            continue
        diff_days = (a.due_date - now) / 86400  # 초 → 일

        if diff_days < 0:
            overdue.append(f"  - [{a.course_name}] {a.name} (기한 초과)")
        elif diff_days <= 7:
            d_label = "D-DAY" if diff_days < 1 else f"D-{int(diff_days)}"
            upcoming.append((diff_days, f"  - [{a.course_name}] {a.name} ({d_label})"))

    upcoming.sort(key=lambda x: x[0])  # 급한 순 정렬

    if upcoming:
        lines = "\n".join(text for _, text in upcoming)
        sections.append(f"이번 주 마감 과제 (미제출):\n{lines}")
    if overdue:
        sections.append("기한 초과 과제:\n" + "\n".join(overdue))

    # ── 3. 최근 성적 (최대 5개) ───────────────────────────────
    if lms_data.grades:
        grade_lines = []
        for g in lms_data.grades[:5]:
            if g.grade and g.max_grade:
                score = f"{g.grade} / {g.max_grade}점"
            elif g.grade:
                score = f"{g.grade}점"
            else:
                score = "미공개"
            grade_lines.append(f"  - [{g.course_name}] {g.item_name}: {score}")
        sections.append("최근 성적:\n" + "\n".join(grade_lines))

    if not sections:
        return ""

    return "[현재 학생 LMS 정보]\n" + "\n\n".join(sections)