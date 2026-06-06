"""
tests/test_lms_crawler.py
app/crawler/lms_crawler.py 유닛 테스트
"""
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


from app.crawler.lms_crawler import (
    _get_credentials,
    sort_assignments_by_due,
    get_all_materials,
    get_lms_data,
    _login,
    _get_courses,
    _get_materials,
    _get_assignments,
    LMS_LOGIN_URL,
    LMS_DASHBOARD_URL,
)


# ════════════════════════════════════════════════════════════════
# 1. _get_credentials
# ════════════════════════════════════════════════════════════════
class TestGetCredentials:

    def test_인자_우선_사용(self):
        sid, pw = _get_credentials("2020001", "pw123")
        assert sid == "2020001"
        assert pw == "pw123"

    def test_환경변수_폴백(self, monkeypatch):
        monkeypatch.setenv("LMS_ID", "env_id")
        monkeypatch.setenv("LMS_PW", "env_pw")
        sid, pw = _get_credentials()
        assert sid == "env_id"
        assert pw == "env_pw"

    def test_인자가_환경변수보다_우선(self, monkeypatch):
        monkeypatch.setenv("LMS_ID", "env_id")
        monkeypatch.setenv("LMS_PW", "env_pw")
        sid, pw = _get_credentials("arg_id", "arg_pw")
        assert sid == "arg_id"
        assert pw == "arg_pw"

    def test_둘_다_없으면_ValueError(self, monkeypatch):
        monkeypatch.delenv("LMS_ID", raising=False)
        monkeypatch.delenv("LMS_PW", raising=False)
        with pytest.raises(ValueError):
            _get_credentials()

    def test_id만_없으면_ValueError(self, monkeypatch):
        monkeypatch.delenv("LMS_ID", raising=False)
        monkeypatch.setenv("LMS_PW", "pw")
        with pytest.raises(ValueError):
            _get_credentials()

    def test_pw만_없으면_ValueError(self, monkeypatch):
        monkeypatch.setenv("LMS_ID", "id")
        monkeypatch.delenv("LMS_PW", raising=False)
        with pytest.raises(ValueError):
            _get_credentials()


# ════════════════════════════════════════════════════════════════
# 2. sort_assignments_by_due
# ════════════════════════════════════════════════════════════════
class TestSortAssignmentsByDue:

    def _make_courses(self, assignments_per_course):
        return [
            {"name": f"강의{i}", "assignments": asgns}
            for i, asgns in enumerate(assignments_per_course)
        ]

    def test_마감일_오름차순_정렬(self):
        courses = self._make_courses([
            [{"title": "과제B", "due_date": "2026-06-20 23:00", "submitted": False}],
            [{"title": "과제A", "due_date": "2026-06-10 23:00", "submitted": False}],
        ])
        result = sort_assignments_by_due(courses)
        assert result[0]["title"] == "과제A"
        assert result[1]["title"] == "과제B"

    def test_마감일_없는_항목은_맨_뒤(self):
        courses = self._make_courses([
            [
                {"title": "날짜없음", "due_date": "", "submitted": False},
                {"title": "날짜있음", "due_date": "2026-06-05 23:00", "submitted": False},
            ]
        ])
        result = sort_assignments_by_due(courses)
        assert result[0]["title"] == "날짜있음"
        assert result[-1]["title"] == "날짜없음"

    def test_표기없음_항목은_맨_뒤(self):
        courses = self._make_courses([
            [
                {"title": "표기없음", "due_date": "표기 없음", "submitted": False},
                {"title": "날짜있음", "due_date": "2026-06-01 23:00", "submitted": False},
            ]
        ])
        result = sort_assignments_by_due(courses)
        assert result[-1]["title"] == "표기없음"

    def test_course_name_필드_추가됨(self):
        courses = [{"name": "운영체제", "assignments": [
            {"title": "과제1", "due_date": "2026-06-10 23:00", "submitted": False}
        ]}]
        result = sort_assignments_by_due(courses)
        assert result[0]["course_name"] == "운영체제"

    def test_빈_과제_목록(self):
        courses = [{"name": "강의", "assignments": []}]
        assert sort_assignments_by_due(courses) == []

    def test_여러_강의_과제_통합(self):
        courses = self._make_courses([
            [{"title": "A", "due_date": "2026-06-15 23:00", "submitted": False}],
            [{"title": "B", "due_date": "2026-06-12 23:00", "submitted": False}],
            [{"title": "C", "due_date": "2026-06-18 23:00", "submitted": False}],
        ])
        result = sort_assignments_by_due(courses)
        titles = [r["title"] for r in result]
        assert titles == ["B", "A", "C"]


# ════════════════════════════════════════════════════════════════
# 3. get_all_materials
# ════════════════════════════════════════════════════════════════
class TestGetAllMaterials:

    def test_강의자료_통합_반환(self):
        courses = [
            {"name": "강의A", "materials": [
                {"title": "자료1", "date": "2026-06-01", "url": "http://a.com/1"},
                {"title": "자료2", "date": "2026-06-02", "url": "http://a.com/2"},
            ]},
            {"name": "강의B", "materials": [
                {"title": "자료3", "date": "2026-06-03", "url": "http://b.com/1"},
            ]},
        ]
        result = get_all_materials(courses)
        assert len(result) == 3

    def test_course_name_필드_포함(self):
        courses = [{"name": "알고리즘", "materials": [
            {"title": "1주차", "date": "", "url": "http://x.com"}
        ]}]
        result = get_all_materials(courses)
        assert result[0]["course_name"] == "알고리즘"

    def test_원본_필드_보존(self):
        courses = [{"name": "강의", "materials": [
            {"title": "슬라이드", "date": "2026-05-01", "url": "http://lms.kr/file"}
        ]}]
        result = get_all_materials(courses)
        assert result[0]["title"] == "슬라이드"
        assert result[0]["date"] == "2026-05-01"
        assert result[0]["url"] == "http://lms.kr/file"

    def test_자료_없는_강의(self):
        courses = [{"name": "강의", "materials": []}]
        assert get_all_materials(courses) == []

    def test_빈_강의_목록(self):
        assert get_all_materials([]) == []


# ════════════════════════════════════════════════════════════════
# 4. _login (async)
# locator()는 Playwright에서 동기 메서드이므로 MagicMock 사용
# ════════════════════════════════════════════════════════════════
def _make_page_mock(url="https://lms.chungbuk.ac.kr/my"):
    page = AsyncMock()
    type(page).url = PropertyMock(return_value=url)

    name_el = AsyncMock()
    name_el.inner_text = AsyncMock(return_value="홍길동(20201234)")
    name_el.wait_for = AsyncMock()

    locator_mock = MagicMock()
    locator_mock.first = name_el

    page.locator = MagicMock(return_value=locator_mock)
    return page


class TestLogin:

    @pytest.mark.asyncio
    async def test_로그인_성공_이름_반환(self):
        page = _make_page_mock()
        result = await _login(page, "2020001", "pw")
        assert result == "홍길동"

    @pytest.mark.asyncio
    async def test_괄호_없는_이름(self):
        page = _make_page_mock()
        name_el = AsyncMock()
        name_el.inner_text = AsyncMock(return_value="김철수")
        name_el.wait_for = AsyncMock()
        page.locator.return_value.first = name_el
        result = await _login(page, "2020001", "pw")
        assert result == "김철수"

    @pytest.mark.asyncio
    async def test_login_url_남아있으면_ValueError(self):
        page = _make_page_mock(url="https://lms.chungbuk.ac.kr/login/index.php")
        with pytest.raises(ValueError, match="로그인 실패"):
            await _login(page, "wrong", "wrong")

    @pytest.mark.asyncio
    async def test_fill_실패시_ValueError(self):
        page = AsyncMock()
        page.goto = AsyncMock()
        page.fill = AsyncMock(side_effect=Exception("timeout"))
        with pytest.raises(ValueError, match="구조"):
            await _login(page, "id", "pw")

    @pytest.mark.asyncio
    async def test_이름_파싱_실패시_학우_반환(self):
        page = _make_page_mock()
        page.locator.return_value.first.wait_for = AsyncMock(side_effect=Exception("not found"))
        result = await _login(page, "2020001", "pw")
        assert result == "학우"


# ════════════════════════════════════════════════════════════════
# 5. _get_courses (async)
# ════════════════════════════════════════════════════════════════
class TestGetCourses:

    def _make_card_mock(self, name: str, url: str):
        card = MagicMock()  # card 자체도 MagicMock (locator 반환값이 동기)

        link_el = AsyncMock()
        link_el.count = AsyncMock(return_value=1)
        link_el.get_attribute = AsyncMock(return_value=url)

        name_el = AsyncMock()
        name_el.count = AsyncMock(return_value=1)
        name_el.inner_text = AsyncMock(return_value=name)

        def locator_side_effect(selector):
            if "tabindex" in selector:
                m = MagicMock()
                m.count = AsyncMock(return_value=1)
                m.get_attribute = AsyncMock(return_value=url)
                m.first = link_el
                return m
            elif "multiline" in selector:
                return name_el
            return MagicMock()

        card.locator.side_effect = locator_side_effect
        return card

    @pytest.mark.asyncio
    async def test_강의_목록_반환(self):
        page = AsyncMock()

        card1 = self._make_card_mock("운영체제", "http://lms/course/view.php?id=1")
        card2 = self._make_card_mock("알고리즘", "http://lms/course/view.php?id=2")

        course_cards = MagicMock()  # locator() 반환값은 MagicMock
        course_cards.count = AsyncMock(return_value=2)
        course_cards.nth = MagicMock(side_effect=[card1, card2])

        page.locator = MagicMock(return_value=course_cards)

        result = await _get_courses(page)
        assert len(result) == 2
        names = [c["name"] for c in result]
        assert "운영체제" in names
        assert "알고리즘" in names

    @pytest.mark.asyncio
    async def test_중복_URL_제거(self):
        page = AsyncMock()

        same_url = "http://lms/course/view.php?id=1"
        card1 = self._make_card_mock("운영체제", same_url)
        card2 = self._make_card_mock("운영체제(중복)", same_url)

        course_cards = MagicMock()
        course_cards.count = AsyncMock(return_value=2)
        course_cards.nth = MagicMock(side_effect=[card1, card2])

        page.locator = MagicMock(return_value=course_cards)

        result = await _get_courses(page)
        assert len(result) == 1


# ════════════════════════════════════════════════════════════════
# 6. _get_materials (async)
# ════════════════════════════════════════════════════════════════
class TestGetMaterials:

    @pytest.mark.asyncio
    async def test_자료_파싱(self):
        page = AsyncMock()

        item = MagicMock()

        title_el = AsyncMock()
        title_el.count = AsyncMock(return_value=1)
        title_el.inner_text = AsyncMock(return_value="1주차 슬라이드\xa0숨기기")

        date_el = AsyncMock()
        date_el.count = AsyncMock(return_value=1)
        date_el.inner_text = AsyncMock(return_value="2026-06-01")

        link_el = AsyncMock()
        link_el.count = AsyncMock(return_value=1)
        link_el.get_attribute = AsyncMock(return_value="http://lms/mod/resource/view.php?id=1")

        def item_locator(sel):
            if "instancename" in sel:
                return title_el
            elif ".date" in sel:
                return date_el
            else:
                return link_el

        item.locator.side_effect = item_locator

        items_mock = MagicMock()
        items_mock.count = AsyncMock(return_value=1)
        items_mock.nth = MagicMock(return_value=item)

        page.locator = MagicMock(return_value=items_mock)

        result = await _get_materials(page, "http://lms/course/view.php?id=1")
        assert len(result) == 1
        assert result[0]["title"] == "1주차 슬라이드"
        assert result[0]["date"] == "2026-06-01"

    @pytest.mark.asyncio
    async def test_자료_없으면_빈_리스트(self):
        page = AsyncMock()
        items_mock = MagicMock()
        items_mock.count = AsyncMock(return_value=0)
        page.locator = MagicMock(return_value=items_mock)

        result = await _get_materials(page, "http://lms/course/view.php?id=99")
        assert result == []


# ════════════════════════════════════════════════════════════════
# 7. _get_assignments (async)
# ════════════════════════════════════════════════════════════════
class TestGetAssignments:

    def _make_row(self, title: str, due_date: str, status: str):
        row = MagicMock()

        title_anchor = AsyncMock()
        title_anchor.count = AsyncMock(return_value=1)
        title_anchor.inner_text = AsyncMock(return_value=title)

        due_el = AsyncMock()
        due_el.inner_text = AsyncMock(return_value=due_date)

        status_el = AsyncMock()
        status_el.inner_text = AsyncMock(return_value=status)

        def row_locator(sel):
            if "c1" in sel:
                return title_anchor
            elif "c2" in sel:
                return due_el
            elif "c3" in sel:
                return status_el
            # 기본 반환값도 count()가 await 될 수 있으므로 AsyncMock
            m = AsyncMock()
            m.count = AsyncMock(return_value=0)
            return m

        row.locator.side_effect = row_locator
        return row

    @pytest.mark.asyncio
    async def test_미제출_미래_과제_포함(self):
        page = AsyncMock()
        future = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M")
        row = self._make_row("중간과제", future, "미제출")

        rows_mock = MagicMock()
        rows_mock.count = AsyncMock(return_value=1)
        rows_mock.nth = MagicMock(return_value=row)
        page.locator = MagicMock(return_value=rows_mock)

        result = await _get_assignments(page, "http://lms/course/view.php?id=1")
        assert len(result) == 1
        assert result[0]["title"] == "중간과제"
        assert result[0]["submitted"] is False

    @pytest.mark.asyncio
    async def test_제출완료_과제_제외(self):
        page = AsyncMock()
        future = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M")
        row = self._make_row("제출된과제", future, "제출 완료")

        rows_mock = MagicMock()
        rows_mock.count = AsyncMock(return_value=1)
        rows_mock.nth = MagicMock(return_value=row)
        page.locator = MagicMock(return_value=rows_mock)

        result = await _get_assignments(page, "http://lms/course/view.php?id=1")
        assert result == []

    @pytest.mark.asyncio
    async def test_기한_지난_과제_제외(self):
        page = AsyncMock()
        past = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        row = self._make_row("기한만료과제", past, "미제출")

        rows_mock = MagicMock()
        rows_mock.count = AsyncMock(return_value=1)
        rows_mock.nth = MagicMock(return_value=row)
        page.locator = MagicMock(return_value=rows_mock)

        result = await _get_assignments(page, "http://lms/course/view.php?id=1")
        assert result == []

    @pytest.mark.asyncio
    async def test_과제_없으면_빈_리스트(self):
        page = AsyncMock()
        page.wait_for_selector = AsyncMock(side_effect=Exception("timeout"))
        result = await _get_assignments(page, "http://lms/course/view.php?id=1")
        assert result == []

    @pytest.mark.asyncio
    async def test_날짜_형식_오류면_통과(self):
        """날짜 파싱 실패 시 ValueError를 삼키고 과제 포함"""
        page = AsyncMock()
        row = self._make_row("날짜이상한과제", "형식이상", "미제출")

        rows_mock = MagicMock()
        rows_mock.count = AsyncMock(return_value=1)
        rows_mock.nth = MagicMock(return_value=row)
        page.locator = MagicMock(return_value=rows_mock)

        result = await _get_assignments(page, "http://lms/course/view.php?id=1")
        assert len(result) == 1


# ════════════════════════════════════════════════════════════════
# 8. get_lms_data (동기 진입점)
# ════════════════════════════════════════════════════════════════
class TestGetLmsData:

    def _mock_crawl_result(self):
        return {
            "user_name": "홍길동",
            "courses": [
                {
                    "name": "운영체제",
                    "materials": [{"title": "1주차", "date": "", "url": "http://a.com"}],
                    "assignments": [
                        {"title": "과제1", "due_date": "2026-06-20 23:00", "submitted": False}
                    ],
                }
            ],
        }

    @patch("app.crawler.lms_crawler.asyncio.run")
    @patch("app.crawler.lms_crawler._get_credentials", return_value=("id", "pw"))
    def test_반환_구조_검증(self, mock_creds, mock_run):
        mock_run.return_value = self._mock_crawl_result()
        result = get_lms_data("id", "pw")

        assert "user_name" in result
        assert "courses" in result
        assert "assignments" in result
        assert "materials" in result

    @patch("app.crawler.lms_crawler.asyncio.run")
    @patch("app.crawler.lms_crawler._get_credentials", return_value=("id", "pw"))
    def test_user_name_전달(self, mock_creds, mock_run):
        mock_run.return_value = self._mock_crawl_result()
        result = get_lms_data("id", "pw")
        assert result["user_name"] == "홍길동"

    @patch("app.crawler.lms_crawler._get_credentials")
    def test_credentials_ValueError_전파(self, mock_creds):
        mock_creds.side_effect = ValueError("자격증명 없음")
        with pytest.raises(ValueError):
            get_lms_data()

    @patch("app.crawler.lms_crawler.asyncio.run")
    @patch("app.crawler.lms_crawler._get_credentials", return_value=("id", "pw"))
    def test_assignments_정렬_포함(self, mock_creds, mock_run):
        data = self._mock_crawl_result()
        data["courses"][0]["assignments"].append(
            {"title": "과제0", "due_date": "2026-06-10 23:00", "submitted": False}
        )
        mock_run.return_value = data
        result = get_lms_data("id", "pw")
        assert result["assignments"][0]["title"] == "과제0"

    @patch("app.crawler.lms_crawler.asyncio.run")
    @patch("app.crawler.lms_crawler._get_credentials", return_value=("id", "pw"))
    def test_materials_통합_포함(self, mock_creds, mock_run):
        mock_run.return_value = self._mock_crawl_result()
        result = get_lms_data("id", "pw")
        assert result["materials"][0]["course_name"] == "운영체제"
