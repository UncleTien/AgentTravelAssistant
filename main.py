import streamlit as st
import json
import os
import re
import unicodedata
import pandas as pd
from csv import Sniffer
import time
import traceback
import datetime as _dt

from config import SERPAPI_KEY
from utils import format_datetime, fetch_flights, extract_cheapest_flights
from agents import researcher, planner, hotel_restaurant_finder
from email_utils import send_itinerary_email

from dotenv import load_dotenv
load_dotenv()

# ============= Helpers: plain text (loại Markdown) =============
_md_hdr_re = re.compile(r"^\s{0,3}#{1,6}\s+")
_md_tbl_re = re.compile(r"^\s*\|.*\|\s*$")
_md_code_fence_re = re.compile(r"^\s*```.*$")
_md_format_re = re.compile(r"(\*\*|\*|`|__|_)")

def to_plain_list(text: str) -> str:
    """Bỏ Markdown cơ bản, đổi bullet thành '- ' và loại bảng/code block."""
    if not isinstance(text, str):
        return ""
    lines = []
    skip_code = False
    for raw in text.splitlines():
        line = raw.rstrip()

        # code fence on/off
        if _md_code_fence_re.match(line):
            skip_code = not skip_code
            continue
        if skip_code:
            continue

        # bỏ header, bảng
        if _md_hdr_re.match(line) or _md_tbl_re.match(line):
            continue

        # đổi các bullet markdown -> '- '
        line = re.sub(r"^\s*[-*+]\s+", "- ", line)
        # bỏ số thứ tự '1. ', '2) ' -> '- '
        line = re.sub(r"^\s*\d+[\.\)]\s+", "- ", line)

        # bỏ inline bold/italic/code
        line = _md_format_re.sub("", line)

        # gộp khoảng trắng
        line = " ".join(line.split())

        if line:
            lines.append(line)
    # nếu không có bullet nào, thêm '- ' cho mỗi dòng để luôn có list
    if not any(l.strip().startswith("- ") for l in lines):
        lines = [f"- {l}" for l in lines if l]
    return "\n".join(lines)

# --- Biến URL thành link (HTML hoặc Markdown) ---
_URL_RE = re.compile(r'(https?://[^\s\]\)<>"]+)')

def linkify(text: str, html: bool = True) -> str:
    """Tìm URL và biến thành thẻ <a> (hoặc Markdown) để bấm được."""
    if not isinstance(text, str) or not text.strip():
        return ""
    if html:
        return _URL_RE.sub(r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', text)
    else:
        return _URL_RE.sub(r'[\1](\1)', text)

# ============== Retry cho agent (chống 429) ====================
def safe_agent_run(agent, prompt: str, retries: int = 3, base_wait: float = 4.0, component_name: str = "agent"):
    for i in range(retries):
        try:
            return agent.run(prompt, stream=False)
        except Exception as e:
            msg = str(e)
            is_rate = ("429" in msg) or ("Too Many Requests" in msg)
            wait = base_wait * (2 ** i) if is_rate else base_wait
            st.warning(f"⚠️ {component_name} đang quá tải (thử {i+1}/{retries}). Sẽ thử lại sau {wait:.0f}s.")
            time.sleep(wait)
    st.error(f"❌ {component_name} lỗi liên tục. Dùng nội dung tạm thời để không gián đoạn.")
    class _Resp:
        def __init__(self, content): self.content = content
    fb = f"[FALLBACK - {component_name}] Model đang quá tải hoặc giới hạn lượt gọi. Vui lòng thử lại sau."
    return _Resp(fb)

# ============== Flights fallback helpers =======================
def _fallback_pick_flights(flight_data, limit=6):
    if not isinstance(flight_data, dict):
        return []
    best = flight_data.get("best_flights") or []
    other = flight_data.get("other_flights") or []
    pool = (best + other)[:limit]

    normalized = []
    for f in pool:
        price = f.get("price") or f.get("total_price") or "N/A"
        duration = f.get("total_duration") or f.get("duration") or "N/A"
        flights_info = f.get("flights") or f.get("segments") or []
        airline_logo = f.get("airline_logo") or f.get("logo") or ""
        airline = f.get("airline") or (flights_info[0].get("airline") if flights_info else "Không xác định")
        normalized.append({
            "airline_logo": airline_logo,
            "airline": airline,
            "price": price,
            "total_duration": duration,
            "flights": flights_info,
            "departure_token": f.get("departure_token", ""),
            "link": f.get("link"),
            "booking_options": f.get("booking_options"),
        })
    return normalized

# ============== City/Country (text) -> IATA từ CSV =============
def _normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = " ".join(s.split())
    return s

CITY_ALIASES = {
    "tp hcm": "ho chi minh",
    "tphcm": "ho chi minh",
    "hcm": "ho chi minh",
    "sai gon": "ho chi minh",
    "saigon": "ho chi minh",
    "tp ho chi minh": "ho chi minh",
    "ha noi": "soc son",
    "hn": "soc son",
    "hanoi": "soc son",
}

COUNTRY_TO_ISO2 = {
    "vn": "vn", "viet nam": "vn", "vietnam": "vn",
    "fr": "fr", "france": "fr",
    "us": "us", "usa": "us", "united states": "us", "united states of america": "us",
    "uk": "gb", "gb": "gb", "great britain": "gb", "united kingdom": "gb",
    "jp": "jp", "japan": "jp",
    "kr": "kr", "south korea": "kr", "korea": "kr",
    "de": "de", "germany": "de",
    "it": "it", "italy": "it",
    "es": "es", "spain": "es",
    "au": "au", "australia": "au",
    "ca": "ca", "canada": "ca",
    "cn": "cn", "china": "cn",
    "sg": "sg", "singapore": "sg",
    "th": "th", "thailand": "th",
    "my": "my", "malaysia": "my",
    "id": "id", "indonesia": "id",
    "ph": "ph", "philippines": "ph",
    "tw": "tw", "taiwan": "tw",
    "hk": "hk", "hong kong": "hk",
    "ru": "ru", "russia": "ru",
    "br": "br", "brazil": "br",
    "mx": "mx", "mexico": "mx",
    "ae": "ae", "uae": "ae", "united arab emirates": "ae",
}

@st.cache_data(show_spinner=False)
def load_airports(csv_path: str = "airports.csv") -> pd.DataFrame:
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        sample = f.read(4096)
        try:
            sep = Sniffer().sniff(sample).delimiter
        except Exception:
            sep = ","
    df = pd.read_csv(csv_path, sep=sep, dtype=str, encoding="utf-8", engine="python")

    required = ["code", "name", "country", "city", "state"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Thiếu cột {c} trong CSV (cần: {', '.join(required)})")

    for c in ["code", "name", "country", "city", "state"]:
        df[c] = df[c].fillna("").astype(str).str.strip()

    df = df[df["code"].str.len() == 3].copy()

    df["n_city"]  = df["city"].map(_normalize_text)
    df["n_state"] = df["state"].map(_normalize_text)
    df["n_name"]  = df["name"].map(_normalize_text)
    df["n_ctry"]  = df["country"].map(_normalize_text)

    df["n_city_slim"]  = df["n_city"].str.replace(r"\bcity\b", "", regex=True).str.strip()
    df["n_state_slim"] = df["n_state"].str.replace(r"\bcity\b", "", regex=True).str.strip()

    return df[["code","name","country","city","state","n_city","n_state","n_name","n_ctry","n_city_slim","n_state_slim"]]

def _split_city_country(q: str):
    parts = [p.strip() for p in (q or "").split(",")]
    city_inp = _normalize_text(parts[0] if parts else "")
    ctry_inp = _normalize_text(parts[1] if len(parts) > 1 else "")

    city_inp = CITY_ALIASES.get(city_inp, city_inp)
    if ctry_inp:
        ctry_inp = COUNTRY_TO_ISO2.get(ctry_inp, ctry_inp)
    return city_inp, ctry_inp

def find_iata_options(query: str, airports_df: pd.DataFrame, max_preview: int = 40):
    city_q, ctry_q = _split_city_country(query)
    if not city_q:
        return [], pd.DataFrame()

    cand = airports_df[
        (airports_df["n_city"] == city_q) |
        (airports_df["n_city_slim"] == city_q) |
        (airports_df["n_state"] == city_q) |
        (airports_df["n_state_slim"] == city_q)
    ].copy()

    if cand.empty:
        cand = airports_df[
            airports_df["n_city"].str.contains(city_q, na=False) |
            airports_df["n_city_slim"].str.contains(city_q, na=False) |
            airports_df["n_state"].str.contains(city_q, na=False) |
            airports_df["n_state_slim"].str.contains(city_q, na=False) |
            airports_df["n_name"].str.contains(city_q, na=False)
        ].copy()

    if ctry_q and not cand.empty:
        cand = cand[cand["n_ctry"] == ctry_q]

    options, seen = [], set()
    for _, r in cand.iterrows():
        code = r["code"]
        if code in seen:
            continue
        seen.add(code)
        label_loc = r["city"] or r["state"]
        label = f"{code} — {r['name']} ({label_loc}, {r['country']})"
        options.append((label, code))

    preview = cand.head(max_preview)[["code","name","city","state","country"]]
    return options, preview

# ============================ UI ================================
st.set_page_config(page_title="🌍 Trợ lý du lịch AI", layout="wide")
st.markdown(
    """
    <style>
        .title { text-align:center; font-size:32px; font-weight:600; color:#2c3e50; }
        .subtitle { text-align:center; font-size:18px; color:#7f8c8d; }
        .stSlider > div { background-color:#f4f6f7; padding:10px; border-radius:8px; }
        .simple-card {
            border:1px solid #e1e1e1; border-radius:8px; padding:16px; background:#fff;
            box-shadow:0 2px 8px rgba(44,62,80,0.04); margin-bottom:16px;
        }
        .simple-btn {
            display:inline-block; padding:8px 18px; font-size:15px; font-weight:500;
            color:#fff; background-color:#2980b9; text-decoration:none; border-radius:5px; margin-top:8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="title">Trợ lý du lịch AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Lên kế hoạch chuyến đi mơ ước của bạn với AI. Nhận đề xuất cá nhân hóa về chuyến bay, khách sạn và hoạt động.</p>', unsafe_allow_html=True)

st.markdown("### Bạn muốn đi đâu?")
st.markdown("Nhập **tên thành phố** (VD: “TP.HCM, VN”, “Hà Nội, VN”, “Paris, FR”, “New York, US”). Ứng dụng sẽ tự động chuyển thành mã IATA.")

# Tải dữ liệu sân bay
airports_df = None
try:
    airports_df = load_airports("airports.csv")
    st.caption(f"📦 Đã nạp {len(airports_df):,} sân bay từ airports.csv")
except Exception as e:
    st.error("Không tải được dữ liệu sân bay (airports.csv).")
    st.caption(f"Chi tiết: {e}")

source_city_input = st.text_input("Thành phố khởi hành:", "TP.HCM, VN")
destination_city_input = st.text_input("Điểm đến:", "Paris, FR")

src_options, src_preview = ([], pd.DataFrame())
dst_options, dst_preview = ([], pd.DataFrame())
if airports_df is not None:
    src_options, src_preview = find_iata_options(source_city_input, airports_df)
    dst_options, dst_preview = find_iata_options(destination_city_input, airports_df)

    if not src_options:
        st.warning("⚠️ Không tìm thấy sân bay phù hợp cho nơi khởi hành.")
        with st.expander("Chẩn đoán khởi hành"):
            st.write(src_preview if not src_preview.empty else "Không có bản ghi nào khớp.")
    if not dst_options:
        st.warning("⚠️ Không tìm thấy sân bay phù hợp cho điểm đến.")
        with st.expander("Chẩn đoán điểm đến"):
            st.write(dst_preview if not dst_preview.empty else "Không có bản ghi nào khớp.")

source = destination = None
if src_options:
    source_label = st.selectbox("Chọn sân bay khởi hành:", [o[0] for o in src_options], index=0, key="src_sel")
    source = dict(src_options)[source_label]
if dst_options:
    destination_label = st.selectbox("Chọn sân bay đến:", [o[0] for o in dst_options], index=0, key="dst_sel")
    destination = dict(dst_options)[destination_label]

st.markdown("### Lên kế hoạch chuyến đi")
num_days = st.slider("Thời gian chuyến đi (ngày):", 1, 14, 5)
travel_theme = st.selectbox(
    "Chọn chủ đề chuyến đi:",
    ["Du lịch cặp đôi", "Du lịch gia đình", "Du lịch khám phá", "Du lịch một mình"]
)

st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center; padding:10px; background-color:#f4f6f7; border-radius:8px; margin-top:10px;">
        <h3 style="color:#2980b9;">Chuyến đi {travel_theme} đến {destination_city_input} sắp bắt đầu!</h3>
        <p style="color:#7f8c8d;">Hãy cùng tìm chuyến bay, nơi ở và trải nghiệm tuyệt vời cho hành trình của bạn.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

activity_preferences = st.text_area(
    "Bạn thích hoạt động gì? (ví dụ: nghỉ dưỡng, khám phá di tích lịch sử, vui chơi về đêm, phiêu lưu)",
    "Nghỉ dưỡng, khám phá di tích lịch sử"
)

departure_date = st.date_input("Ngày khởi hành")
return_date = st.date_input("Ngày trở về")

st.sidebar.title("Trợ lý du lịch")
st.sidebar.subheader("Cá nhân hóa chuyến đi")

budget = st.sidebar.number_input("Ngân sách mong muốn (USD):", min_value=100.0, max_value=10000.0, step=50.0, value=1000.0)
flight_class = st.sidebar.radio("Hạng vé máy bay:", ["Phổ thông", "Thương gia", "Hạng nhất"])
hotel_rating = st.sidebar.selectbox("Xếp hạng khách sạn mong muốn:", ["Bất kỳ", "3⭐", "4⭐", "5⭐"])

st.sidebar.subheader("Danh sách cần mang theo")
packing_list = {
    "Quần áo": True,
    "Giày dép thoải mái": True,
    "Kính râm & kem chống nắng": False,
    "Sách hướng dẫn du lịch": False,
    "Thuốc & dụng cụ y tế": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

st.sidebar.subheader("Thông tin cần thiết")
visa_required = st.sidebar.checkbox("Kiểm tra yêu cầu visa")
travel_insurance = st.sidebar.checkbox("Mua bảo hiểm du lịch")
currency_converter = st.sidebar.checkbox("Tỷ giá ngoại tệ")

params = {
    "engine": "google_flights",
    "departure_id": source,
    "arrival_id": destination,
    "outbound_date": str(departure_date),
    "return_date": str(return_date),
    "currency": "INR",  # đổi sang "USD"/"VND" nếu muốn
    "hl": "en",
    "api_key": SERPAPI_KEY
}

st.caption("💡 Mẹo: Có thể nhập “Thành phố, Quốc gia” (VD: 'Ho Chi Minh, VN' / 'Paris, FR').")

btn_disabled = not (source and destination and airports_df is not None)

if st.button("Tạo kế hoạch du lịch", disabled=btn_disabled):
    try:
        if not source or not destination:
            st.error("Vui lòng chọn sân bay khởi hành và đến hợp lệ.")
            st.stop()

        with st.spinner("Đang tìm chuyến bay tốt nhất..."):
            data_main = fetch_flights(source, destination, departure_date, return_date)

            cheapest_flights = []
            try:
                cheapest_flights = extract_cheapest_flights(data_main) or []
            except Exception as e:
                st.warning(f"extract_cheapest_flights lỗi: {e}")

            if not cheapest_flights:
                cheapest_flights = _fallback_pick_flights(data_main)

            if not cheapest_flights:
                try_dates = []
                try:
                    d0 = _dt.date.fromisoformat(str(departure_date))
                    r0 = _dt.date.fromisoformat(str(return_date))
                    try_dates = [
                        (d0, r0),
                        (d0 + _dt.timedelta(days=1), r0 + _dt.timedelta(days=1)),
                        (d0 - _dt.timedelta(days=1), r0 - _dt.timedelta(days=1)),
                    ]
                except Exception:
                    try_dates = []

                for d, r in try_dates[1:]:
                    data_try = fetch_flights(source, destination, d, r)
                    cf = []
                    try:
                        cf = extract_cheapest_flights(data_try) or []
                    except:
                        pass
                    if not cf:
                        cf = _fallback_pick_flights(data_try)
                    if cf:
                        st.info(f"Không thấy kết quả ngày chính xác. Đã dùng khoảng ngày: {d} → {r}.")
                        cheapest_flights = cf
                        break

        if not cheapest_flights:
            st.warning("SerpAPI không trả chuyến bay phù hợp. Hiển thị phản hồi gốc để kiểm tra:")
            if isinstance(data_main, dict):
                st.json({k: data_main.get(k) for k in ["search_metadata", "error", "best_flights", "other_flights"]})

        # ---------- Research: TRẢ VỀ VĂN BẢN THUẦN ----------
        with st.spinner("Đang tìm điểm đến & hoạt động nổi bật..."):
            research_prompt = f"""
Bạn là Travel Researcher.
Điểm đến: {destination_city_input}.
Sở thích: {activity_preferences}. Chủ đề: {travel_theme}. Số ngày: {num_days}.

HÃY TRẢ VỀ VĂN BẢN THUẦN (KHÔNG MARKDOWN, KHÔNG BẢNG, KHÔNG TIÊU ĐỀ).
Chỉ liệt kê theo dạng gạch đầu dòng, ngắn gọn, mỗi mục một dòng.

Bao gồm:
- Tổng quan nhanh: khí hậu theo mùa, lưu ý an toàn, tips di chuyển nội đô.
- Danh sách 8–12 hoạt động phù hợp với "{travel_theme}" trong {num_days} ngày.
- Mỗi hoạt động: tên + mô tả ngắn + khung giờ gợi ý (sáng/chiều/tối) + chi phí ước tính nếu có.
Ngôn ngữ: tiếng Việt.
            """.strip()
            research_results = safe_agent_run(
                researcher, research_prompt, retries=3, base_wait=4.0,
                component_name="Nghiên cứu điểm đến"
            )

        # ---------- Hotels & Restaurants: VĂN BẢN THUẦN ----------
        with st.spinner("Đang tìm khách sạn & nhà hàng..."):
            hotel_restaurant_prompt = f"""
Bạn là Hotel & Restaurant Finder cho {destination_city_input}.
Ngân sách ~{int(budget)} USD. Hạng khách sạn mong muốn: {hotel_rating}.
Sở thích: {activity_preferences}. Hành trình: {num_days} ngày. Chủ đề: {travel_theme}.

HÃY TRẢ VỀ VĂN BẢN THUẦN (KHÔNG MARKDOWN, KHÔNG BẢNG).
Chỉ liệt kê danh sách gạch đầu dòng, mỗi dòng 1 mục đầy đủ thông tin.
Chia phần 1 và phần 2 cho dễ nhìn. 

Phần 1 - Khách sạn (8–12 gợi ý):
- Tên khách sạn | Khu vực gần landmark | Hạng sao | Điểm đánh giá | Giá ước tính/đêm (USD) | Chính sách huỷ | Link đặt phòng (có chưa URL đầy đủ, đưa thẳng đến website, có chưa https://)

Phần 2 - Nhà hàng/quán ăn (10–15 gợi ý, đủ sáng/trưa/tối, nhiều mức giá):
- Tên | Loại ẩm thực | Khu vực | Mức giá/người (USD) | Có đặt bàn không | Link Maps/Website Link đặt phòng (có chưa URL đầy đủ, đưa thẳng đến website, có chưa https://)

Ưu tiên vị trí thuận tiện và chỗ đáng tin cậy. Ngôn ngữ: tiếng Việt.
            """.strip()
            hotel_restaurant_results = safe_agent_run(
                hotel_restaurant_finder, hotel_restaurant_prompt, retries=3, base_wait=4.0,
                component_name="Khách sạn & Nhà hàng"
            )

        with st.spinner("Đang tạo lịch trình cá nhân hóa..."):
            planning_prompt = (
                f"Dựa trên dữ liệu sau, hãy tạo lịch trình {num_days} ngày cho chuyến đi {travel_theme.lower()} đến {destination_city_input}. "
                f"Khách du lịch thích: {activity_preferences}. Ngân sách: khoảng {int(budget)} USD. Hạng vé: {flight_class}. Khách sạn: {hotel_rating}. "
                f"Visa: {visa_required}. Bảo hiểm: {travel_insurance}. Nghiên cứu: {research_results.content}. "
                f"Chuyến bay: {json.dumps(cheapest_flights, ensure_ascii=False)}. Khách sạn & Nhà hàng: {hotel_restaurant_results.content}."
            )
            itinerary = safe_agent_run(
                planner, planning_prompt, retries=3, base_wait=4.0,
                component_name="Lập lịch trình"
            )

        # ========== Render ==========
        st.subheader("Các chuyến bay giá tốt nhất")
        if cheapest_flights:
            cols = st.columns(min(4, len(cheapest_flights)))
            for idx, flight in enumerate(cheapest_flights[:len(cols)]):
                with cols[idx]:
                    airline_logo = flight.get("airline_logo", "")
                    airline_name = flight.get("airline", "Không xác định")
                    price = flight.get("price", "Không có thông tin")
                    total_duration = flight.get("total_duration", "N/A")

                    flights_info = flight.get("flights", [{}])
                    departure = flights_info[0].get("departure_airport", {}) if flights_info else {}
                    arrival = flights_info[-1].get("arrival_airport", {}) if flights_info else {}
                    airline_name = flights_info[0].get("airline", airline_name) if flights_info else airline_name

                    departure_time = format_datetime(departure.get("time", "N/A"))
                    arrival_time = format_datetime(arrival.get("time", "N/A"))

                    # --- Link đặt vé: ưu tiên link trực tiếp nếu có, fallback Google Flights ---
                    booking_link = None
                    try:
                        booking_link = (
                            flight.get("link")
                            or (flight.get("booking_options") or [{}])[0].get("link")
                        )
                    except Exception:
                        booking_link = None

                    if not booking_link:
                        dep = str(departure_date)
                        ret = str(return_date)
                        booking_link = (
                            f"https://www.google.com/travel/flights?"
                            f"q={source}%20to%20{destination}%20{dep}%20{ret}"
                        )

                    if not isinstance(booking_link, str) or not booking_link.startswith(("http://", "https://")):
                        booking_link = "https://www.google.com/travel/flights"

                    st.markdown(
                        f"""
                        <div class="simple-card">
                            {'<img src="'+airline_logo+'" width="80" alt="Logo hãng bay" />' if airline_logo else ''}
                            <h4 style="margin: 8px 0; color:#2c3e50;">{airline_name}</h4>
                            <p><strong>Khởi hành:</strong> {departure_time}</p>
                            <p><strong>Đến nơi:</strong> {arrival_time}</p>
                            <p><strong>Thời gian bay:</strong> {total_duration}</p>
                            <h3 style="color: #2980b9;">{price}</h3>
                            <a href="{booking_link}" target="_blank" class="simple-btn">Đặt vé ngay</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning("Không có dữ liệu chuyến bay.")

        # Hai phần sau hiển thị VĂN BẢN THUẦN đã linkify, dùng Markdown để có link bấm được
        st.subheader("Điểm đến & hoạt động nổi bật ")
        research_plain = to_plain_list(research_results.content)
        st.markdown(linkify(research_plain, html=True).replace("\n", "  \n"), unsafe_allow_html=True)

        st.subheader("Khách sạn & Nhà hàng ")
        hotels_plain = to_plain_list(hotel_restaurant_results.content)
        st.markdown(linkify(hotels_plain, html=True).replace("\n", "  \n"), unsafe_allow_html=True)

        st.subheader("Lịch trình cá nhân hóa của bạn")
        st.write(itinerary.content)

        st.success("Kế hoạch du lịch đã được tạo thành công!")

        st.session_state.itinerary = itinerary.content
        st.session_state.hotel_restaurant_results = hotel_restaurant_results.content

    except Exception:
        st.error("Đã xảy ra lỗi không mong muốn khi tạo kế hoạch.")
        with st.expander("Chi tiết lỗi"):
            st.code("".join(traceback.format_exc()))

# --- Gửi Email ---
if "itinerary" in st.session_state:
    st.markdown("---")
    st.subheader("📧 Gửi lịch trình qua Email")
    with st.form("send_email_form"):
        receiver_email = st.text_input("📨 Email người nhận", value="")
        subject = st.text_input("📝 Tiêu đề Email", value="Lịch trình du lịch AI của bạn")
        st.markdown("**Nội dung Email sẽ bao gồm lịch trình du lịch và thông tin khách sạn & nhà hàng.**")

        itinerary_html = st.session_state.itinerary.replace('\n', '<br>')
        hotel_html_raw = st.session_state.hotel_restaurant_results
        # linkify để URL trong email bấm được
        hotel_html = linkify(to_plain_list(hotel_html_raw), html=True).replace('\n', '<br>')

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h2 {{ color: #2c3e50; }}
                .section {{ margin-bottom: 20px; }}
                a {{ color: #2980b9; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h2>📌 Lịch trình du lịch</h2>
            <div class="section">{itinerary_html}</div>
            <h2>🏨 Khách sạn & Nhà hàng (văn bản thuần)</h2>
            <div class="section">{hotel_html}</div>
        </body>
        </html>
        """

        submitted = st.form_submit_button("📤 Gửi Email")
        if submitted:
            sender_email = os.getenv("GMAIL_SENDER_EMAIL")
            if sender_email and receiver_email:
                success = send_itinerary_email(
                    sender_email=sender_email,
                    receiver_email=receiver_email,
                    subject=subject,
                    body=body
                )
                if success:
                    st.success("✅ Email đã được gửi thành công!")
                else:
                    st.error("❌ Gửi email thất bại. Kiểm tra cấu hình hoặc App Password.")
            else:
                st.warning("⚠️ Thiếu thông tin người gửi hoặc người nhận.")