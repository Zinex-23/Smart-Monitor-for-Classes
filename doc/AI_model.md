# 🤖 AI Model Documentation — Smart Monitor Class

## 1. Tổng quan các Model AI sử dụng

Hệ thống sử dụng **3 mô hình AI** theo pipeline tuần tự:

```
Camera Frame → [Model 1: MTCNN] → [Model 2: FaceNet] → [Model 3: ResNet-50]
              (Face Detection)   (Face Recognition)   (Emotion Classification)
```

---

## 2. Model 1 — MTCNN (Multi-task Cascaded CNN)

### Mục đích
Phát hiện và cắt khuôn mặt từ frame video.

### Thông số kỹ thuật

| Thuộc tính | Giá trị |
|---|---|
| **Thư viện** | `facenet_pytorch.MTCNN` |
| **Chế độ** | `keep_all=True` (nhận diện nhiều khuôn mặt cùng lúc) |
| **Output** | Bounding boxes + face tensors (160×160×3, RGB) |
| **Device** | CUDA (nếu có GPU) hoặc CPU |
| **Kiến trúc** | 3-stage cascaded CNN (P-Net → R-Net → O-Net) |

### Hoạt động
```python
boxes, _ = mtcnn.detect(img)          # Detect bounding boxes
faces = mtcnn.extract(img, boxes, ...)  # Extract & resize faces to 160×160
```

---

## 3. Model 2 — InceptionResnetV1 (FaceNet)

### Mục đích
Tạo embedding vector đặc trưng khuôn mặt → So sánh với database để nhận diện danh tính.

### Thông số kỹ thuật

| Thuộc tính | Giá trị |
|---|---|
| **Thư viện** | `facenet_pytorch.InceptionResnetV1` |
| **Pretrained** | VGGFace2 (1.4M ảnh, 9,131 người) |
| **Output** | Embedding vector 512 chiều |
| **Threshold** | Khoảng cách Euclidean < **0.9** → cùng người |
| **Chế độ** | `.eval()` — inference only |
| **Device** | CUDA hoặc CPU |

### Face Database
```python
known_embeddings, known_names = torch.load("new_face_db.pth", map_location=device)
# File: new_face_db.pth (865,322 bytes)
# Chứa: list embedding vectors + list tên tương ứng
```

### Logic nhận diện
```python
for db_emb, db_name in zip(known_embeddings, known_names):
    dist = (emb - db_emb).norm().item()    # Euclidean distance
    if dist < min_dist and dist < 0.9:     # Threshold: 0.9
        name = db_name
# Nếu không tìm thấy → name = "Unknown"
```

---

## 4. Model 3 — ResNet-50 (Emotion Classifier)

### Mục đích
Phân loại cảm xúc khuôn mặt thành 7 nhóm.

### Thông số kỹ thuật

| Thuộc tính | Giá trị |
|---|---|
| **Base architecture** | ResNet-50 (`torchvision.models.resnet50`) |
| **Pretrained base** | ImageNet1K V1 |
| **Input channel** | **1 (grayscale)** — conv1 được thay thế |
| **Input size** | 48×48 pixels (grayscale) |
| **Normalization** | `(pixel - 127.5) / 127.5` → range [-1, 1] |
| **Output classes** | **7** (FER2013 labels) |
| **Checkpoint** | `4_Model_checkpoint.pth` |

### Kiến trúc classifier head (thay thế fc gốc)
```python
emotion_model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
emotion_model.fc = nn.Sequential(
    nn.Linear(2048, 256),   # num_ftrs = 2048 (ResNet-50)
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, 7)       # 7 emotion classes
)
```

### Nhãn đầu ra (FER2013 Labels)

| Index | Label | Tiếng Việt | Color Code |
|---|---|---|---|
| 0 | Angry | Tức giận | `#f39c12` |
| 1 | Disgust | Ghê tởm | `#3498db` |
| 2 | Fear | Sợ hãi | `#e74c3c` |
| 3 | Happy | Vui vẻ | `#e67e22` |
| 4 | Sad | Buồn bã | `#95a5a6` |
| 5 | Surprise | Ngạc nhiên | `#27ae60` |
| 6 | Neutral | Bình thường | `#8e44ad` |

### Preprocessing
```python
face_gray = cv2.resize(face_crop, (48, 48), interpolation=cv2.INTER_AREA)
face_tensor = torch.from_numpy(face_gray).unsqueeze(0).unsqueeze(0).float()
face_tensor = (face_tensor - 127.5) / 127.5   # Normalize to [-1, 1]
```

---

## 5. Model 4 — LLM Report Generator (StudentEmotionAnalyzer)

### Mục đích
Tạo báo cáo ngôn ngữ tự nhiên từ dữ liệu cảm xúc thu thập được.

### Thông số kỹ thuật

| Thuộc tính | Giá trị |
|---|---|
| **Module** | `emotion_analyzer.StudentEmotionAnalyzer` |
| **API** | HuggingFace Inference API |
| **Token** | HF_TOKEN (Bearer Authentication) |
| **Input** | `emotion_per_person.json` |
| **Output** | Báo cáo văn bản về tình hình lớp học |
| **Trigger** | Khi phát hiện dữ liệu cảm xúc thay đổi |

> ⚠️ **Lưu ý**: File `emotion_analyzer.py` hiện **không có trong repository**. Đây là dependency bị thiếu.

---

## 6. Thống kê cảm xúc theo thời gian

### Cấu trúc dữ liệu tích lũy
```python
person_emotion_stats = defaultdict(lambda: {
    emotion: {
        "score_sum": 0.0,   # Tổng (confidence × delta_time)
        "duration": 0.0,    # Tổng thời gian xuất hiện (giây)
        "count": 0          # Số lần detect
    } for emotion in FER2013_LABELS
})
```

### Công thức tính điểm trung bình
```python
avg_score = score_sum / duration    # weighted average by time
```

### Lưu JSON (mỗi 10 giây)
```json
[
  {
    "name": "Nguyen Van A",
    "emotions": {
      "Happy": {"score": 0.82, "duration": 45.3},
      "Neutral": {"score": 0.65, "duration": 12.1},
      ...
    }
  }
]
```

---

## 7. Performance Index (Frontend)

### Tính hiệu suất học tập từ cảm xúc
```javascript
// Positive emotions: Happy, Surprise
const positive = happy.score + surprise.score;
// Negative emotions: Angry, Disgust, Fear, Sad
const negative = angry.score + disgust.score + fear.score + sad.score;
// Performance score (normalized)
const performance = (positive - negative) / 2;
```

### Phân loại mức hiệu suất

| Ngưỡng | Mức độ |
|---|---|
| performance < -0.5 | Rất thấp |
| -0.5 ≤ p < -0.1 | Thấp |
| -0.1 ≤ p < 0.3 | Trung bình |
| 0.3 ≤ p < 0.7 | Cao |
| p ≥ 0.7 | Rất cao |
