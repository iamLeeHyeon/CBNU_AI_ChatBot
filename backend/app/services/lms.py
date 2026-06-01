import httpx
from typing import Optional

LMS_BASE = "https://lms.chungbuk.ac.kr"
REST_URL = f"{LMS_BASE}/webservice/rest/server.php"


def _rest(token: str, function: str, **params) -> dict:
    """LMS REST API 공통 호출."""
    response = httpx.post(
        REST_URL,
        params={"wstoken": token, "wsfunction": function, "moodlewsrestformat": "json"},
        data=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    # LMS가 오류를 200으로 반환하는 경우 처리
    if isinstance(data, dict) and data.get("exception"):
        raise ValueError(data.get("message", "LMS API 오류"))
    return data


def get_token(username: str, password: str) -> str:
    """ID/PW로 LMS 토큰 발급. 실패 시 ValueError."""
    response = httpx.post(
        f"{LMS_BASE}/login/token.php",
        data={"username": username, "password": password, "service": "moodle_mobile_app"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if "token" not in data:
        raise ValueError(data.get("error", "로그인 실패: 아이디 또는 비밀번호를 확인하세요."))
    return data["token"]


def get_user_info(token: str) -> dict:
    """로그인한 사용자 기본 정보 반환."""
    data = _rest(token, "core_webservice_get_site_info")

    fullname = data.get("fullname", "").strip()

    if not fullname:
        firstname = data.get("firstname", "").strip()
        lastname = data.get("lastname", "").strip()
        fullname = f"{lastname}{firstname}".strip()

    return {
        "user_id": data.get("userid"),
        "user_name": fullname,
    }


def get_courses(token: str) -> list[dict]:
    """수강 중인 강좌 목록 반환."""
    data = _rest(
        token,
        "core_course_get_enrolled_courses_by_timeline_classification",
        classification="inprogress",
    )
    courses = data if isinstance(data, list) else data.get("courses", [])
    return [
        {"id": c["id"], "full_name": c["fullname"], "short_name": c["shortname"]}
        for c in courses
    ]


def get_assignments(token: str, course_ids: list[int]) -> list[dict]:
    """과제 목록과 마감일 반환."""
    if not course_ids:
        return []

    params = {f"courseids[{i}]": cid for i, cid in enumerate(course_ids)}
    data = _rest(token, "mod_assign_get_assignments", **params)

    results = []
    for course in data.get("courses", []):
        course_name = course.get("fullname", "")
        for assign in course.get("assignments", []):
            due = assign.get("duedate")
            results.append({
                "id": assign["id"],
                "course_name": course_name,
                "name": assign["name"],
                "due_date": due if due and due > 0 else None,
                "submitted": False,  # 제출 여부는 별도 조회
            })
    return results


def get_submission_statuses(token: str, assignment_ids: list[int]) -> dict[int, bool]:
    """과제 ID별 제출 여부 반환. {assign_id: True/False}"""
    submitted_map: dict[int, bool] = {}
    for aid in assignment_ids:
        try:
            data = _rest(token, "mod_assign_get_submission_status", assignid=aid)
            submission = data.get("lastattempt", {}).get("submission", {})
            status = submission.get("status", "")
            submitted_map[aid] = status == "submitted"
        except Exception:
            submitted_map[aid] = False
    return submitted_map


def get_grades(token: str, user_id: int) -> list[dict]:
    """전체 강좌 성적 반환."""
    data = _rest(token, "gradereport_overview_get_course_grades", userid=user_id)
    results = []
    for item in data.get("grades", []):
        results.append({
            "course_id": item.get("courseid"),
            "course_name": item.get("coursefullname", ""),
            "item_name": "최종 성적",
            "grade": item.get("grade"),
            "max_grade": None,
        })
    return results


def get_materials(token: str, course_ids: list[int]) -> list[dict]:
    """강좌별 강의자료(파일/링크) 목록 반환. core_course_get_contents 사용."""
    materials = []
    for cid in course_ids:
        try:
            sections = _rest(token, "core_course_get_contents", courseid=cid)
            for section in sections:
                for module in section.get("modules", []):
                    if module.get("modname") in ("resource", "url"):
                        materials.append({
                            "title": module.get("name", ""),
                            "url": module.get("url", ""),
                            "course_id": cid,
                        })
        except Exception:
            pass
    return materials


def get_calendar(token: str, user_id: int) -> list[dict]:
    """향후 60일 캘린더 이벤트 반환."""
    import time
    now = int(time.time())
    sixty_days = 60 * 24 * 60 * 60

    data = _rest(
        token,
        "core_calendar_get_calendar_events",
        **{
            "options[userevents]": 1,
            "options[siteevents]": 1,
            "options[timestart]": now,
            "options[timeend]": now + sixty_days,
        },
    )
    results = []
    for event in data.get("events", []):
        results.append({
            "id": event["id"],
            "name": event["name"],
            "time_start": event["timestart"],
            "event_type": event.get("eventtype", ""),
        })
    return results
