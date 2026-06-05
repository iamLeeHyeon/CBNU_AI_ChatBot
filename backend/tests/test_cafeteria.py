import unittest
from datetime import date
from unittest.mock import patch, MagicMock
from app.services.cafeteria import is_cafeteria_query, get_today_cafeteria_menu


class TestIsCafeteriaQuery(unittest.TestCase):

    def test_학식_키워드_감지(self):
        self.assertTrue(is_cafeteria_query("오늘 학식 뭐야"))

    def test_식단_키워드_감지(self):
        self.assertTrue(is_cafeteria_query("오늘 식단 알려줘"))

    def test_식당명_직접_언급_감지(self):
        self.assertTrue(is_cafeteria_query("한빛식당 메뉴"))
        self.assertTrue(is_cafeteria_query("별빛식당"))
        self.assertTrue(is_cafeteria_query("은하수식당"))

    def test_관련없는_질문은_감지_안함(self):
        self.assertFalse(is_cafeteria_query("도서관 어디야"))
        self.assertFalse(is_cafeteria_query("수강신청 언제야"))
        self.assertFalse(is_cafeteria_query(""))


class TestGetTodayCafeteriaMenu(unittest.TestCase):

    @patch("app.services.cafeteria.requests.get", side_effect=Exception("연결 실패"))
    def test_네트워크_오류(self, _):
        result = get_today_cafeteria_menu()
        self.assertEqual(result, "학식 정보를 불러오는 데 실패했습니다.")

    @patch("app.services.cafeteria.requests.get")
    def test_오늘_날짜_없음(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = "<html><body></body></html>"
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("학식 정보가 없습니다", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_menu_result_없음(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = """<html><body>
            <table><th class="weekday-title">06.05</th></table>
        </body></html>"""
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("찾을 수 없습니다", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_오늘_메뉴_등록_안됨(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = """<html><body>
            <table><th class="weekday-title">06.05</th></table>
            <div id="menu-result"></div>
        </body></html>"""
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("등록되어 있지 않습니다", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_메뉴_정상_파싱(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        html = """<html><body>
        <table>
          <th class="weekday-title">06.05</th>
          <th class="weekday-title">06.06</th>
        </table>
        <table>
          <tr>
            <th class="row-label">한빛식당 점심</th>
            <td id="table-1-2-3-0"></td>
          </tr>
        </table>
        <div id="menu-result">
          <div class="menu" data-table="1-2-3-0">
            <div class="menu-body">
              <h6 class="card-header">된장찌개</h6>
              <ul>
                <li class="side">김치</li>
                <li class="side">밥</li>
              </ul>
              <span class="commas">5,000</span>
            </div>
          </div>
        </div>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = html
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("한빛식당", result)
        self.assertIn("된장찌개", result)
        self.assertIn("김치", result)
        self.assertIn("5,000", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_미운영_메뉴_스킵(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        html = """<html><body>
        <table><th class="weekday-title">06.05</th></table>
        <table>
          <tr>
            <th class="row-label">한빛식당 점심</th>
            <td id="table-1-2-3-0"></td>
          </tr>
        </table>
        <div id="menu-result">
          <div class="menu" data-table="1-2-3-0">
            <div class="menu-body">
              <h6 class="card-header">미운영</h6>
            </div>
          </div>
        </div>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = html
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("등록되어 있지 않습니다", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_다른_요일_메뉴_스킵(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        html = """<html><body>
        <table><th class="weekday-title">06.05</th></table>
        <table>
          <tr>
            <th class="row-label">한빛식당 점심</th>
            <td id="table-1-2-3-0"></td>
          </tr>
        </table>
        <div id="menu-result">
          <div class="menu" data-table="1-2-3-1">
            <div class="menu-body">
              <h6 class="card-header">비빔밥</h6>
            </div>
          </div>
        </div>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = html
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("등록되어 있지 않습니다", result)

    @patch("app.services.cafeteria.requests.get")
    @patch("app.services.cafeteria.date")
    def test_row_label_단어_부족_스킵(self, mock_date_cls, mock_get):
        mock_date_cls.today.return_value = date(2026, 6, 5)
        html = """<html><body>
        <table><th class="weekday-title">06.05</th></table>
        <table>
          <tr>
            <th class="row-label">한빛식당</th>
            <td id="table-1-2-3-0"></td>
          </tr>
        </table>
        <div id="menu-result"></div>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.encoding = "utf-8"
        mock_resp.text = html
        mock_get.return_value = mock_resp
        result = get_today_cafeteria_menu()
        self.assertIn("등록되어 있지 않습니다", result)


if __name__ == "__main__":
    unittest.main()
