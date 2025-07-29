# 🌍 Trợ Lý Du Lịch AI (AI Travel Assistant)

Một ứng dụng Streamlit sử dụng AI để tạo lịch trình du lịch cá nhân hóa cho người dùng, tìm chuyến bay, khách sạn, nhà hàng và gửi lịch trình qua email.

---

## 🚀 Tính năng

- 📍 **Lên kế hoạch du lịch thông minh**: Nhập điểm đến, số ngày, chủ đề chuyến đi và nhận kế hoạch chi tiết.
- ✈️ **Tìm chuyến bay giá rẻ**: Dữ liệu từ Google Flights qua SerpAPI.
- 🏨 **Gợi ý khách sạn và nhà hàng**: AI chọn lọc theo ngân sách và sở thích.
- 🧠 **AI đa tác vụ**: Sử dụng các Agent chuyên biệt để nghiên cứu, lên lịch và tìm địa điểm ăn ở.
- 📧 **Gửi email lịch trình**: Chia sẻ kế hoạch du lịch dễ dàng.

---

## 📦 Cài đặt

### 1. Clone dự án
```bash
git clone https://github.com/UncleTien/AgentTravelAssistant.git
cd AgentTravelAssistant
```

### 2. Tạo môi trường ảo (khuyến nghị)
```bash
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

---

## 🔐 Thiết lập biến môi trường

Tạo file `.env` trong thư mục gốc và thêm các thông tin sau:

```env
SERPAPI_API_KEY=your_serpapi_key
GOOGLE_API_KEY=your_google_genai_key

GMAIL_SENDER_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
```

📌 **Lưu ý:**  
- `SERPAPI_API_KEY`: Lấy từ [SerpAPI](https://serpapi.com/)
- `GOOGLE_API_KEY`: Lấy từ [Google Generative AI](https://makersuite.google.com/app/apikey)
- `GMAIL_APP_PASSWORD`: Lấy từ [Google App Passwords](https://myaccount.google.com/apppasswords)
- `GMAIL_SENDER_EMAIL`: Email của mã GMAIL_APP_PASSWORD

---

## 🏃‍♂️ Chạy ứng dụng

```bash
streamlit run main.py
```

Ứng dụng sẽ mở tại `http://localhost:8501` trên trình duyệt mặc định.

---

## 📁 Cấu trúc thư mục

```
.
├── main.py
├── agents.py
├── config.py
├── utils.py
├── email_utils.py
├── requirements.txt
├── .env
└── README.md
```

---

## 📬 Gửi email kế hoạch

Sau khi tạo xong kế hoạch, người dùng có thể nhập địa chỉ email và nhấn “📤 Gửi Email” để nhận lịch trình kèm khách sạn và nhà hàng qua email.

---

## 💡 Ghi chú

- Mã IATA ví dụ: `SGN` (HCM), `CDG` (Paris), `LHR` (London), `JFK` (New York).
- Dữ liệu chuyến bay dựa trên [Google Flights qua SerpAPI](https://serpapi.com/google-flights-api).
- Ứng dụng sử dụng `agno` để quản lý các agent AI.

---

## 📜 License

MIT © 2025
