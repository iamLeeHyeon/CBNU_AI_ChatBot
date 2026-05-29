import re
import requests
from datetime import date
from bs4 import BeautifulSoup, Comment

MENU_URL = "https://www.cbnucoop.com/service/restaurant/"
CAFETERIA_KEYWORDS = ["학식", "식단", "메뉴", "밥", "급식", "한빛식당", "별빛식당", "은하수식당", "오늘 뭐 먹"]

MEAL_ORDER = ["아침", "점심", "저녁"]
RESTAURANT_ORDER = ["한빛식당", "별빛식당", "은하수식당"]


def is_cafeteria_query(text: str) -> bool:
    return any(kw in text for kw in CAFETERIA_KEYWORDS)


def get_today_cafeteria_menu() -> str:
    today = date.today()
    today_str = today.strftime("%m.%d")

    try:
        resp = requests.get(MENU_URL, timeout=10)
        resp.encoding = "utf-8"
    except Exception:
        return "학식 정보를 불러오는 데 실패했습니다."

    # HTML 주석 제거 후 파싱 (주석 안에 예시 데이터가 있어 제거 필요)
    cleaned = re.sub(r"<!--.*?-->", "", resp.text, flags=re.DOTALL)
    soup = BeautifulSoup(cleaned, "html.parser")

    # 1. 오늘 요일 인덱스 찾기 (0=월 ~ 4=금)
    weekday_headers = soup.find_all("th", class_="weekday-title")
    today_day_index = None
    for i, th in enumerate(weekday_headers[:5]):  # 첫 식당 탭 기준 5개
        if today_str in th.get_text():
            today_day_index = i
            break

    if today_day_index is None:
        return f"오늘({today.strftime('%m월 %d일')})은 학식 정보가 없습니다. (주말이거나 방학 기간일 수 있습니다.)"

    # 2. row-label → (식당, 식사) 매핑 빌드
    prefix_to_info: dict[str, tuple[str, str]] = {}
    for label_th in soup.find_all("th", class_="row-label"):
        label_text = label_th.get_text(strip=True)
        parts = label_text.split()
        if len(parts) < 2:
            continue
        restaurant, meal = parts[0], parts[1]

        row = label_th.find_parent("tr")
        if not row:
            continue
        tds = row.find_all("td", id=re.compile(r"^table-"))
        if not tds:
            continue

        first_id = tds[0].get("id", "")  # e.g. "table-18-8-16-0"
        segments = first_id.replace("table-", "").split("-")
        if len(segments) >= 4:
            prefix = "-".join(segments[:-1])  # e.g. "18-8-16"
            prefix_to_info[prefix] = (restaurant, meal)

    # 3. menu-result에서 오늘 메뉴 수집
    menu_result = soup.find(id="menu-result")
    if not menu_result:
        return "학식 메뉴 정보를 찾을 수 없습니다."

    collected: dict[tuple[str, str], list[dict]] = {}

    for menu_div in menu_result.find_all("div", class_="menu"):
        data_table = menu_div.get("data-table", "")
        segments = data_table.split("-")
        if len(segments) < 4:
            continue
        if int(segments[-1]) != today_day_index:
            continue

        prefix = "-".join(segments[:-1])
        info = prefix_to_info.get(prefix)
        if not info:
            continue
        restaurant, meal = info

        for body in menu_div.find_all("div", class_="menu-body"):
            header = body.find("h6", class_="card-header")
            menu_name = header.get_text(strip=True) if header else ""
            if not menu_name or any(kw in menu_name for kw in ["미운영", "휴무", "중단"]):
                continue

            sides = [li.get_text(strip=True) for li in body.find_all("li", class_="side")]
            price_span = body.find("span", class_=re.compile("commas"))
            price = price_span.get_text(strip=True) if price_span else ""

            collected.setdefault((restaurant, meal), []).append({
                "name": menu_name,
                "sides": sides,
                "price": price,
            })

    if not collected:
        return f"오늘({today.strftime('%m월 %d일')}) 학식 메뉴가 등록되어 있지 않습니다."

    # 4. 포맷
    lines = [f"{today.strftime('%Y년 %m월 %d일')} 충북대 학식 메뉴\n"]
    for restaurant in RESTAURANT_ORDER:
        meals_found = [(meal, collected[(restaurant, meal)]) for meal in MEAL_ORDER if (restaurant, meal) in collected]
        if not meals_found:
            continue
        lines.append(f"[{restaurant}]")
        for meal, items in meals_found:
            lines.append(f"  {meal}")
            for item in items:
                lines.append(f"    · {item['name']}")
                if item["sides"]:
                    lines.append(f"      반찬: {', '.join(item['sides'])}")
                if item["price"]:
                    lines.append(f"      가격: {item['price']}원")
        lines.append("")

    return "\n".join(lines).strip()
