# 📌 Project Problem — Smart Monitor Class

## 1. Bối cảnh & Động lực

Trong môi trường giảng dạy truyền thống, giáo viên phải tự quan sát và đánh giá cảm xúc/trạng thái tâm lý của từng học sinh — đây là nhiệm vụ **khó khăn, tốn thời gian và dễ bỏ sót** khi lớp học đông người. Giáo viên thường không có khả năng theo dõi đồng thời nhiều học sinh và nhận biết sớm những dấu hiệu tiêu cực như lo lắng, chán nản hay mất tập trung.

## 2. Vấn đề cụ thể

| Vấn đề | Mô tả |
|---|---|
| **Thiếu dữ liệu khách quan** | Giáo viên chỉ có thể đánh giá bằng cảm tính, không có dữ liệu định lượng về cảm xúc học sinh |
| **Không phân biệt được từng cá nhân** | Trong lớp đông, việc theo dõi từng học sinh theo tên gần như không thể |
| **Phản ứng chậm** | Giáo viên chỉ nhận ra trạng thái học sinh sau khi có hành vi biểu hiện rõ ràng, không có cảnh báo sớm |
| **Không có báo cáo tổng hợp** | Không có công cụ tổng hợp dữ liệu cảm xúc theo thời gian cho từng học sinh |

## 3. Phát biểu bài toán

> **"Làm thế nào để tự động nhận diện, theo dõi và báo cáo trạng thái cảm xúc của từng học sinh trong lớp học theo thời gian thực, sử dụng camera giám sát mà không cần sự can thiệp thủ công của giáo viên?"**

## 4. Yêu cầu hệ thống

### Yêu cầu chức năng
- ✅ Nhận diện khuôn mặt học sinh qua camera → **gán tên** từng người
- ✅ Phân loại cảm xúc theo thời gian thực với **7 nhãn**: Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral
- ✅ Tích lũy thống kê cảm xúc theo **thời gian và điểm số** cho mỗi cá nhân
- ✅ Hiển thị dashboard trực quan qua **web browser**
- ✅ Tạo **báo cáo tự động** (có thể kết hợp AI) về tình hình lớp học

### Yêu cầu phi chức năng
- ⚡ Xử lý real-time (camera live-stream)
- 🔒 Không cần phần cứng đặc biệt — chạy trên laptop/PC thông thường
- 🌐 Giao diện web đơn giản, không cần cài đặt ứng dụng

## 5. Đối tượng sử dụng

| Người dùng | Mục đích |
|---|---|
| **Giáo viên** | Quan sát cảm xúc lớp học, nhận báo cáo định kỳ |
| **Nhà quản lý giáo dục** | Đánh giá chất lượng lớp học theo dữ liệu |
| **Nghiên cứu giáo dục** | Thu thập dữ liệu cảm xúc cho phân tích học thuật |

## 6. Giới hạn phạm vi dự án (Scope)

- ✅ Hỗ trợ camera USB/webcam thông thường
- ✅ Nhận diện danh sách học sinh đã biết trước (closed-set face recognition)
- ❌ Không hỗ trợ nhận diện người hoàn toàn xa lạ (open-set)
- ❌ Không hỗ trợ nhiều phòng học cùng lúc (multi-room)
- ❌ Không có tích hợp LMS (Learning Management System)
