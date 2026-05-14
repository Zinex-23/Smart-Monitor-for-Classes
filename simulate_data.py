import json
import random
import os

# Configuration
NUM_STUDENTS = 20
OUTPUT_FILE = "emotion_per_person.json"
EMOTIONS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

STUDENT_NAMES = [
    "Nguyễn Văn An", "Trần Thị Bình", "Lê Hoàng Cường", "Phạm Minh Đức", 
    "Vũ Hải Yến", "Đặng Quốc Khánh", "Bùi Mai Chi", "Đỗ Hữu Nghĩa",
    "Ngô Thanh Tùng", "Hoàng Kim Ngân", "Lý Gia Bảo", "Phan Anh Thư",
    "Trịnh Minh Triết", "Lương Thu Thảo", "Võ Văn Hùng", "Diệp Bảo Ngọc",
    "Đào Quang Huy", "Hà Trúc Linh", "Tạ Minh Tâm", "Quách Gia Huy"
]

def generate_simulated_data():
    simulated_data = []
    
    # We want to distribute students across 5 performance levels
    # Levels: Excellent, Good, Average, Low, Very Low
    # 4 students per level to make it perfectly even
    
    for i, name in enumerate(STUDENT_NAMES):
        level = i // 4 # 0, 1, 2, 3, 4
        
        emotions_stats = {}
        total_duration = random.uniform(30.0, 45.0)
        
        # Base weights for classroom (mostly neutral)
        weights = {emo: 0.05 for emo in EMOTIONS}
        weights['Neutral'] = 0.5
        
        if level == 0: # Rất cao (Excellent)
            weights['Happy'] = 0.3
            weights['Surprise'] = 0.1
            weights['Neutral'] = 0.4
            scores = {'Happy': (0.8, 0.95), 'Surprise': (0.7, 0.9), 'Neutral': (0.7, 0.9)}
            neg_score = (0.1, 0.3)
        elif level == 1: # Cao (Good)
            weights['Happy'] = 0.2
            weights['Surprise'] = 0.1
            scores = {'Happy': (0.7, 0.85), 'Surprise': (0.6, 0.8), 'Neutral': (0.7, 0.9)}
            neg_score = (0.2, 0.4)
        elif level == 2: # Trung bình (Average)
            weights['Happy'] = 0.15
            weights['Neutral'] = 0.6
            scores = {'Happy': (0.5, 0.7), 'Surprise': (0.5, 0.7), 'Neutral': (0.7, 0.9)}
            neg_score = (0.4, 0.6)
        elif level == 3: # Thấp (Low)
            weights['Sad'] = 0.2
            weights['Fear'] = 0.1
            scores = {'Happy': (0.3, 0.5), 'Surprise': (0.3, 0.5), 'Neutral': (0.6, 0.8)}
            neg_score = (0.6, 0.8)
        else: # Rất thấp (Very Low)
            weights['Angry'] = 0.15
            weights['Sad'] = 0.15
            weights['Fear'] = 0.1
            scores = {'Happy': (0.1, 0.3), 'Surprise': (0.1, 0.3), 'Neutral': (0.5, 0.7)}
            neg_score = (0.8, 0.95)

        # Normalize weights
        total_w = sum(weights.values())
        for k in weights:
            weights[k] /= total_w
            
        for emo in EMOTIONS:
            duration = total_duration * weights[emo]
            if emo in scores:
                score = random.uniform(*scores[emo])
            else:
                score = random.uniform(*neg_score)
                
            emotions_stats[emo] = {
                "score": round(score, 2),
                "duration": round(duration, 2)
            }
            
        simulated_data.append({
            "name": name,
            "emotions": emotions_stats
        })
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(simulated_data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Đã tạo dữ liệu mô phỏng phân phối đều cho {NUM_STUDENTS} học sinh vào file {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_simulated_data()
