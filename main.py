import streamlit as st
import json
from config import SERPAPI_KEY
from utils import format_datetime, fetch_flights, extract_cheapest_flights
from agents import researcher, planner, hotel_restaurant_finder
from email_utils import send_itinerary_email
import os

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="🌍 Trợ lý du lịch AI", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 32px;
            font-weight: 600;
            color: #2c3e50;
        }
        .subtitle {
            text-align: center;
            font-size: 18px;
            color: #7f8c8d;
        }
        .stSlider > div {
            background-color: #f4f6f7;
            padding: 10px;
            border-radius: 8px;
        }
        .simple-card {
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 16px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(44,62,80,0.04);
            margin-bottom: 16px;
        }
        .simple-btn {
            display: inline-block;
            padding: 8px 18px;
            font-size: 15px;
            font-weight: 500;
            color: #fff;
            background-color: #2980b9;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="title">Trợ lý du lịch AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Lên kế hoạch chuyến đi mơ ước của bạn với AI. Nhận đề xuất cá nhân hóa về chuyến bay, khách sạn và hoạt động.</p>', unsafe_allow_html=True)

st.markdown("### Bạn muốn đi đâu?")
st.markdown('Chọn điểm đến của bạn và nhập thông tin chuyến bay, Nhập mã IATA của thành phố khởi hành và điểm đến')
st.markdown('SGN: TP.HCM, HAN: Hà Nội, DAD: Đà Nẵng, CDG: Paris, LHR: London, JFK: New York, HND: Tokyo,...')
st.markdown('Bạn có thể truy cập [IATA Codes](https://www.iata.org/en/publications/directories/code-search/) để tìm mã IATA của sân bay.')
source = st.text_input("Thành phố khởi hành (Mã IATA):", "SGN")
destination = st.text_input("Điểm đến (Mã IATA):", "CDG") #Paris

st.markdown("### Lên kế hoạch chuyến đi")
num_days = st.slider("Thời gian chuyến đi (ngày):", 1, 14, 5)
travel_theme = st.selectbox(
    "Chọn chủ đề chuyến đi:",
    ["Du lịch cặp đôi", "Du lịch gia đình", "Du lịch khám phá", "Du lịch một mình"]
)

st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 10px; 
        background-color: #f4f6f7; 
        border-radius: 8px; 
        margin-top: 10px;
    ">
        <h3 style="color:#2980b9;">Chuyến đi {travel_theme} đến {destination} sắp bắt đầu!</h3>
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

budget = st.sidebar.radio("Ngân sách:", ["Tiết kiệm", "Tiêu chuẩn", "Cao cấp"])
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
    "currency": "INR",
    "hl": "en",
    "api_key": SERPAPI_KEY
}

if st.button("Tạo kế hoạch du lịch"):
    with st.spinner("Đang tìm chuyến bay tốt nhất..."):
        flight_data = fetch_flights(source, destination, departure_date, return_date)
        cheapest_flights = extract_cheapest_flights(flight_data)

    with st.spinner("Đang tìm điểm đến & hoạt động nổi bật..."):
        research_prompt = (
            f"Tìm các điểm đến và hoạt động nổi bật ở {destination} cho chuyến đi {travel_theme.lower()} {num_days} ngày. "
            f"Khách du lịch thích: {activity_preferences}. Ngân sách: {budget}. Hạng vé: {flight_class}. "
            f"Khách sạn: {hotel_rating}. Visa: {visa_required}. Bảo hiểm: {travel_insurance}."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("Đang tìm khách sạn & nhà hàng..."):
        hotel_restaurant_prompt = (
            f"Tìm khách sạn và nhà hàng tốt nhất gần các điểm tham quan ở {destination} cho chuyến đi {travel_theme.lower()}. "
            f"Ngân sách: {budget}. Khách sạn: {hotel_rating}. Hoạt động yêu thích: {activity_preferences}."
        )
        hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)

    with st.spinner("Đang tạo lịch trình cá nhân hóa..."):
        planning_prompt = (
            f"Dựa trên dữ liệu sau, hãy tạo lịch trình {num_days} ngày cho chuyến đi {travel_theme.lower()} đến {destination}. "
            f"Khách du lịch thích: {activity_preferences}. Ngân sách: {budget}. Hạng vé: {flight_class}. Khách sạn: {hotel_rating}. "
            f"Visa: {visa_required}. Bảo hiểm: {travel_insurance}. Nghiên cứu: {research_results.content}. "
            f"Chuyến bay: {json.dumps(cheapest_flights)}. Khách sạn & Nhà hàng: {hotel_restaurant_results.content}."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    st.subheader("Các chuyến bay giá tốt nhất")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_logo = flight.get("airline_logo", "")
                airline_name = flight.get("airline", "Không xác định")
                price = flight.get("price", "Không có thông tin")
                total_duration = flight.get("total_duration", "N/A")
                
                flights_info = flight.get("flights", [{}])
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})
                airline_name = flights_info[0].get("airline", "Không xác định") 
                
                departure_time = format_datetime(departure.get("time", "N/A"))
                arrival_time = format_datetime(arrival.get("time", "N/A"))
                
                departure_token = flight.get("departure_token", "")

                booking_link = "#"
                if departure_token:
                    params_with_token = {
                        **params,
                        "departure_token": departure_token
                    }
                    search_with_token = fetch_flights(source, destination, departure_date, return_date)
                    try:
                        booking_options = search_with_token['best_flights'][idx]['booking_token']
                        booking_link = f"https://www.google.com/travel/flights?tfs={booking_options}"
                    except Exception:
                        booking_link = "#"

                st.markdown(
                    f"""
                    <div class="simple-card">
                        <img src="{airline_logo}" width="80" alt="Logo hãng bay" />
                        <h4 style="margin: 8px 0; color:#2c3e50;">{airline_name}</h4>
                        <p><strong>Khởi hành:</strong> {departure_time}</p>
                        <p><strong>Đến nơi:</strong> {arrival_time}</p>
                        <p><strong>Thời gian bay:</strong> {total_duration} phút</p>
                        <h3 style="color: #2980b9;">{price}</h3>
                        <a href="{booking_link}" target="_blank" class="simple-btn">Đặt vé ngay</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("Không có dữ liệu chuyến bay.")

    st.subheader("Khách sạn & Nhà hàng")
    st.write(hotel_restaurant_results.content)

    st.subheader("Lịch trình cá nhân hóa của bạn")
    st.write(itinerary.content)

    st.success("Kế hoạch du lịch đã được tạo thành công!")


    # Lưu session_state để gửi email
    st.session_state.itinerary = itinerary.content
    st.session_state.hotel_restaurant_results = hotel_restaurant_results.content

# --- Form gửi Email (luôn hiển thị nếu đã có lịch trình) ---
if "itinerary" in st.session_state:
    st.markdown("---")
    st.subheader("📧 Gửi lịch trình qua Email")

    with st.form("send_email_form"):
        receiver_email = st.text_input("📨 Email người nhận", value="")
        subject = st.text_input("📝 Tiêu đề Email", value="Lịch trình du lịch AI của bạn")
        st.markdown("**Nội dung Email sẽ bao gồm lịch trình du lịch và thông tin khách sạn & nhà hàng.**")

        itinerary_html = st.session_state.itinerary.replace('\n', '<br>')
        hotel_html = st.session_state.hotel_restaurant_results.replace('\n', '<br>')

        body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                }}
                h2 {{
                    color: #2c3e50;
                }}
                .section {{
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <h2>📌 Lịch trình du lịch</h2>
            <div class="section">{itinerary_html}</div>

            <h2>🏨 Khách sạn & Nhà hàng</h2>
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
