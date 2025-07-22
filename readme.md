# AI Agent Travel Planner

## Giới thiệu
Ứng dụng web hỗ trợ lập kế hoạch du lịch thông minh sử dụng AI Agent. Người dùng nhập thông tin chuyến đi (điểm xuất phát, điểm đến, thời gian, sở thích, ngân sách...), hệ thống sẽ tự động tìm kiếm và đề xuất các lựa chọn chuyến bay, khách sạn, nhà hàng và lên lịch trình cá nhân hóa.

## Tính năng
- Tìm kiếm chuyến bay phù hợp và giá tốt nhất
- Đề xuất khách sạn, nhà hàng theo tiêu chí cá nhân
- Tổng hợp các địa điểm tham quan, hoạt động nổi bật tại điểm đến
- Lên lịch trình chi tiết cho từng ngày của chuyến đi

## Công nghệ sử dụng
- Python
- Streamlit (giao diện web)
- Gemini AI Agent
- SerpApi (tìm kiếm thông tin)

## Hướng dẫn sử dụng

1. **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirement.txt
    ```

2. **Tạo file `.env` và thêm API Key:**
    ```
    SERPAPI_API_KEY=your_serpapi_key
    GOOGLE_API_KEY=your_google_api_key
    ```

3. **Chạy ứng dụng:**
    ```bash
    streamlit run main.py
    ```

4. **Truy cập ứng dụng trên trình duyệt:**  
   Thường là [http://localhost:8501](http://localhost:8501)

## Lưu ý bảo mật
- File `.env` chứa API key đã được thêm vào `.gitignore` để không bị push lên GitHub.

## Đóng góp
Mọi đóng góp, ý kiến hoặc báo lỗi vui lòng tạo issue hoặc pull request trên repository này.

---
```// filepath: /Users/phuoctien/Documents/AgentBookingTravel/README.md
# AI Agent Travel Planner

## Giới thiệu
Ứng dụng web hỗ trợ lập kế hoạch du lịch thông minh sử dụng AI Agent. Người dùng nhập thông tin chuyến đi (điểm xuất phát, điểm đến, thời gian, sở thích, ngân sách...), hệ thống sẽ tự động tìm kiếm và đề xuất các lựa chọn chuyến bay, khách sạn, nhà hàng và lên lịch trình cá nhân hóa.

## Tính năng
- Tìm kiếm chuyến bay phù hợp và giá tốt nhất
- Đề xuất khách sạn, nhà hàng theo tiêu chí cá nhân
- Tổng hợp các địa điểm tham quan, hoạt động nổi bật tại điểm đến
- Lên lịch trình chi tiết cho từng ngày của chuyến đi

## Công nghệ sử dụng
- Python
- Streamlit (giao diện web)
- Gemini AI Agent
- SerpApi (tìm kiếm thông tin)

## Hướng dẫn sử dụng

1. **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install streamlit python-dotenv serpapi agno
    ```

2. **Tạo file `.env` và thêm API Key:**
    ```
    SERPAPI_API_KEY=your_serpapi_key
    GOOGLE_API_KEY=your_google_api_key
    ```

3. **Chạy ứng dụng:**
    ```bash
    streamlit run main.py
    ```

4. **Truy cập ứng dụng trên trình duyệt:**  
   Thường là [http://localhost:8501](http://localhost:8501)

## Lưu ý bảo mật
- File `.env` chứa API key đã được thêm vào `.gitignore` để không bị push lên GitHub.

## Đóng góp
Mọi đóng góp, ý kiến hoặc báo lỗi vui lòng tạo issue hoặc pull request trên