# ⚙️ Technical Documentation — Smart Monitor Class

## 1. Tổng quan kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                      │
│  - Dashboard UI (Chart.js)                                   │
│  - Camera stream display                                     │
│  - Emotion table / Stats cards                               │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP / REST API
┌────────────────────────▼─────────────────────────────────────┐
│                    Flask Web Server (app.py)                  │
│                         Port: 5000                           │
│                                                              │
│  Routes:                                                     │
│  GET  /              → Dashboard (index.html)                │
│  GET  /video_feed    → MJPEG stream                          │
│  GET  /api/emotions  → JSON emotion data                     │
│  GET  /get_input_text → Current model output text            │
│  POST /api/update    → Update model output                   │
│                                                              │
│  Background Threads:                                         │
│  - Camera capture + AI inference (generate_frames)           │
│  - JSON sync thread (update_data_continuously, 5s interval)  │
└──────────┬──────────────┬────────────────────────────────────┘
           │              │
    ┌──────▼──────┐  ┌────▼────────────────────┐
    │  OpenCV     │  │  AI Models (PyTorch)     │
    │  Camera I/O │  │  - MTCNN (face detect)   │
    │  (cv2)      │  │  - FaceNet (recognition) │
    └─────────────┘  │  - ResNet50 (emotion)    │
                     └─────────────────────────┘
                               │
                     ┌─────────▼──────────┐
                     │  emotion_per_person │
                     │  .json (data store) │
                     └────────────────────┘
```

## 2. Stack công nghệ

| Lớp | Công nghệ | Phiên bản/Ghi chú |
|---|---|---|
| **Backend Framework** | Flask (Python) | Lightweight web server |
| **Computer Vision** | OpenCV (`cv2`) | Camera capture, BGR→RGB conversion |
| **Deep Learning** | PyTorch (`torch`) | GPU/CPU inference |
| **Face Detection** | MTCNN (`facenet_pytorch`) | Multi-task CNN |
| **Face Recognition** | InceptionResnetV1 (`facenet_pytorch`) | Pretrained on VGGFace2 |
| **Emotion Classification** | ResNet-50 (`torchvision`) | Fine-tuned on FER2013 |
| **Image Processing** | Pillow (PIL) | RGB frame conversion |
| **AI Report** | HuggingFace LLM (`emotion_analyzer`) | Tạo báo cáo tự nhiên |
| **Frontend** | HTML5 + Vanilla JS + CSS3 | Không framework |
| **Charting** | Chart.js 3.9.1 | Bar chart phân bố hiệu suất |
| **Data Storage** | JSON file (`emotion_per_person.json`) | Không database |

## 3. Luồng xử lý chính (Pipeline)

### 3.1 Real-time Inference Pipeline

```
Camera Frame (BGR)
    │
    ▼
cv2.cvtColor → RGB Frame
    │
    ▼
PIL.Image ──→ MTCNN.detect()
               ├─ boxes (bounding boxes)
               └─ MTCNN.extract() → face tensors (160×160×3)
                       │
            ┌──────────┴──────────────┐
            │                         │
    Face Recognition              Emotion Detection
    InceptionResnetV1              ResNet-50 (grayscale)
    embedding → cosine dist        face_crop → 48×48 gray
    → compare vs known_embeddings  → normalize [-1,1]
    → threshold: 0.9               → softmax → 7 classes
    → name assignment              → label + confidence
            │                         │
            └──────────┬──────────────┘
                       │
              Update person_emotion_stats
              (score_sum, duration, count)
                       │
              Save to emotion_per_person.json (every 10s)
```

### 3.2 Data Flow (Backend ↔ Frontend)

```
[Background Thread] every 5s:
    read emotion_per_person.json
    → update current_model_output
    → if changed: trigger AI report generation

[Frontend] every 30s:
    GET /api/emotions
    → studentsData[]
    → updateStats()
    → renderStudentsTable()
    → initializeChart()

[Frontend] every 5s:
    GET /get_input_text
    → update textarea
```

## 4. Cấu trúc file dự án

```
Emotions-Detection-main/
├── app.py                    # Flask server + AI inference
├── emotion_analyzer.py       # [MISSING] HF LLM report generator
├── emotion_per_person.json   # Data store (auto-generated)
├── new_face_db.pth           # Known face embeddings database
├── templates/
│   └── index.html            # Single-page dashboard (1043 lines)
├── static/
│   └── style.css             # Supplementary table styles
├── Final_project_Group5.pdf  # Project report
└── doc/                      # Documentation (this folder)
```

## 5. API Endpoints chi tiết

| Method | Endpoint | Request | Response |
|---|---|---|---|
| GET | `/` | — | HTML Dashboard |
| POST | `/` | `input_text`, `use_ai` | HTML với báo cáo |
| GET | `/video_feed` | — | `multipart/x-mixed-replace` MJPEG |
| GET | `/api/emotions` | — | `{data, last_update, total_students}` |
| GET | `/get_input_text` | — | `{input_text: string}` |
| POST | `/api/update` | `{output_model_1}` | `{status, message}` |

## 6. Thread Safety & Concurrency

- **`camera_lock`** (threading.Lock): Bảo vệ truy cập camera giữa `init_camera()` và `generate_frames()`
- **`data_lock`** (threading.Lock): Bảo vệ `current_model_output`, `cached_report`, `cached_parsed_data`
- **Background thread** (`update_data_continuously`): Đọc JSON mỗi 5 giây, daemon thread
- **MJPEG stream**: Generator function `generate_frames()` chạy trong thread riêng của Flask

## 7. Hạn chế kỹ thuật hiện tại

| Hạn chế | Mô tả |
|---|---|
| **Missing module** | `emotion_analyzer.py` không có trong repo — import sẽ fail |
| **Hardcoded model path** | Windows-style path `r"Model\Final_Model\..."` sẽ lỗi trên Linux |
| **No database** | Dữ liệu chỉ lưu JSON file — không có persistence thực sự |
| **Single camera** | Chỉ hỗ trợ 1 camera (ID=0) |
| **Global state** | `cap = cv2.VideoCapture(0)` tại line 183 bị tạo 2 lần (duplicate) |
| **No auth** | Không có xác thực — bất kỳ ai trên mạng cũng truy cập được |
