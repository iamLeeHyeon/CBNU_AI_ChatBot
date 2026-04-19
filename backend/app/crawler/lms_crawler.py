import os
import asyncio
from playwright.async_api import async_playwright, Page, Browser

# ── 1. LMS 기본 상수 ──────────────────────────────────────────────────────────
# 충북대 LMS 접속 URL과 각 페이지 경로를 상수로 관리합니다.
LMS_BASE_URL = "https://lms.chungbuk.ac.kr"
LMS_LOGIN_URL = f"{LMS_BASE_URL}/login/index.php"
LMS_DASHBOARD_URL = f"{LMS_BASE_URL}/my"


# ── 2. 환경변수에서 로그인 정보 읽기 ──────────────────────────────────────────
def _get_credentials(student_id: str | None = None, password: str | None = None) -> tuple[str, str]:
    """
    인자로 받은 학번/비밀번호를 우선 사용하고,
    없으면 환경변수 LMS_ID / LMS_PW에서 읽어 반환합니다.
    민감 정보를 코드에 하드코딩하지 않기 위한 함수입니다.
    """
    sid = student_id or os.getenv("LMS_ID")
    pw = password or os.getenv("LMS_PW")
    if not sid or not pw:
        raise ValueError("LMS 학번(LMS_ID)과 비밀번호(LMS_PW)가 설정되지 않았습니다.")
    return sid, pw


# ── 3. 브라우저 실행 및 LMS 로그인 ────────────────────────────────────────────
async def _login(page: Page, student_id: str, password: str) -> None:
    """
    Playwright로 LMS 로그인 페이지에 접속 후 학번/비밀번호를 입력합니다.
    로그인 실패 시 예외를 발생시킵니다.
    """
    await page.goto(LMS_LOGIN_URL)

    # 학번 입력란에 학번 입력
    await page.fill("#username", student_id)
    # 비밀번호 입력란에 비밀번호 입력
    await page.fill("#password", password)
    # 로그인 버튼 클릭
    await page.click("#loginbtn")

    # 로그인 실패 메시지가 있으면 예외 처리
    error = page.locator(".loginerrors")
    if await error.count() > 0:
        raise ValueError("LMS 로그인 실패: 학번 또는 비밀번호를 확인하세요.")


# ── 4. 수강 중인 강의 목록 가져오기 ───────────────────────────────────────────
async def _get_courses(page: Page) -> list[dict]:
    """
    LMS 대시보드에서 현재 수강 중인 강의 목록을 파싱합니다.
    반환 형태: [{"name": 강의명, "url": 강의 URL}, ...]
    """
    await page.goto(LMS_DASHBOARD_URL)

    # 강의 카드 목록 선택 (LMS Moodle 기본 구조 기준)
    course_links = page.locator(".coursename a")
    count = await course_links.count()

    courses = []
    for i in range(count):
        link = course_links.nth(i)
        name = await link.inner_text()
        url = await link.get_attribute("href")
        courses.append({"name": name.strip(), "url": url})

    return courses


# ── 5. 강의자료 목록 크롤링 ───────────────────────────────────────────────────
async def _get_materials(page: Page, course_url: str) -> list[dict]:
    """
    개별 강의 페이지에서 강의자료(파일/링크) 목록을 파싱합니다.
    반환 형태: [{"title": 자료명, "date": 날짜, "url": URL}, ...]
    """
    await page.goto(course_url)

    # 강의자료 activity 항목 선택 (resource = 파일 자료)
    items = page.locator(".activity.resource, .activity.url")
    count = await items.count()

    materials = []
    for i in range(count):
        item = items.nth(i)
        # 자료 제목
        title_el = item.locator(".instancename")
        title = await title_el.inner_text() if await title_el.count() > 0 else "제목 없음"
        # 날짜 정보 (있는 경우만)
        date_el = item.locator(".date")
        date = await date_el.inner_text() if await date_el.count() > 0 else ""
        # 자료 링크
        link_el = item.locator("a")
        url = await link_el.get_attribute("href") if await link_el.count() > 0 else ""

        materials.append({
            "title": title.replace("\xa0숨기기", "").strip(),  # LMS가 제목에 붙이는 불필요 텍스트 제거
            "date": date.strip(),
            "url": url,
        })

    return materials
