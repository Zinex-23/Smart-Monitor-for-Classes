# 🖥️ UI Information — Smart Monitor Class

## 1. Tổng quan giao diện

Ứng dụng có **một trang duy nhất** (Single Page Application) phục vụ tại `http://localhost:5000/`.  
Tên: **"Smart Monitor Class"**  
Ngôn ngữ UI: Tiếng Việt

---

## 2. Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    HEADER                                   │
│         🧠 Smart Monitor Class                               │
│         [⏰ Cập nhật lần cuối: ...]                          │
├──────────────────────────────────────────────────────────────┤
│              STATS GRID (4 stat-cards)                       │
│  [Tổng HS] [Độ vui vẻ TB] [Độ tự tin TB] [Độ lo lắng TB]  │
├──────────────────────────────────────────────────────────────┤
│            DASHBOARD GRID (3 columns)                        │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  📊 Bar Chart  │  │ 😊 Positive  │  │  📹 Camera Feed  │ │
│  │  Performance   │  │  Score (%)   │  │  (MJPEG Stream)  │ │
│  │  Distribution  │  │              │  │  [Bật/Tắt Ảnh]  │ │
│  └────────────────┘  └──────────────┘  └──────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                   SECTION DIVIDER                            │
├──────────────────────────────────────────────────────────────┤
│              REPORT SECTION                                  │
│  📝 Textarea (emotion data input)                            │
│  ☑️ Checkbox: Sử dụng AI                                     │
│  [Tạo Báo Cáo] [Xuất Báo Cáo]                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  🟢 Main Report Display (gradient green-blue)        │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│           STUDENTS EMOTION TABLE                             │
│  Tên | Angry | Disgust | Fear | Happy | Sad | Surprise |... │
│  [Dữ liệu học sinh - auto loaded by JS]                      │
├──────────────────────────────────────────────────────────────┤
│  [⟳ Làm mới] (Fixed bottom-right button)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Color Palette

| Yếu tố | Màu sắc |
|---|---|
| **Background (body)** | Linear gradient: `#667eea → #764ba2` (tím xanh) |
| **Cards** | `white` với shadow `rgba(0,0,0,0.1)` |
| **Primary button** | Gradient: `#667eea → #764ba2` |
| **Success button** | Gradient: `#28a745 → #20c997` |
| **Report display** | Gradient: `#17ef79 → #0984e3` (xanh lá → xanh dương) |
| **Angry emotion** | `#f39c12` (cam) |
| **Disgust emotion** | `#3498db` (xanh dương) |
| **Fear emotion** | `#e74c3c` (đỏ) |
| **Happy emotion** | `#e67e22` (cam đậm) |
| **Sad emotion** | `#95a5a6` (xám) |
| **Surprise emotion** | `#27ae60` (xanh lá) |
| **Neutral emotion** | `#8e44ad` (tím) |

---

## 4. Components chi tiết

### 4.1 Stats Grid (4 cards)

| Card | ID Element | Tính toán |
|---|---|---|
| Tổng số học sinh | `#totalStudents` | `studentsData.length` |
| Độ vui vẻ trung bình | `#avgHappiness` | `avg(happy.score) × 100%` |
| Độ tự tin trung bình | `#avgConfidence` | `avg(surprise.score) × 100%` |
| Độ lo lắng trung bình | `#avgFear` | `avg(fear.score) × 100%` |

> 📌 **Lưu ý**: "Độ tự tin" được tính từ `surprise.score` — đây có thể là limitation của mapping

### 4.2 Performance Bar Chart

- **Library**: Chart.js 3.9.1
- **Type**: `bar`
- **Canvas ID**: `performanceChart`
- **Labels**: `['Rất thấp', 'Thấp', 'Trung bình', 'Cao', 'Rất cao']`
- **Colors**: `[#e74c3c, #f39c12, #f1c40f, #2ecc71, #27ae60]`
- **Refresh**: Destroy & re-create mỗi 30 giây

### 4.3 Positive Score Indicator

- **Element**: `#positiveScore`
- **Formula**:  
  `totalPositive = Σ max(0, (happy + surprise - angry - disgust - fear - sad) / 2)`  
  `score = round(totalPositive / numStudents × 100)%`

### 4.4 Camera Feed

- **Source**: `/video_feed` (MJPEG multipart stream)
- **Container**: 300×100% với `object-fit: cover`
- **Status indicator**: Dot xanh/đỏ với animation `pulse` (2s cycle)
- **Controls**:
  - `toggleCamera()` — Bật/Tắt hiển thị stream
  - `captureImage()` — Gửi POST `/capture_image` (⚠️ endpoint chưa implement)

### 4.5 Students Emotion Table

- **Columns**: Tên | Angry | Disgust | Fear | Happy | Sad | Surprise | Neutral
- **Refresh**: Mỗi 30 giây qua `/api/emotions`
- **Cell format**: `{score}% / {duration}min`
- **Row hover**: Background `#f8f9fa`
- **Responsive**: `overflow-x: auto` trên mobile

### 4.6 Report Section

| Element | Mô tả |
|---|---|
| Textarea `#input_text` | Hiển thị emotion data dạng text, auto-update 5s |
| Checkbox `#use_ai` | Toggle AI report generation |
| Submit button | POST form → Flask server |
| Export button | `generateReport()` → fetch POST → extract report HTML |
| `#mainReport` div | Hiển thị báo cáo từ `StudentEmotionAnalyzer` |

---

## 5. Auto-refresh Logic

```javascript
// Input text (emotion data string) — mỗi 5 giây
setInterval(fetchInputText, 5000);  // GET /get_input_text

// Full data reload — mỗi 30 giây  
setInterval(loadData, 30000);       // GET /api/emotions
```

---

## 6. Responsive Breakpoints

| Breakpoint | Layout |
|---|---|
| > 1024px | Dashboard: 3 columns |
| 768px – 1024px | Dashboard: 2 columns |
| < 768px | Dashboard: 1 column, buttons stacked vertically |

---

## 7. Font & Icons

| Tài nguyên | CDN |
|---|---|
| **Font** | `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif` (system font) |
| **Icons** | Font Awesome 6.0.0 (`cdnjs.cloudflare.com`) |
| **Charts** | Chart.js 3.9.1 (`cdnjs.cloudflare.com`) |

---

## 8. Micro-animations

| Animation | Áp dụng cho | Duration |
|---|---|---|
| `translateY(-5px)` | Card hover | 0.3s ease |
| `translateY(-3px)` | Button hover | 0.3s ease |
| `pulse` (opacity) | Camera status indicator | 2s infinite |
| `spin` (rotate 360°) | Loading spinner | 1s linear infinite |
| `translateY(-2px)` | Refresh & camera buttons | 0.3s ease |

---

## 9. Screenshot Reference

> Ứng dụng chạy tại: `http://localhost:5000`  
> Backend cần khởi động với: `python app.py` (sau khi cài đủ dependencies)

**Màn hình chính** có gradient tím-xanh nổi bật, các card trắng với shadow, và live camera feed ở góc phải.
