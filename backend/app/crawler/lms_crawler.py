import os
import datetime 
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



# ── 4. 수강 중인 강의 목록 가져오기 (수정본) ───────────────────────────────────────────
async def _get_courses(page: Page) -> list[dict]:
    await page.goto(LMS_DASHBOARD_URL)
    await page.wait_for_selector('div[data-region="courses-view"]', timeout=10000)
    
    try:
        filter_btn = page.locator("#groupingdropdown")
        await filter_btn.click(timeout=3000)
        in_progress_option = page.locator('.dropdown-menu[aria-labelledby="groupingdropdown"] a:has-text("progress"), .dropdown-menu[aria-labelledby="groupingdropdown"] a:has-text("진행")').first
        await in_progress_option.click(timeout=3000)
        await page.wait_for_timeout(2000)
    except Exception:
        pass

    # [핵심 1] '최근 학습한 강좌' 구역을 피하기 위해 courses-view 하위의 카드만 타겟팅
    course_cards = page.locator('div[data-region="courses-view"] .card.dashboard-card[data-region="course-content"]')
    count = await course_cards.count()

    courses_dict = {} # [핵심 2] URL을 키값으로 사용하여 완벽한 중복 제거
    
    for i in range(count):
        card = course_cards.nth(i)
        
        link_el = card.locator('a[tabindex="-1"]').first
        url = await link_el.get_attribute("href") if await link_el.count() > 0 else ""
        
        name_el = card.locator('.coursename span.multiline')
        if await name_el.count() > 0:
            raw_name = await name_el.inner_text()
            clean_name = raw_name.strip()
        else:
            continue # 🚨 이름이 안 찾아지는 찌꺼기 카드는 과감히 스킵!
            
        # URL이 정상적이고, 딕셔너리에 아직 등록되지 않은 강좌만 추가
        if url and url not in courses_dict:
            courses_dict[url] = {"name": clean_name, "url": url}

    # 딕셔너리의 값들만 리스트로 변환하여 반환
    return list(courses_dict.values())

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






# ── 6. 과제 목록 크롤링 (수정본) ───────────────────────────────────────────────────────
async def _get_assignments(page: Page, course_url: str) -> list[dict]:
    """
    개별 강의의 '과제 전용 페이지'로 이동하여 마감일과 제출 여부를 파싱합니다.
    기한이 지났거나 제출 완료된 과제는 제외합니다.
    """
    # [핵심 1] 강의 메인 화면(course/view.php) URL을 과제 전용 화면(mod/assign/index.php) URL로 변환!
    assign_url = course_url.replace("course/view.php", "mod/assign/index.php")
    await page.goto(assign_url)
    
    # 만약 과제가 하나도 없는 강의라면 테이블이 없을 수 있으므로 예외 처리
    try:
        await page.wait_for_selector("table.generaltable tbody tr", timeout=3000)
    except Exception:
        return [] # 과제 없음

    rows = page.locator("table.generaltable tbody tr")
    count = await rows.count()

    assignments = []
    now = datetime.datetime.now() # 현재 시간 (기한 만료 비교용)

    for i in range(count):
        row = rows.nth(i)
        
        # 테이블의 가로줄(구분선)이나 빈 칸 건너뛰기
        if await row.locator("td.c1 a").count() == 0:
            continue

        # HTML 구조에 맞춰 텍스트 추출 (c1=과제명, c2=종료일시, c3=제출물)
        title = await row.locator("td.c1 a").inner_text()
        due_date_str = await row.locator("td.c2").inner_text()
        status_str = await row.locator("td.c3").inner_text()

        # [핵심 2] 이미 "제출 완료"한 과제는 목록에서 아예 삭제
        if "제출 완료" in status_str:
            continue
            
        # [핵심 3] 마감 기한이 지난 과제 필터링
        try:
            # due_date_str ("2026-06-1 23:00")을 파이썬 시간 데이터로 변환
            due_date = datetime.datetime.strptime(due_date_str.strip(), "%Y-%m-%d %H:%M")
            if due_date < now:
                continue # 현재 시간보다 과거면 스킵!
        except ValueError:
            pass # 혹시 날짜가 "-" 거나 형식이 다르면 그냥 통과시킴

        # 남은 진짜 '해야 할 과제'들만 리스트에 추가
        clean_title = title.replace("\xa0", " ").strip()
        
        assignments.append({
            "title": clean_title,
            "due_date": due_date_str.strip(),
            "submitted": False, # 위에서 제출 완료를 다 걸렀으므로 여기 오는 건 무조건 미제출(False)입니다.
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
        browser: Browser = await pw.chromium.launch(headless=False)
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


# ── 8. 과제 목록 마감일 기준 정렬 (수정본) ─────────────────────────────────────────────
def sort_assignments_by_due(courses: list[dict]) -> list[dict]:
    all_assignments = []
    for course in courses:
        for assignment in course.get("assignments", []):
            all_assignments.append({**assignment, "course_name": course["name"]})

    def get_sort_key(a):
        date_str = a.get("due_date", "")
        # 마감일 정보가 없으면 정렬 순서를 맨 뒤로(아주 먼 미래로 취급) 미룹니다.
        if not date_str or "표기 없음" in date_str:
            return "9999-12-31" 
        return date_str

    # 마감일 문자열 오름차순(빠른 날짜가 먼저)으로 정렬
    all_assignments.sort(key=get_sort_key)
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
