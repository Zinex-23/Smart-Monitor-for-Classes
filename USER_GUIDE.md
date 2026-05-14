# Hướng Dẫn Sử Dụng - Smart Monitor for Classes

## 1. Giới Thiệu
Hệ thống giám sát lớp học thông minh sử dụng AI để nhận diện khuôn mặt và phân tích cảm xúc học sinh trong thời gian thực. Hệ thống hỗ trợ giáo viên theo dõi mức độ tập trung và trạng thái tâm lý của lớp học để đưa ra các điều chỉnh giảng dạy phù hợp.

## 2. Cài Đặt & Triển Khai (Localhost)
Để cài đặt và chạy hệ thống trên máy tính cá nhân, vui lòng tham khảo hướng dẫn chi tiết (copy-paste) tại:
👉 **[Hướng dẫn chạy nhanh (RUN_GUIDE.txt)](RUN_GUIDE.txt)**

**Các bước cơ bản:**
1. Mở Terminal hoặc Command Prompt tại thư mục dự án.
2. Copy lệnh tương ứng trong `RUN_GUIDE.txt` và dán vào terminal.
3. Sau khi cài đặt xong, ứng dụng sẽ chạy tại: `http://localhost:5000`

## 3. Các Tính Năng Chính

### 3.1. Đăng Nhập
Hệ thống cung cấp các tài khoản mặc định:
*   **Tài khoản Giáo viên**: ID: `1` / Pass: `1` (Dùng cho dữ liệu thực tế)
*   **Tài khoản Test**: ID: `0` / Pass: `0` (Dùng cho dữ liệu mô phỏng)

### 3.2. Giám Sát Thời Gian Thực (Real-time Monitoring)
*   Cho phép chuyển đổi giữa **Camera trực tiếp** và **Video file**.
*   Tự động nhận diện khuôn mặt và phân tích cảm xúc: *Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral*.

### 3.3. Báo Cáo AI (AI Pedagogical Reports)
*   Hệ thống tự động tổng hợp dữ liệu cảm xúc của cả lớp.
*   Tích hợp AI (Gemini/Groq) để phân tích và đưa ra các đề xuất sư phạm giúp giáo viên cải thiện chất lượng tiết dạy.

### 3.4. Quản Lý Lịch Sử
*   Xem lại kết quả phân tích của các tiết học trong quá khứ.
*   Lọc dữ liệu theo ngày và tiết học.

### 3.5. Cấu Hình Hệ Thống
*   Tùy chỉnh thời gian tiết học, số lượng tiết trong ngày.
*   Cấu hình nguồn dữ liệu (Camera/Simulation).

## 4. Yêu Cầu Hệ Thống
*   **Python**: Phiên bản 3.8 trở lên.
*   **Thư viện**: Xem chi tiết tại `requirements.txt`.
*   **Camera**: Webcam hoặc camera tích hợp (nếu dùng chế độ giám sát trực tiếp).

---
© 2024 Smart Monitor for Classes - Phát triển bởi Zinex.
