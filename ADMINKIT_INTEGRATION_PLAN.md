# Kế Hoạch Áp Dụng AdminKit Cho Dự Án Smart Monitor Class

## 1. Mục tiêu

Tài liệu này mô tả cách áp dụng giao diện **AdminKit** vào dự án **Smart Monitor Class**.

Mục tiêu chính là **nâng cấp giao diện dashboard hiện tại** để trông chuyên nghiệp, rõ ràng và dễ sử dụng hơn, nhưng **không thay đổi kiến trúc backend hiện có**.

Dự án hiện tại đã có đầy đủ các thành phần chính:

- Dashboard hiển thị trên trình duyệt web
- Flask backend chạy tại `localhost:5000`
- Camera livestream qua endpoint `/video_feed`
- Dữ liệu cảm xúc qua endpoint `/api/emotions`
- Text dữ liệu báo cáo qua endpoint `/get_input_text`
- Khu vực tạo báo cáo lớp học
- Bảng thống kê cảm xúc từng học sinh
- Chart.js để hiển thị biểu đồ

AdminKit chỉ được sử dụng để thay đổi **giao diện frontend**, bao gồm:

- Layout tổng thể
- Sidebar
- Top navbar
- Card thống kê
- Card biểu đồ
- Card camera
- Card báo cáo
- Bảng dữ liệu học sinh
- Responsive layout

Backend Flask hiện tại sẽ được giữ nguyên nếu không có yêu cầu bắt buộc.

---

## 2. Nguyên tắc tích hợp

Khi áp dụng AdminKit vào dự án, cần tuân thủ các nguyên tắc sau:

### 2.1. Không thay đổi backend nếu không cần thiết

Không tự ý thay đổi các route backend hiện có:

```text
GET  /
GET  /video_feed
GET  /api/emotions
GET  /get_input_text
POST /
POST /api/update
```

Các endpoint này vẫn sẽ được frontend mới gọi lại như cũ.

---

### 2.2. Không chuyển sang React, Vue hoặc Next.js

Dự án hiện tại sử dụng:

```text
Flask + HTML + CSS + Vanilla JavaScript + Chart.js
```

Vì vậy khi dùng AdminKit, chỉ dùng bản HTML/CSS/JS của AdminKit.

Không chuyển frontend sang:

```text
React
Vue
Next.js
Angular
```

---

### 2.3. Giữ nguyên các ID DOM quan trọng

Các phần JavaScript hiện tại đang cập nhật dữ liệu dựa trên ID của các element trong HTML.

Vì vậy khi thay giao diện, bắt buộc giữ lại các ID sau:

```text
totalStudents
avgHappiness
avgConfidence
avgFear
performanceChart
positiveScore
videoFeed
input_text
use_ai
mainReport
studentsTableBody
```

Nếu đổi các ID này, JavaScript hiện tại có thể bị lỗi hoặc không cập nhật dữ liệu được.

---

### 2.4. Chỉ dùng AdminKit như bộ giao diện

Không copy toàn bộ demo của AdminKit vào project.

Chỉ lấy các phần cần thiết:

```text
Layout
Sidebar
Navbar
Card
Table
Button
Form
Grid system
Responsive style
CSS/JS build sẵn
```

Không cần lấy các phần không dùng tới:

```text
Login page
Register page
Calendar demo
Map demo
Profile demo
Notification demo
Demo chart data
Demo dashboard data
```

---

## 3. Cấu trúc thư mục đề xuất

Sau khi tích hợp AdminKit, cấu trúc project nên được tổ chức như sau:

```text
Emotions-Detection-main/
├── app.py
├── emotion_per_person.json
├── new_face_db.pth
├── templates/
│   ├── index.html
│   └── index_old.html
├── static/
│   ├── adminkit/
│   │   ├── css/
│   │   │   └── app.css
│   │   ├── js/
│   │   │   └── app.js
│   │   └── img/
│   ├── css/
│   │   └── smart-monitor.css
│   └── js/
│       └── dashboard.js
└── README.md
```

Ý nghĩa từng phần:

| Đường dẫn | Vai trò |
|---|---|
| `templates/index.html` | Giao diện mới dùng AdminKit |
| `templates/index_old.html` | Backup giao diện cũ |
| `static/adminkit/css/app.css` | CSS chính của AdminKit |
| `static/adminkit/js/app.js` | JavaScript chính của AdminKit |
| `static/adminkit/img/` | Ảnh/icon asset của AdminKit nếu cần |
| `static/css/smart-monitor.css` | CSS custom riêng cho Smart Monitor Class |
| `static/js/dashboard.js` | JavaScript xử lý fetch API, chart, table, camera |

---

## 4. Cách import AdminKit vào Flask template

Trong file `templates/index.html`, import AdminKit như sau:

```html
<link href="{{ url_for('static', filename='adminkit/css/app.css') }}" rel="stylesheet">
<link href="{{ url_for('static', filename='css/smart-monitor.css') }}" rel="stylesheet">
```

Ở cuối file HTML, trước thẻ đóng `</body>`:

```html
<script src="{{ url_for('static', filename='adminkit/js/app.js') }}"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
```

Lưu ý:

- `app.css` của AdminKit được load trước.
- `smart-monitor.css` được load sau để override màu sắc riêng của project.
- `dashboard.js` được load sau cùng để đảm bảo DOM đã sẵn sàng.

---

## 5. Layout tổng thể sau khi áp dụng AdminKit

Dashboard mới sẽ dùng bố cục AdminKit như sau:

```text
┌──────────────────────────────────────────────────────────────┐
│ Sidebar │ Top Navbar                                         │
│         ├────────────────────────────────────────────────────┤
│         │ Main Dashboard Content                             │
│         │                                                    │
│         │ Stat Cards                                         │
│         │ Chart + Camera + Positive Score                    │
│         │ Report Section                                     │
│         │ Student Emotion Table                              │
└─────────┴────────────────────────────────────────────────────┘
```

Giao diện bao gồm các khu vực chính:

1. Sidebar
2. Top Navbar
3. Overview Statistics
4. Learning Performance Chart
5. Positive Emotion Score
6. Camera Monitor
7. Class Report Generator
8. Student Emotion Detail Table

---

# 6. Chi tiết từng phần của Dashboard

## 6.1. Sidebar

Sidebar là thanh điều hướng bên trái của dashboard.

Sidebar không cần quá nhiều menu. Dự án hiện tại chỉ có một trang dashboard chính, nên sidebar chỉ dùng để chia khu vực nội dung.

### Menu đề xuất

```text
Smart Monitor Class
├── Tổng quan
├── Camera giám sát
├── Báo cáo lớp học
└── Cảm xúc học sinh
```

### Nội dung sidebar

| Menu | Ý nghĩa |
|---|---|
| Tổng quan | Điều hướng đến phần thống kê tổng quan |
| Camera giám sát | Điều hướng đến khu vực camera livestream |
| Báo cáo lớp học | Điều hướng đến khu vực tạo báo cáo |
| Cảm xúc học sinh | Điều hướng đến bảng cảm xúc từng học sinh |

### Ghi chú triển khai

Vì hiện tại project chỉ là single-page application, các menu này có thể dùng anchor link:

```html
<a href="#overview">Tổng quan</a>
<a href="#camera-section">Camera giám sát</a>
<a href="#report-section">Báo cáo lớp học</a>
<a href="#students-section">Cảm xúc học sinh</a>
```

Không cần tạo route mới trong Flask.

---

## 6.2. Top Navbar

Top Navbar nằm ở phía trên phần nội dung chính.

### Thông tin cần hiển thị

Top Navbar chỉ cần hiển thị các thông tin đang có trong project:

```text
Smart Monitor Class
Cập nhật lần cuối
Trạng thái hệ thống
```

### Cấu trúc đề xuất

```text
[Smart Monitor Class]                         [Cập nhật lần cuối: ...] [Online/Offline]
```

### Dữ liệu sử dụng

| Thành phần | Nguồn dữ liệu |
|---|---|
| Tên hệ thống | Text tĩnh: `Smart Monitor Class` |
| Cập nhật lần cuối | Lấy từ response của `/api/emotions` |
| Trạng thái hệ thống | Dựa trên việc fetch `/api/emotions` thành công hay thất bại |

### Ghi chú

Không cần hiển thị thông tin user, avatar, notification hoặc setting phức tạp vì project hiện tại chưa có đăng nhập.

---

## 6.3. Overview Statistics

Đây là khu vực 4 card thống kê đầu trang.

### Mục đích

Giúp giáo viên nhìn nhanh tình trạng chung của lớp học.

### Các card cần có

```text
1. Tổng số học sinh
2. Độ vui vẻ trung bình
3. Độ tự tin trung bình
4. Độ lo lắng trung bình
```

### Chi tiết từng card

| Card | ID DOM | Nội dung hiển thị |
|---|---|---|
| Tổng số học sinh | `totalStudents` | Tổng số học sinh có trong dữ liệu |
| Độ vui vẻ trung bình | `avgHappiness` | Trung bình điểm cảm xúc Happy |
| Độ tự tin trung bình | `avgConfidence` | Trung bình điểm Surprise theo logic hiện tại |
| Độ lo lắng trung bình | `avgFear` | Trung bình điểm Fear |

### Layout AdminKit đề xuất

Mỗi chỉ số là một AdminKit card:

```text
┌────────────────────┐
│ Tổng số học sinh   │
│ 0                  │
│ Đang được theo dõi │
└────────────────────┘
```

### HTML mẫu

```html
<div class="col-sm-6 col-xl-3">
  <div class="card">
    <div class="card-body">
      <h5 class="card-title mb-4">Tổng số học sinh</h5>
      <h1 class="mt-1 mb-3" id="totalStudents">0</h1>
      <div class="mb-1">
        <span class="text-muted">Đang được theo dõi</span>
      </div>
    </div>
  </div>
</div>
```

### Ghi chú

Không thêm các chỉ số chưa có dữ liệu thực tế.

Không thêm:

```text
Tỷ lệ chuyên cần
Điểm trung bình học tập
Số lớp học
Số giáo viên
Số cảnh báo hôm nay
```

trừ khi backend đã có dữ liệu tương ứng.

---

## 6.4. Learning Performance Chart

Đây là card hiển thị biểu đồ phân bố hiệu suất học tập.

### Mục đích

Biểu đồ giúp giáo viên xem tổng quan phân bố trạng thái lớp học theo các mức hiệu suất.

### Thông tin hiển thị

Biểu đồ gồm 5 nhóm:

```text
Rất thấp
Thấp
Trung bình
Cao
Rất cao
```

### ID DOM bắt buộc

```html
<canvas id="performanceChart"></canvas>
```

### Nguồn dữ liệu

Dữ liệu lấy từ endpoint:

```text
GET /api/emotions
```

Frontend sẽ xử lý dữ liệu cảm xúc để tính performance score theo logic hiện tại.

### Layout đề xuất

Card nên nằm bên trái hoặc chiếm khoảng 6 cột trên desktop:

```text
┌────────────────────────────────────┐
│ Phân Bố Hiệu Suất Học Tập           │
│                                    │
│ [Chart.js Bar Chart]               │
└────────────────────────────────────┘
```

### HTML mẫu

```html
<div class="col-12 col-lg-6">
  <div class="card">
    <div class="card-header">
      <h5 class="card-title mb-0">Phân Bố Hiệu Suất Học Tập</h5>
    </div>
    <div class="card-body">
      <canvas id="performanceChart"></canvas>
    </div>
  </div>
</div>
```

### Ghi chú

Không dùng demo chart data của AdminKit.

Không đổi `id="performanceChart"`.

Không tạo thêm biểu đồ mới nếu backend chưa có dữ liệu.

---

## 6.5. Positive Emotion Score

Đây là card hiển thị chỉ số cảm xúc tích cực chung của lớp.

### Mục đích

Cho giáo viên biết nhanh mức độ tích cực tổng thể của lớp học.

### ID DOM bắt buộc

```html
<div id="positiveScore">0%</div>
```

### Thông tin hiển thị

```text
Chỉ Số Cảm Xúc Tích Cực
0%
Tích cực chung của lớp
```

### Nguồn dữ liệu

Dữ liệu lấy từ `/api/emotions`.

Frontend tính toán dựa trên các cảm xúc:

```text
Positive: Happy, Surprise
Negative: Angry, Disgust, Fear, Sad
```

### Layout đề xuất

```text
┌────────────────────────────────────┐
│ Chỉ Số Cảm Xúc Tích Cực             │
│                                    │
│                0%                  │
│        Tích cực chung của lớp       │
└────────────────────────────────────┘
```

### HTML mẫu

```html
<div class="col-12 col-lg-3">
  <div class="card h-100">
    <div class="card-header">
      <h5 class="card-title mb-0">Chỉ Số Cảm Xúc Tích Cực</h5>
    </div>
    <div class="card-body d-flex flex-column align-items-center justify-content-center">
      <div id="positiveScore" class="display-4 fw-bold text-success">0%</div>
      <p class="text-muted mt-2 mb-0">Tích cực chung của lớp</p>
    </div>
  </div>
</div>
```

### Ghi chú

Có thể hiển thị dạng số lớn hoặc progress bar.

Không thêm nhận xét tự động nếu chưa có logic phân tích tương ứng.

---

## 6.6. Camera Monitor

Đây là card hiển thị camera giám sát lớp học.

### Mục đích

Hiển thị livestream từ webcam/camera đang xử lý nhận diện khuôn mặt và cảm xúc.

### Endpoint sử dụng

```text
GET /video_feed
```

### ID DOM bắt buộc

```html
<img id="videoFeed" src="/video_feed">
```

### Nội dung card

```text
Camera Giám Sát
Livestream camera
Trạng thái Online/Offline
Nút Bật/Tắt Camera
Nút Chụp Ảnh
```

### Layout đề xuất

```text
┌────────────────────────────────────┐
│ Camera Giám Sát                    │
│                                    │
│ [MJPEG Camera Feed]                │
│                                    │
│ [Bật/Tắt Camera] [Chụp Ảnh]        │
└────────────────────────────────────┘
```

### HTML mẫu

```html
<div class="col-12 col-lg-3" id="camera-section">
  <div class="card h-100">
    <div class="card-header">
      <h5 class="card-title mb-0">Camera Giám Sát</h5>
    </div>
    <div class="card-body">
      <div class="camera-wrapper">
        <img id="videoFeed" src="/video_feed" class="img-fluid rounded" alt="Camera Feed">
      </div>

      <div class="d-flex gap-2 mt-3">
        <button type="button" class="btn btn-primary" onclick="toggleCamera()">
          Bật/Tắt Camera
        </button>

        <button type="button" class="btn btn-success" onclick="captureImage()">
          Chụp Ảnh
        </button>
      </div>
    </div>
  </div>
</div>
```

### Ghi chú quan trọng

Nếu endpoint chụp ảnh `/capture_image` chưa được implement, không nên làm nút này quá nổi bật.

Có thể giữ nút `Chụp Ảnh`, nhưng cần xử lý lỗi nhẹ nhàng nếu backend chưa hỗ trợ.

Ví dụ:

```text
Chức năng chụp ảnh chưa khả dụng.
```

---

## 6.7. Class Report Generator

Đây là khu vực tạo báo cáo lớp học.

### Mục đích

Cho phép giáo viên tạo báo cáo từ dữ liệu cảm xúc hiện tại.

### Thành phần cần có

```text
Textarea nhập dữ liệu báo cáo
Checkbox sử dụng AI
Nút Tạo Báo Cáo
Nút Xuất Báo Cáo
Khu vực hiển thị báo cáo
```

### ID DOM bắt buộc

```text
input_text
use_ai
mainReport
```

### Layout đề xuất

Khu vực báo cáo nên nằm trong một card lớn:

```text
┌──────────────────────────────────────────────┐
│ Tạo Báo Cáo Lớp Học                          │
│                                              │
│ Nhập dữ liệu báo cáo                         │
│ [Textarea]                                   │
│                                              │
│ [ ] Sử dụng AI để tối ưu hóa báo cáo          │
│                                              │
│ [Tạo Báo Cáo] [Xuất Báo Cáo]                 │
│                                              │
│ Báo Cáo Tình Hình Chung Của Lớp              │
│ [Nội dung báo cáo]                           │
└──────────────────────────────────────────────┘
```

### HTML mẫu

```html
<div class="card" id="report-section">
  <div class="card-header">
    <h5 class="card-title mb-0">Tạo Báo Cáo Lớp Học</h5>
  </div>

  <div class="card-body">
    <form method="POST" action="/">
      <div class="mb-3">
        <label for="input_text" class="form-label">Nhập dữ liệu báo cáo</label>
        <textarea
          class="form-control"
          id="input_text"
          name="input_text"
          rows="5"
          placeholder="Nhập thông tin về tình hình lớp học..."
        ></textarea>
      </div>

      <div class="form-check mb-3">
        <input class="form-check-input" type="checkbox" id="use_ai" name="use_ai">
        <label class="form-check-label" for="use_ai">
          Sử dụng AI để tối ưu hóa báo cáo
        </label>
      </div>

      <div class="d-flex gap-2 mb-4">
        <button type="submit" class="btn btn-primary">
          Tạo Báo Cáo
        </button>

        <button type="button" class="btn btn-success" onclick="generateReport()">
          Xuất Báo Cáo
        </button>
      </div>
    </form>

    <div class="report-result">
      <h5>Báo Cáo Tình Hình Chung Của Lớp</h5>
      <div id="mainReport" class="p-3 rounded bg-light">
        Chưa có báo cáo. Vui lòng nhập dữ liệu và tạo báo cáo.
      </div>
    </div>
  </div>
</div>
```

### Ghi chú

Không thêm các trường dữ liệu mới như:

```text
Tên giáo viên
Tên môn học
Mã lớp
Thời lượng tiết học
Điểm danh
Kết quả kiểm tra
```

nếu backend hiện tại chưa xử lý các thông tin đó.

---

## 6.8. Student Emotion Detail Table

Đây là bảng hiển thị chi tiết cảm xúc từng học sinh.

### Mục đích

Cho giáo viên xem dữ liệu cảm xúc của từng học sinh theo từng nhãn cảm xúc.

### Nguồn dữ liệu

Dữ liệu lấy từ endpoint:

```text
GET /api/emotions
```

### ID DOM bắt buộc

```html
<tbody id="studentsTableBody"></tbody>
```

### Các cột cần có

```text
Tên Học Sinh
Tức Giận
Ghê Tởm
Sợ Hãi
Vui Vẻ
Buồn Bã
Ngạc Nhiên
Bình Thường
```

### Tương ứng với 7 nhãn cảm xúc

```text
Angry
Disgust
Fear
Happy
Sad
Surprise
Neutral
```

### Layout đề xuất

```text
┌────────────────────────────────────────────────────────────┐
│ Chi Tiết Cảm Xúc Từng Học Sinh                              │
│                                                            │
│ Tên | Angry | Disgust | Fear | Happy | Sad | Surprise |... │
└────────────────────────────────────────────────────────────┘
```

### HTML mẫu

```html
<div class="card" id="students-section">
  <div class="card-header">
    <h5 class="card-title mb-0">Chi Tiết Cảm Xúc Từng Học Sinh</h5>
  </div>

  <div class="card-body">
    <div class="table-responsive">
      <table class="table table-hover table-striped">
        <thead>
          <tr>
            <th>Tên Học Sinh</th>
            <th>Tức Giận</th>
            <th>Ghê Tởm</th>
            <th>Sợ Hãi</th>
            <th>Vui Vẻ</th>
            <th>Buồn Bã</th>
            <th>Ngạc Nhiên</th>
            <th>Bình Thường</th>
          </tr>
        </thead>
        <tbody id="studentsTableBody">
        </tbody>
      </table>
    </div>
  </div>
</div>
```

### Format dữ liệu trong ô

Mỗi ô cảm xúc nên hiển thị:

```text
score% / duration min
```

Ví dụ:

```text
82% / 3.4min
```

### Ghi chú

Không thêm các cột chưa có dữ liệu như:

```text
Điểm học tập
Mức độ tập trung
Số lần phát biểu
Cảnh báo kỷ luật
Trạng thái điểm danh
```

---

# 7. JavaScript cần giữ lại

Frontend mới vẫn cần các chức năng JavaScript hiện tại.

Các chức năng chính gồm:

```text
loadData()
updateStats()
initializeChart()
renderStudentsTable()
fetchInputText()
toggleCamera()
captureImage()
generateReport()
```

## 7.1. Load dữ liệu cảm xúc

Dữ liệu cảm xúc tiếp tục lấy từ:

```javascript
fetch('/api/emotions')
```

Sau khi lấy dữ liệu, frontend cập nhật:

```text
4 stat cards
positive score
performance chart
students emotion table
last update
```

---

## 7.2. Load input text cho báo cáo

Textarea báo cáo tiếp tục lấy dữ liệu từ:

```javascript
fetch('/get_input_text')
```

ID textarea cần giữ:

```text
input_text
```

---

## 7.3. Auto refresh

Giữ logic refresh hiện tại:

```text
Input text: mỗi 5 giây
Full data dashboard: mỗi 30 giây
```

Không cần thêm websocket nếu backend hiện tại chưa có.

---

# 8. CSS custom cho Smart Monitor Class

AdminKit cung cấp style chính, nhưng project vẫn cần một file CSS riêng để giữ nhận diện Smart Monitor Class.

File đề xuất:

```text
static/css/smart-monitor.css
```

## 8.1. Màu nhận diện chính

Có thể giữ màu tím/xanh hiện tại của project:

```css
:root {
  --smc-primary: #667eea;
  --smc-secondary: #764ba2;
  --smc-success: #28a745;
  --smc-info: #0984e3;
}
```

## 8.2. Header hoặc nhấn mạnh thương hiệu

```css
.smc-brand-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
}
```

## 8.3. Camera wrapper

```css
.camera-wrapper {
  width: 100%;
  min-height: 260px;
  background: #000;
  border-radius: 0.5rem;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

## 8.4. Report result

```css
.report-result {
  border-radius: 0.5rem;
}

#mainReport {
  min-height: 120px;
}
```

## 8.5. Emotion badges

Nếu muốn hiển thị badge cho từng cảm xúc, dùng các class sau:

```css
.emotion-angry {
  color: #f39c12;
}

.emotion-disgust {
  color: #3498db;
}

.emotion-fear {
  color: #e74c3c;
}

.emotion-happy {
  color: #e67e22;
}

.emotion-sad {
  color: #95a5a6;
}

.emotion-surprise {
  color: #27ae60;
}

.emotion-neutral {
  color: #8e44ad;
}
```

---

# 9. Các bước thực hiện tích hợp

## Bước 1: Backup giao diện cũ

Đổi tên file hiện tại:

```text
templates/index.html
```

thành:

```text
templates/index_old.html
```

Sau đó tạo file mới:

```text
templates/index.html
```

---

## Bước 2: Copy asset AdminKit

Từ folder AdminKit, lấy các file build sẵn:

```text
dist/css/app.css
dist/js/app.js
dist/img/
```

Copy vào project:

```text
static/adminkit/css/app.css
static/adminkit/js/app.js
static/adminkit/img/
```

---

## Bước 3: Tạo file CSS custom

Tạo file:

```text
static/css/smart-monitor.css
```

File này dùng để chứa màu sắc và style riêng của Smart Monitor Class.

---

## Bước 4: Tạo file JS dashboard riêng

Tạo file:

```text
static/js/dashboard.js
```

Chuyển logic JavaScript hiện tại từ `index.html` sang file này nếu có thể.

Nếu chưa muốn tách ngay, có thể giữ script trong `index.html`, nhưng về lâu dài nên tách riêng để dễ bảo trì.

---

## Bước 5: Dựng layout AdminKit

Dựng layout gồm:

```text
wrapper
sidebar
main
navbar
content
container-fluid
row
col
card
```

Không cần đưa toàn bộ demo page của AdminKit vào.

---

## Bước 6: Gắn lại các ID DOM

Sau khi dựng UI, kiểm tra lại chắc chắn các ID sau vẫn tồn tại:

```text
totalStudents
avgHappiness
avgConfidence
avgFear
performanceChart
positiveScore
videoFeed
input_text
use_ai
mainReport
studentsTableBody
```

---

## Bước 7: Test từng phần

Test lần lượt:

```text
1. Trang / có load giao diện không
2. CSS AdminKit có chạy không
3. Sidebar có hiển thị không
4. Stat cards có cập nhật không
5. Chart có hiển thị không
6. Camera /video_feed có hiển thị không
7. Textarea có nhận dữ liệu từ /get_input_text không
8. Nút Tạo Báo Cáo có hoạt động không
9. Nút Xuất Báo Cáo có hoạt động không
10. Bảng học sinh có render dữ liệu không
```

---

# 10. Checklist sau khi tích hợp

## 10.1. Checklist giao diện

```text
[ ] Sidebar hiển thị đúng
[ ] Top navbar hiển thị đúng
[ ] 4 stat cards hiển thị đúng
[ ] Biểu đồ performance hiển thị đúng
[ ] Positive score hiển thị đúng
[ ] Camera card hiển thị đúng
[ ] Report section hiển thị đúng
[ ] Student emotion table hiển thị đúng
[ ] Giao diện responsive trên màn hình nhỏ
```

---

## 10.2. Checklist chức năng

```text
[ ] GET / hoạt động
[ ] GET /api/emotions hoạt động
[ ] GET /video_feed hoạt động
[ ] GET /get_input_text hoạt động
[ ] POST / tạo báo cáo hoạt động
[ ] Dữ liệu tự refresh mỗi 30 giây
[ ] Textarea tự cập nhật mỗi 5 giây
[ ] Chart không bị render trùng nhiều lần
[ ] Không lỗi JavaScript trong Console
```

---

## 10.3. Checklist kỹ thuật

```text
[ ] Không đổi endpoint backend
[ ] Không đổi ID DOM quan trọng
[ ] Không dùng demo data của AdminKit
[ ] Không import thừa quá nhiều CSS/JS
[ ] Không chuyển sang framework frontend khác
[ ] Custom CSS được đặt sau AdminKit CSS
[ ] Dashboard JS được load sau AdminKit JS
```

---

# 11. Những lỗi thường gặp

## 11.1. CSS không load

Nguyên nhân thường là sai đường dẫn.

Sai:

```html
<link href="css/app.css" rel="stylesheet">
```

Đúng trong Flask:

```html
<link href="{{ url_for('static', filename='adminkit/css/app.css') }}" rel="stylesheet">
```

---

## 11.2. Dữ liệu không cập nhật

Nguyên nhân thường là bị đổi ID DOM.

Cần kiểm tra các ID:

```text
totalStudents
avgHappiness
avgConfidence
avgFear
positiveScore
studentsTableBody
```

---

## 11.3. Chart không hiển thị

Kiểm tra:

```text
Canvas có id="performanceChart" chưa
Chart.js đã được import chưa
Dữ liệu /api/emotions có trả về không
Console có lỗi JavaScript không
```

---

## 11.4. Camera không hiển thị

Kiểm tra:

```text
Backend Flask có chạy không
Endpoint /video_feed có hoạt động không
Camera có bị chiếm bởi app khác không
Thẻ img có src="/video_feed" không
```

---

## 11.5. Giao diện bị lệch

Nguyên nhân có thể do CSS cũ xung đột với AdminKit.

Cách xử lý:

```text
Giữ AdminKit CSS làm nền chính
Chỉ giữ lại các CSS custom cần thiết
Xóa các CSS layout cũ nếu đè lên .wrapper, .main, .card, .row, .container
```

---

# 12. Prompt dùng cho AI trong IDE

Có thể dùng prompt sau để yêu cầu AI tích hợp AdminKit:

```text
Hãy đọc project Flask Smart Monitor Class hiện tại và folder AdminKit tôi đã tải về.

Nhiệm vụ:
Tích hợp giao diện AdminKit vào frontend hiện tại của project.

Yêu cầu bắt buộc:
1. Không chuyển sang React, Vue, Next.js hoặc framework frontend khác.
2. Không thay đổi backend Flask nếu không bắt buộc.
3. Không thay đổi các endpoint hiện tại:
   - /
   - /video_feed
   - /api/emotions
   - /get_input_text
   - /api/update
4. Giữ nguyên các ID DOM:
   - totalStudents
   - avgHappiness
   - avgConfidence
   - avgFear
   - performanceChart
   - positiveScore
   - videoFeed
   - input_text
   - use_ai
   - mainReport
   - studentsTableBody
5. Chỉ dùng AdminKit để tạo layout dashboard gồm:
   - Sidebar
   - Top navbar
   - 4 stat cards
   - Performance chart card
   - Positive emotion score card
   - Camera monitor card
   - Report generator card
   - Student emotion table card
6. Không dùng demo data của AdminKit.
7. Giữ logic fetch dữ liệu hiện tại từ:
   - /api/emotions
   - /get_input_text
8. Đặt CSS AdminKit vào:
   - static/adminkit/css/app.css
9. Đặt JS AdminKit vào:
   - static/adminkit/js/app.js
10. Tạo CSS custom riêng tại:
   - static/css/smart-monitor.css
11. Tạo JS dashboard riêng tại:
   - static/js/dashboard.js
12. Giữ màu nhận diện tím/xanh của Smart Monitor Class ở một số phần như brand, button hoặc header.
13. Sau khi làm xong, kiểm tra để đảm bảo chart, camera, report và bảng cảm xúc vẫn hoạt động.
```

---

# 13. Kết luận

AdminKit được dùng để nâng cấp giao diện dashboard của Smart Monitor Class.

Việc tích hợp chỉ tập trung vào frontend:

```text
HTML
CSS
JavaScript
Layout
Card
Table
Navbar
Sidebar
```

Không cần thay đổi lớn ở backend.

Cần giữ nguyên:

```text
Flask routes
API endpoints
DOM IDs
JavaScript logic xử lý dữ liệu
Camera stream
Chart.js
Report form
Emotion table
```

Cách làm an toàn nhất là dùng AdminKit làm khung giao diện, sau đó gắn lại các thành phần hiện có của Smart Monitor Class vào từng card tương ứng.