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
    """
    await page.goto(LMS_LOGIN_URL)

    try:
        # 요소를 못 찾을 경우 30초 무한 대기하는 것을 막기 위해 timeout 5초 설정
        await page.fill("#input-username", student_id, timeout=5000)
        await page.fill("#input-password", password, timeout=5000)
        await page.click("button[name='loginbutton']", timeout=5000)
        
        # [핵심] 로그인 버튼 클릭 후, 서버 처리가 완료될 때까지 안전하게 5초 대기
        await page.wait_for_load_state("networkidle", timeout=5000) 
        


        
    except Exception as e:
        # 아이디 칸이나 버튼을 5초 안에 못 찾으면 멈추지 말고 즉시 프론트엔드에 에러 던지기
        raise ValueError("LMS 사이트의 구조가 달라서 입력칸을 찾을 수 없습니다.")

    if "login" in page.url:
        raise ValueError("LMS 로그인 실패: 학번 또는 비밀번호를 확인하세요.")

# 💡 [해결 2] 이름 추출 로직 개선
    try:
        await page.click(".btn-userinfo img.userpicture", timeout=3000)

        # 👇 이 부분을 직접 찾으신 h4.username으로 수정합니다.
        user_name_el = page.locator("h4.username").first
        
        # 요소가 화면에 나타날 때까지 최대 3초만 기다립니다.
        await user_name_el.wait_for(timeout=3000)
        user_name = await user_name_el.inner_text()
        
        # '홍길동(20201234)' 처럼 학번이 같이 나오면 이름만 자르거나, 불필요한 공백 제거
        clean_name = user_name.split('(')[0].strip()
        
        if clean_name:
            return clean_name
        else:
            return "학우"
            
    except Exception as e:
        print(f"⚠️ 이름 파싱 실패: {e}")
        return "학우"

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


# ── 6. 과제 목록 크롤링 ───────────────────────────────────────────────────────
async def _get_assignments(page: Page, course_url: str) -> list[dict]:
    """
    개별 강의 페이지에서 과제 목록과 마감일, 제출 여부를 파싱합니다.
    반환 형태: [{"title": 과제명, "due_date": 마감일, "submitted": bool}, ...]
    """
    await page.goto(course_url)

    # 과제 activity 항목 선택 (assign = 과제)
    items = page.locator(".activity.assign")
    count = await items.count()

    assignments = []
    for i in range(count):
        item = items.nth(i)
        # 과제 제목
        title_el = item.locator(".instancename")
        title = await title_el.inner_text() if await title_el.count() > 0 else "제목 없음"
        # 마감일
        date_el = item.locator(".date")
        due_date = await date_el.inner_text() if await date_el.count() > 0 else ""
        # 제출 여부: 'submitted' 클래스가 있으면 제출 완료
        submitted = await item.locator(".submitted").count() > 0

        assignments.append({
            "title": title.replace("\xa0숨기기", "").strip(),
            "due_date": due_date.strip(),
            "submitted": submitted,
        })

    return assignments


# ── 7. 전체 데이터 수집 파이프라인 ────────────────────────────────────────────
async def _crawl(student_id: str, password: str) -> dict:
    """
    로그인 → 강의 목록 → 각 강의별 강의자료 + 과제 순서로 크롤링합니다.
    반환 형태:
    {
        "courses": [
            {
                "name": 강의명,
                "materials": [...],
                "assignments": [...]
            },
            ...
        ]
    }
    """
    async with async_playwright() as pw:
        # headless=True: 브라우저 창 없이 백그라운드 실행
        browser: Browser = await pw.chromium.launch(headless=True)
        page: Page = await browser.new_page()

        try:
            # 로그인
            user_name = await _login(page, student_id, password)
            # 수강 강의 목록
            courses = await _get_courses(page)

            result = []
            for course in courses:
                # 강의별 자료 + 과제 수집
                materials = await _get_materials(page, course["url"])
                assignments = await _get_assignments(page, course["url"])
                result.append({
                    "name": course["name"],
                    "materials": materials,
                    "assignments": assignments,
                })

            return {"courses": result, "user_name": user_name}
        except ValueError as ve:
            raise ve    
        finally:
            # 성공/실패 관계없이 브라우저 반드시 종료
            await browser.close()


# ── 8. 과제 목록 마감일 기준 정렬 ─────────────────────────────────────────────
def sort_assignments_by_due(courses: list[dict]) -> list[dict]:
    """
    전체 강의의 과제를 하나의 리스트로 합쳐 마감일 기준 오름차순 정렬합니다.
    마감일 없는 항목은 맨 뒤로 보냅니다.
    """
    all_assignments = []
    for course in courses:
        for assignment in course.get("assignments", []):
            # 어느 강의 과제인지 추적하기 위해 course_name 추가
            all_assignments.append({**assignment, "course_name": course["name"]})

    # 마감일 없는 경우 "~" 문자열로 맨 뒤 정렬
    all_assignments.sort(key=lambda a: a.get("due_date") or "~")
    return all_assignments


# ── 9. 강의자료 목록 통합 반환 ────────────────────────────────────────────────
def get_all_materials(courses: list[dict]) -> list[dict]:
    """
    전체 강의의 강의자료를 하나의 리스트로 합쳐 반환합니다.
    각 항목에 course_name 필드가 포함됩니다.
    """
    all_materials = []
    for course in courses:
        for material in course.get("materials", []):
            all_materials.append({**material, "course_name": course["name"]})
    return all_materials


# ── 10. 통합 진입점 (동기 래퍼) ───────────────────────────────────────────────
def get_lms_data(student_id: str | None = None, password: str | None = None) -> dict:
    """
    FastAPI 엔드포인트에서 호출하는 동기 진입점입니다.
    """
    sid, pw = _get_credentials(student_id, password)
    data = asyncio.run(_crawl(sid, pw))

    courses = data["courses"]
    return {
        "user_name": data["user_name"],
        "courses": courses,
        "assignments": sort_assignments_by_due(courses),
        "materials": get_all_materials(courses),
    }
