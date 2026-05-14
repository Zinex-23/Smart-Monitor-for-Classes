from flask import Flask, render_template, Response, request, jsonify, session, redirect, url_for
from functools import wraps
import cv2
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
import torch
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1
from torch import nn
import torch.nn.functional as F
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
import time
import sys
import io
import threading
import os
from dotenv import load_dotenv
from emotion_analyzer import StudentEmotionAnalyzer
import threading
from time import sleep

load_dotenv()
analyzer = StudentEmotionAnalyzer(
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY"),
    GROQ_API_KEY=os.getenv("GROQ_API_KEY")
)


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smartmonitor-dev-secret-2024-change-in-prod')

# ── Auth helper ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# Camera and emotion detection variables
camera = None
camera_lock = threading.Lock()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize models
mtcnn = MTCNN(keep_all=True, device=device)
face_recog_model = InceptionResnetV1(pretrained='vggface2').eval().to(device)
known_embeddings, known_names = torch.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "new_face_db.pth"), map_location=device)

# Emotion model
emotion_model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
emotion_model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
num_ftrs = emotion_model.fc.in_features
emotion_model.fc = nn.Sequential(
    nn.Linear(num_ftrs, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, 7)
)
checkpoint = torch.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "4_Model_checkpoint.pth"), map_location=device, weights_only=True)
emotion_model.load_state_dict(checkpoint['model_state_dict'])
emotion_model = emotion_model.to(device)
emotion_model.eval()

FER2013_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
json_file_path = "emotion_per_person.json"



# ── Data source mode ─────────────────────────────────────────
# DATA_SOURCE = "camera"      → dùng webcam
# DATA_SOURCE = "video"       → dùng file video
# DATA_SOURCE = "simulation"  → dùng dữ liệu giả lập (không reset JSON)
DATA_SOURCE = os.getenv("DATA_SOURCE", "video")
VIDEO_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           os.getenv("VIDEO_FILE", "KhaNgan.MOV"))

# Global variables
file_path = r'emotion_per_person.json'
current_model_output = None
last_update_time = None
cached_report = None
cached_parsed_data = None
data_lock = threading.Lock()

SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"

TRANSLATIONS = {
    "vi": {
        "dashboard": "Tổng quan",
        "monitoring": "Camera giám sát",
        "video_analysis": "Phân tích video",
        "reports": "Báo cáo tiết học",
        "history": "Lịch sử tiết học",
        "settings": "Cấu hình",
        "logout": "Đăng xuất",
        "teacher": "Giáo viên",
        "account": "Tài khoản",
        "welcome": "Chào mừng",
        "ai_analysis_sub": "Tạo báo cáo chi tiết sử dụng trí tuệ nhân tạo (Groq/Gemini AI)",
        "last_update": "Cập nhật lần cuối",
        "data_source": "Nguồn dữ liệu",
        "video_file": "Tệp video",
        "create_report": "Tạo Báo Cáo Mới",
        "export_file": "Xuất File Báo Cáo",
        "raw_data": "Dữ liệu cảm xúc thô",
        "ai_analysis": "Sử dụng AI để phân tích",
        "detail_report": "Nội dung báo cáo chi tiết",
        "no_report": "Chưa có báo cáo. Vui lòng nhấn Tạo Báo Cáo Mới.",
        "delete_confirm": "Bạn có chắc chắn muốn xóa bản ghi này?",
        "lesson": "Tiết",
        "date": "Ngày",
        "stats": "Thống kê cảm xúc",
        "ai_comment": "Nhận xét từ AI",
        "realtime_monitor_sub": "Giám sát cảm xúc học sinh theo thời gian thực",
        "total_students": "Tổng số học sinh",
        "monitoring_now": "Đang được theo dõi",
        "avg_happiness": "Độ vui vẻ TB",
        "happy_score_avg": "Happy score trung bình",
        "avg_confidence": "Độ tự tin TB",
        "surprise_score_avg": "Surprise score trung bình",
        "avg_anxiety": "Độ lo lắng TB",
        "fear_score_avg": "Fear score trung bình",
        "performance_distribution": "Phân Bố Hiệu Suất Học Tập",
        "positive_emotions": "Cảm Xúc Tích Cực",
        "overall_positive": "Tích cực chung của lớp",
        "no_history_data": "Chưa có dữ liệu lịch sử tiết học nào được ghi lại.",
        "auto_save_msg": "Hệ thống sẽ tự động lưu lại sau khi kết thúc một tiết học theo cấu hình.",
        "input_placeholder": "Dữ liệu sẽ tự động cập nhật từ hệ thống giám sát...",
        "report_config": "Cấu hình báo cáo",
        "nav_title": "Điều hướng",
        "live_camera": "Camera Giám Sát",
        "monitor_live_sub": "Theo dõi lớp học qua Camera trực tiếp",
        "status_offline": "Ngoại tuyến",
        "live_stream": "Luồng Camera Trực Tiếp",
        "live_badge": "Trực tiếp",
        "camera_off": "Camera Đang Tắt",
        "camera_off_sub": "Nhấn nút 'Bật Camera' bên dưới để bắt đầu quan sát.",
        "sim_mode_msg": "Hệ thống đang chạy chế độ Mô phỏng.",
        "sim_mode_sub": "Bạn có thể xem dữ liệu tại Dashboard mà không cần bật Camera.",
        "turn_on_camera": "Bật Camera",
        "turn_off_camera": "Tắt Camera",
        "capture_class": "Chụp Ảnh Của Lớp",
        "video_analysis_sub": "Phân tích cảm xúc từ file video có sẵn trong hệ thống",
        "system_ready": "Hệ thống sẵn sàng",
        "back_to_camera": "Quay lại Camera",
        "ready_to_analyze": "Sẵn sàng phân tích video",
        "play_video_sub": "Nhấn 'Phát Video' bên dưới để bắt đầu quá trình nhận diện cảm xúc từ file.",
        "play_analyze": "Phát Video & Phân Tích",
        "tip": "Mẹo",
        "video_analysis_tip": "Sau khi phát video, bạn có thể chuyển sang trang Dashboard để xem kết quả phân tích theo thời gian thực.",
        "morning_periods": "Số tiết buổi sáng",
        "morning_start_time": "Giờ bắt đầu sáng",
        "afternoon_periods": "Số tiết buổi chiều",
        "afternoon_start_time": "Giờ bắt đầu chiều",
        "lesson_length": "Thời lượng mỗi tiết (phút)",
        "break_length": "Thời gian giải lao (phút)",
        "config_note": "Hệ thống sẽ tự động bắt đầu thu thập dữ liệu camera khi đến giờ bắt đầu từng tiết và tự động tạo báo cáo AI khi kết thúc tiết.",
        "save_settings": "Lưu cấu hình",
        "save_success": "Đã lưu cấu hình thành công! Hệ thống sẽ áp dụng thời gian biểu mới ngay lập tức.",
        "save_error": "Lỗi khi lưu cấu hình",
        "note": "Lưu ý",
        "logout_confirm_title": "Xác nhận đăng xuất",
        "logout_confirm_msg": "Bạn có chắc chắn muốn đăng xuất khỏi hệ thống không?",
        "cancel": "Hủy bỏ",
        "confirm": "Đồng ý",
        "perf_very_low": "Rất thấp",
        "perf_low": "Thấp",
        "perf_medium": "Trung bình",
        "perf_high": "Cao",
        "perf_very_high": "Rất cao",
        "num_students": "Số lượng học sinh",
        "perf_level": "Mức độ hiệu suất",
        "no_data_camera": "Chưa có dữ liệu. Hãy bật camera để bắt đầu ghi nhận.",
        "exporting": "Đang xuất...",
        "report_created": "Báo cáo đã được tạo!",
        "report_error": "Có lỗi xảy ra khi tạo báo cáo!",
        "input_data_error": "Không tìm thấy vùng nhập dữ liệu báo cáo!",
        "input_required": "Vui lòng nhập dữ liệu trước khi tạo báo cáo!",
        "online": "Trực tuyến",
        "conn_error": "Lỗi kết nối",
        "stop_video": "Dừng Video",
        "stop_camera": "Tắt Camera",
        "play_video": "Phát Video",
        "turn_on_camera_toast": "Vui lòng bật camera trước khi chụp ảnh!",
        "capture_success": "Đã chụp ảnh thành công!",
        "not_available": "Chức năng chụp ảnh chưa khả dụng.",
        "switching": "Đang chuyển...",
        "switched_video": "Đã chuyển sang phân tích video",
        "switched_camera": "Đã chuyển sang camera trực tiếp",
        "switch_error": "Lỗi khi chuyển mode",
        "analyzing": "Đang phân tích",
        "video_analysis_title": "Video Phân Tích",
        "no_data": "Chưa có dữ liệu",
        "morning": "Sáng",
        "afternoon": "Chiều",
        "login_meta_desc": "Đăng nhập vào Smart Monitor Class — Hệ thống giám sát cảm xúc học sinh theo thời gian thực",
        "login_title_tab": "Đăng Nhập",
        "login_header_title": "Chào mừng trở lại 👋",
        "login_header_sub": "Đăng nhập để truy cập bảng điều khiển lớp học của bạn."
    },
    "en": {
        "dashboard": "Dashboard",
        "monitoring": "Live Monitoring",
        "video_analysis": "Video Analysis",
        "reports": "Class Reports",
        "history": "Lesson History",
        "settings": "Settings",
        "logout": "Logout",
        "teacher": "Teacher",
        "account": "Account",
        "welcome": "Welcome",
        "ai_analysis_sub": "Generate detailed reports using AI (Groq/Gemini)",
        "last_update": "Last Update",
        "data_source": "Data Source",
        "video_file": "Video File",
        "create_report": "Create New Report",
        "export_file": "Export Report File",
        "raw_data": "Raw Emotion Data",
        "ai_analysis": "Use AI for analysis",
        "detail_report": "Detailed Report Content",
        "no_report": "No report yet. Please click Create New Report.",
        "delete_confirm": "Are you sure you want to delete this record?",
        "lesson": "Lesson",
        "date": "Date",
        "stats": "Emotion Statistics",
        "ai_comment": "AI Comments",
        "realtime_monitor_sub": "Real-time student emotion monitoring",
        "total_students": "Total Students",
        "monitoring_now": "Being monitored",
        "avg_happiness": "Avg Happiness",
        "happy_score_avg": "Average happy score",
        "avg_confidence": "Avg Confidence",
        "surprise_score_avg": "Average surprise score",
        "avg_anxiety": "Avg Anxiety",
        "fear_score_avg": "Average fear score",
        "performance_distribution": "Learning Performance Distribution",
        "positive_emotions": "Positive Emotions",
        "overall_positive": "Overall class positive",
        "no_history_data": "No history data recorded yet.",
        "auto_save_msg": "System will auto-save after each lesson ends based on config.",
        "input_placeholder": "Data will auto-update from monitoring system...",
        "report_config": "Report Configuration",
        "nav_title": "Navigation",
        "live_camera": "Live Monitoring",
        "monitor_live_sub": "Monitor class via live camera",
        "status_offline": "Offline",
        "live_stream": "Live Camera Stream",
        "live_badge": "Live",
        "camera_off": "Camera is Off",
        "camera_off_sub": "Click 'Turn On Camera' below to start monitoring.",
        "sim_mode_msg": "System is running in Simulation mode.",
        "sim_mode_sub": "You can view data on Dashboard without turning on Camera.",
        "turn_on_camera": "Turn On Camera",
        "turn_off_camera": "Turn Off Camera",
        "capture_class": "Capture Class Image",
        "video_analysis_sub": "Analyze emotions from existing video files",
        "system_ready": "System Ready",
        "back_to_camera": "Back to Live Camera",
        "ready_to_analyze": "Ready to Analyze Video",
        "play_video_sub": "Click 'Play Video' below to start emotion recognition from file.",
        "play_analyze": "Play Video & Analyze",
        "tip": "Tip",
        "video_analysis_tip": "After playing the video, you can switch to the Dashboard to see real-time analysis results.",
        "morning_periods": "Number of morning periods",
        "morning_start_time": "Morning start time",
        "afternoon_periods": "Number of afternoon periods",
        "afternoon_start_time": "Afternoon start time",
        "lesson_length": "Lesson duration (minutes)",
        "break_length": "Break duration (minutes)",
        "config_note": "System will auto-start camera capture at lesson start and generate AI reports at the end.",
        "save_settings": "Save Configuration",
        "save_success": "Configuration saved successfully! New schedule applied immediately.",
        "save_error": "Error saving configuration",
        "note": "Note",
        "logout_confirm_title": "Confirm Logout",
        "logout_confirm_msg": "Are you sure you want to log out of the system?",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "perf_very_low": "Very Low",
        "perf_low": "Low",
        "perf_medium": "Medium",
        "perf_high": "High",
        "perf_very_high": "Very High",
        "num_students": "Number of Students",
        "perf_level": "Performance Level",
        "no_data_camera": "No data yet. Please turn on camera to start recording.",
        "exporting": "Exporting...",
        "report_created": "Report created!",
        "report_error": "Error creating report!",
        "input_data_error": "Report input area not found!",
        "input_required": "Please enter data before creating report!",
        "online": "Online",
        "conn_error": "Connection error",
        "stop_video": "Stop Video",
        "stop_camera": "Turn Off Camera",
        "play_video": "Play Video",
        "turn_on_camera_toast": "Please turn on camera before capturing image!",
        "capture_success": "Image captured successfully!",
        "not_available": "Capture function not available yet.",
        "switching": "Switching...",
        "switched_video": "Switched to video analysis",
        "switched_camera": "Switched to live camera",
        "switch_error": "Error switching mode",
        "analyzing": "Analyzing",
        "video_analysis_title": "Video Analysis",
        "no_data": "No data yet",
        "morning": "Morning",
        "afternoon": "Afternoon",
        "login_meta_desc": "Log in to Smart Monitor Class — Real-time student emotion monitoring system",
        "login_title_tab": "Login",
        "login_header_title": "Welcome Back 👋",
        "login_header_sub": "Log in to access your classroom dashboard."
    }
}

def get_report_by_lang(full_report, lang):
    if "[---LANG-SPLIT---]" in full_report:
        parts = full_report.split("[---LANG-SPLIT---]")
        if lang == "en" and len(parts) > 1:
            return parts[1].strip()
        return parts[0].strip()
    return full_report

app.jinja_env.filters['report_lang'] = get_report_by_lang

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'vi')
    return {
        't': TRANSLATIONS.get(lang, TRANSLATIONS['vi']),
        'current_lang': lang,
        't_js': json.dumps(TRANSLATIONS.get(lang, TRANSLATIONS['vi']), ensure_ascii=False)
    }

@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in ["en", "vi"]:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

def load_settings(username="0"):
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(username), data.get("0"))
    except:
        return {
            "morning_count": 5, "afternoon_count": 4,
            "morning_start": "07:30", "afternoon_start": "13:30",
            "lesson_duration": 45, "break_duration": 5
        }

def save_settings(username, config):
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
    except:
        data = {}
    data[str(username)] = config
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_lesson_slots(username="0"):
    settings = load_settings(username)
    slots = []
    try:
        # Morning
        curr = datetime.strptime(settings['morning_start'], "%H:%M")
        for i in range(int(settings['morning_count'])):
            end = curr + timedelta(minutes=int(settings['lesson_duration']))
            slots.append({
                "name": f"Tiết {i+1} - Sáng",
                "start": curr.strftime("%H:%M"),
                "end": end.strftime("%H:%M")
            })
            curr = end + timedelta(minutes=int(settings['break_duration']))
            
        # Afternoon
        curr = datetime.strptime(settings['afternoon_start'], "%H:%M")
        for i in range(int(settings['afternoon_count'])):
            end = curr + timedelta(minutes=int(settings['lesson_duration']))
            slots.append({
                "name": f"Tiết {i+1} - Chiều",
                "start": curr.strftime("%H:%M"),
                "end": end.strftime("%H:%M")
            })
            curr = end + timedelta(minutes=int(settings['break_duration']))
    except Exception as e:
        print(f"Error calculating slots: {e}")
    return slots

active_lesson = None
is_monitoring = False

def auto_scheduler():
    global active_lesson, is_monitoring
    while True:
        try:
            now_str = datetime.now().strftime("%H:%M")
            today_str = datetime.now().strftime("%d/%m/%Y")
            
            # Lấy cấu hình tiết học cho user 0 (admin)
            slots = get_lesson_slots("0")
            
            current_slot = None
            for slot in slots:
                if slot['start'] <= now_str < slot['end']:
                    current_slot = slot
                    break
            
            if current_slot and not is_monitoring:
                # Bắt đầu tiết học
                print(f"[AUTO] Bắt đầu tiết học: {current_slot['name']}")
                active_lesson = current_slot
                is_monitoring = True
                reset_data()
                # Khởi tạo camera (chế độ camera thực tế)
                init_camera("camera") 
                
            elif not current_slot and is_monitoring:
                # Kết thúc tiết học
                print(f"[AUTO] Kết thúc tiết học: {active_lesson['name']}")
                
                # 1. Lấy dữ liệu model hiện tại
                output = get_model_output()
                # 2. Tạo báo cáo AI
                report = analyzer.generate_report(output)
                
                # 3. Tính toán thống kê cảm xúc trung bình
                stats = {}
                for emotion in FER2013_LABELS:
                    total_score = sum(p[emotion]['score_sum'] for p in person_emotion_stats.values())
                    stats[emotion] = round(total_score, 2)

                # 4. Lưu vào Lịch sử
                history_entry = {
                    "id": str(int(time.time())),
                    "username": "0",
                    "lesson_name": active_lesson['name'],
                    "time_range": f"{active_lesson['start']} - {active_lesson['end']}",
                    "date": today_str,
                    "ai_report": report,
                    "emotion_stats": stats
                }
                
                if os.path.exists(HISTORY_FILE):
                    with open(HISTORY_FILE, "r") as f:
                        history = json.load(f)
                else:
                    history = []
                history.insert(0, history_entry)
                with open(HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=4, ensure_ascii=False)
                    
                active_lesson = None
                is_monitoring = False
                # Giải phóng camera khi hết tiết
                with camera_lock:
                    global camera
                    if camera:
                        camera.release()
                        camera = None
        except Exception as e:
            print(f"Error in auto_scheduler: {e}")
            
        sleep(30) # Kiểm tra mỗi 30 giây

# Chạy scheduler trong một luồng riêng biệt
scheduler_thread = threading.Thread(target=auto_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

def reset_data():
    global current_model_output, last_update_time, cached_report, cached_parsed_data, person_emotion_stats
    with data_lock:
        current_model_output = None
        last_update_time = None
        cached_report = None
        cached_parsed_data = None
        # Reset statistics
        person_emotion_stats = defaultdict(lambda: {
            emotion: {"score_sum": 0.0, "duration": 0.0, "count": 0} for emotion in FER2013_LABELS
        })
        
        # Chỉ reset file JSON nếu KHÔNG phải chế độ simulation
        if DATA_SOURCE != "simulation":
            try:
                with open("emotion_per_person.json", "w") as f:
                    json.dump([], f)
            except Exception as e:
                print(f"Error resetting emotion_per_person.json: {e}")

reset_data()

# Emotion tracking variables
start_time = time.time()
last_time = start_time
person_emotion_stats = defaultdict(lambda: {
    emotion: {"score_sum": 0.0, "duration": 0.0, "count": 0} for emotion in FER2013_LABELS
})

# Runtime mode (can switch between "camera" and "video" without restart)
current_mode     = DATA_SOURCE
_video_stop_event = threading.Event()



def get_model_output():
    """Lấy output từ file JSON."""
    # Đọc dữ liệu từ file JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            students_data = json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None  # Trả về None nếu có lỗi đọc file
    
    # Xây dựng chuỗi output từ dữ liệu JSON
    output = ""
    for student in students_data:
        student_name = student['name']
        emotions = student['emotions']
        emotion_details = []
        
        # Tạo các cảm xúc cho từng học sinh
        for emotion, details in emotions.items():
            score = details['score']
            duration = details['duration']
            emotion_details.append(f"{emotion.lower()}={score} ({duration}min)")
        
        # Ghép các thông tin của học sinh lại thành chuỗi
        output += f"{student_name}: " + "; ".join(emotion_details) + " | "
    
    return output.strip(" | ")  # Loại bỏ dấu '|' thừa ở cuối chuỗi

def update_data_continuously():
    while True:
        with data_lock:
            global current_model_output, cached_parsed_data, last_update_time
            new_output = get_model_output()
            if new_output != current_model_output:
                current_model_output = new_output
                if new_output:
                    try:
                        cached_parsed_data = parse_emotion_data(new_output)
                        last_update_time = datetime.now()
                    except Exception as e:
                        print(f"Error parsing in background: {e}")
        sleep(5)


def parse_emotion_data(input_text):
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    students_data = []
    student_entries = input_text.strip().split('|')
    for entry in student_entries:
        entry = entry.strip()
        if not entry:
            continue
        name_match = re.match(r'^([^:]+):', entry)
        if not name_match:
            continue
        student_name = name_match.group(1).strip()
        emotion_pattern = r'(\w+)=([0-9.]+) \(([0-9.]+)min\)'
        emotions = re.findall(emotion_pattern, entry)
        student_emotions = {em: {"score": 0.0, "duration": 0.0} for em in EMOTIONS}
        for emotion, score, duration in emotions:
            if emotion in EMOTIONS:
                student_emotions[emotion] = {
                    'score': float(score),
                    'duration': float(duration)
                }
        students_data.append({
            'name': student_name,
            'emotions': student_emotions
        })
    return students_data

# Chạy background task sau khi đã định nghĩa các hàm cần thiết
thread = threading.Thread(target=update_data_continuously)
thread.daemon = True
thread.start()

def check_data_freshness():
    """Logic cập nhật đã được chuyển sang update_data_continuously."""
    pass

def init_camera(source_type="camera"):
    global camera
    with camera_lock:
        # If camera is already open but for a different source, close it
        if camera is not None:
            camera.release()
            camera = None
            
        if source_type == "video":
            video_file = os.getenv("VIDEO_FILE", "test_video.mp4")
            camera = cv2.VideoCapture(video_file)
            print(f"[INFO] Bắt đầu phân tích video: {video_file}")
        else:
            camera = cv2.VideoCapture(0)
            print("[INFO] Bắt đầu stream camera trực tiếp")
            
        if not camera.isOpened():
            print(f"[ERROR] Không thể mở nguồn {source_type}.")
            camera = None

def save_emotion_data():
    """Ghi dữ liệu cảm xúc vào file JSON"""
    output_json = []
    for person_name, emotions in person_emotion_stats.items():
        emotion_info = {}
        for emotion, stats in emotions.items():
            if stats["duration"] > 0:
                avg_score = stats["score_sum"] / stats["duration"]
                emotion_info[emotion] = {
                    "score": round(avg_score, 2),
                    "duration": round(stats["duration"], 2)
                }
        output_json.append({
            "name": person_name,
            "emotions": emotion_info
        })

    with open(file_path, "w") as f:
        json.dump(output_json, f, indent=4)
def preprocess_emotion_face(face_gray):
    face_gray = cv2.resize(face_gray, (48, 48), interpolation=cv2.INTER_AREA)
    face_tensor = torch.from_numpy(face_gray).unsqueeze(0).unsqueeze(0).float()
    face_tensor = (face_tensor - 127.5) / 127.5
    return face_tensor.to(device)

def generate_frames(source_type="camera"):
    global last_time, person_emotion_stats
    init_camera(source_type)
    
    if camera is None:
        return
    
    while True:
        with camera_lock:
            if camera is None:
                break
            ret, frame = camera.read()
        
        if not ret:
            if DATA_SOURCE == "video":
                # Loop video lại từ đầu
                with camera_lock:
                    if camera is not None:
                        camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        boxes, _ = mtcnn.detect(img)
        faces = mtcnn.extract(img, boxes, save_path=None) if boxes is not None else []

        for i, face_tensor in enumerate(faces):
            name = "Unknown"
            min_dist = 1.0

            # Nhận diện tên
            with torch.no_grad():
                emb = face_recog_model(face_tensor.unsqueeze(0).to(device))
            for db_emb, db_name in zip(known_embeddings, known_names):
                dist = (emb - db_emb).norm().item()
                if dist < min_dist and dist < 0.9:
                    min_dist = dist
                    name = db_name

            # Cắt khuôn mặt
            x1, y1, x2, y2 = [int(coord) for coord in boxes[i]]
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, frame.shape[1]), min(y2, frame.shape[0])
            face_crop = frame[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue

            gray_face = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)

            try:
                input_face = preprocess_emotion_face(gray_face)
                with torch.no_grad():
                    output = emotion_model(input_face)
                    prob = F.softmax(output, dim=1)
                    conf, pred = torch.max(prob, 1)
                    label = FER2013_LABELS[pred.item()]
                    confidence = conf.item()
            except:
                continue

            # Cập nhật thống kê theo người
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            person_stats = person_emotion_stats[name]
            person_stats[label]["score_sum"] += confidence * delta_time
            person_stats[label]["duration"] += delta_time
            person_stats[label]["count"] += 1

            # Hiển thị
            display_text = f"{name} - {label} ({confidence:.2f})"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, display_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 0), 2)

        # Save emotion data periodically
        if int(time.time()) % 10 == 0:  # Save every 10 seconds
            save_emotion_data()

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', 'camera')
    return Response(generate_frames(source), mimetype='multipart/x-mixed-replace; boundary=frame')

# ── Video background processor (no streaming, silent analysis) ──
def video_background_processor():
    """Đọc video, chạy AI inference, cập nhật emotion stats — không stream ra browser."""
    global last_time, person_emotion_stats
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"[ERROR] Không mở được video: {VIDEO_PATH}")
        return
    print(f"[INFO] Video processor bắt đầu: {os.path.basename(VIDEO_PATH)}")
    frame_idx  = 0
    last_save  = time.time()

    while not _video_stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_idx += 1
        if frame_idx % 3 != 0:     # xử lý mỗi 3 frame để giảm tải CPU
            continue

        try:
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img   = Image.fromarray(rgb)
            boxes, _ = mtcnn.detect(img)
            if boxes is None:
                continue
            faces = mtcnn.extract(img, boxes, save_path=None)

            for i, ft in enumerate(faces):
                name = "Unknown"; min_dist = 1.0
                with torch.no_grad():
                    emb = face_recog_model(ft.unsqueeze(0).to(device))
                for db_emb, db_name in zip(known_embeddings, known_names):
                    d = (emb - db_emb).norm().item()
                    if d < min_dist and d < 0.9:
                        min_dist = d; name = db_name

                x1, y1, x2, y2 = [int(c) for c in boxes[i]]
                x1, y1 = max(x1, 0), max(y1, 0)
                x2, y2 = min(x2, frame.shape[1]), min(y2, frame.shape[0])
                fc = frame[y1:y2, x1:x2]
                if fc.size == 0:
                    continue
                gf  = cv2.cvtColor(fc, cv2.COLOR_RGB2GRAY)
                inp = preprocess_emotion_face(gf)
                with torch.no_grad():
                    out  = emotion_model(inp)
                    prob = F.softmax(out, dim=1)
                    conf, pred = torch.max(prob, 1)
                    label      = FER2013_LABELS[pred.item()]
                    confidence = conf.item()

                now = time.time()
                dt  = now - last_time
                last_time = now
                person_emotion_stats[name][label]["score_sum"] += confidence * dt
                person_emotion_stats[name][label]["duration"]  += dt
                person_emotion_stats[name][label]["count"]     += 1
        except Exception as e:
            pass

        if time.time() - last_save >= 10:
            save_emotion_data()
            last_save = time.time()

        time.sleep(0.033)   # ~30 fps

    cap.release()
    print("[INFO] Video processor đã dừng.")


def start_video_processor():
    _video_stop_event.clear()
    t = threading.Thread(target=video_background_processor, daemon=True)
    t.start()


def stop_video_processor():
    _video_stop_event.set()



@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        return redirect(url_for('reports'))
        
    check_data_freshness()
    with data_lock:
        update_time = last_update_time
    return render_template("dashboard.html",
                          active_page='dashboard',
                          last_update=update_time,
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/monitoring", methods=["GET"])
@login_required
def monitoring():
    check_data_freshness()
    return render_template("monitoring.html",
                          active_page='monitoring',
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/video_analysis", methods=["GET"])
@login_required
def video_analysis():
    check_data_freshness()
    return render_template("video_analysis.html",
                          active_page='video_analysis',
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/capture_image", methods=["POST"])
@login_required
def capture_image():
    # Stub for capture image functionality
    return jsonify({"success": False, "message": "Tính năng chụp ảnh đang được bảo trì."})

@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports():
    check_data_freshness()
    report = None
    input_text = ""
    
    if request.method == "POST":
        input_text = request.form.get("input_text", "")
        use_ai = request.form.get("use_ai") == "on"
        if input_text:
            try:
                report = analyzer.analyze_from_text(input_text, use_ai)
            except Exception as e:
                report = f"Error: {str(e)}"
    else:
        with data_lock:
            input_text = current_model_output
            
    return render_template("reports.html",
                          active_page='reports',
                          report=report,
                          input_text=input_text,
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/history", methods=["GET"])
@login_required
def history():
    target_date_iso = request.args.get('date')
    if not target_date_iso:
        target_date_iso = datetime.now().strftime("%Y-%m-%d")
    
    # Chuyển YYYY-MM-DD sang dd/mm/yyyy để khớp với dữ liệu trong json
    try:
        dt = datetime.strptime(target_date_iso, "%Y-%m-%d")
        target_date_display = dt.strftime("%d/%m/%Y")
    except:
        target_date_display = datetime.now().strftime("%d/%m/%Y")
        
    username = str(session.get('user_email', '0'))
        
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                all_data = json.load(f)
        else:
            all_data = []
    except:
        all_data = []
        
    # Lọc dữ liệu theo ngày và username
    filtered_history = [
        item for item in all_data 
        if item.get('date') == target_date_display and str(item.get('username')) == username
    ]
    
    # Sắp xếp theo ID hoặc timestamp (nếu có) - ở đây dùng ID giả định là timestamp
    filtered_history.sort(key=lambda x: x.get('id', '0'), reverse=True)

    return render_template("history.html",
                          active_page='history',
                          history=filtered_history,
                          selected_date=target_date_iso,
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/settings", methods=["GET"])
@login_required
def settings():
    config = load_settings("0")
    return render_template("settings.html",
                          active_page='settings',
                          config=config,
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))

@app.route("/api/save_settings", methods=["POST"])
@login_required
def api_save_settings():
    try:
        config = request.json
        save_settings("0", config)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/delete_history", methods=["POST"])
@login_required
def api_delete_history():
    try:
        history_id = request.json.get('id')
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
            history = [h for h in history if h['id'] != history_id]
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "File not found"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/students", methods=["GET"])
@login_required
def students():
    check_data_freshness()
    return render_template("students.html",
                          active_page='students',
                          data_source=current_mode,
                          video_file=os.path.basename(VIDEO_PATH))


@app.route("/api/update", methods=["POST"])
def api_update():
    try:
        data = request.json
        new_output = data.get('output_model_1', '')
        if new_output:
            global output_model_1
            output_model_1 = new_output
            return jsonify({'status': 'success', 'message': 'Data updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ── Mode switch API ─────────────────────────────────────────
@app.route("/api/switch_mode", methods=["POST"])
@login_required
def api_switch_mode():
    global current_mode, camera
    data     = request.get_json() or {}
    new_mode = data.get("mode", "")
    if new_mode not in ("camera", "video"):
        return jsonify({"error": "mode phải là 'camera' hoặc 'video'"}), 400
    if new_mode == current_mode:
        return jsonify({"mode": current_mode, "video_file": os.path.basename(VIDEO_PATH)})

    current_mode = new_mode

    if new_mode == "video":
        # Giải phóng camera nếu đang mở
        with camera_lock:
            if camera is not None:
                camera.release()
                camera = None
        start_video_processor()
        print("[INFO] Đã chuyển sang chế độ VIDEO")
    else:
        stop_video_processor()
        with camera_lock:
            if camera is not None:
                camera.release()
                camera = None
        print("[INFO] Đã chuyển sang chế độ CAMERA")

    return jsonify({"mode": current_mode, "video_file": os.path.basename(VIDEO_PATH)})


# ── Auth & Account Configuration ────────────────────────────
ACCOUNTS = {
    "1": {"password": "1", "name": "Giáo Viên 1", "mode": "real"},
    "0": {"password": "0", "name": "Tài Khoản Test", "mode": "simulation"}
}

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if email in ACCOUNTS and ACCOUNTS[email]["password"] == password:
            session.permanent = remember
            session['logged_in']   = True
            session['user_email']  = email
            session['user_name']   = ACCOUNTS[email]["name"]
            session['user_mode']   = ACCOUNTS[email]["mode"]
            return redirect(url_for('index'))
            
        error = 'Tài khoản hoặc mật khẩu không đúng. Vui lòng thử lại.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ── Updated Data APIs to support user-specific sources ───────

@app.route("/api/emotions")
@login_required
def api_emotions():
    user_mode = session.get('user_mode', 'real')
    target_file = "simulation_data.json" if user_mode == "simulation" else "emotion_per_person.json"
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Convert to parsed format if necessary
        # If the file is already in our list format, we just return it
        parsed_data = []
        for item in raw_data:
            raw_emotions = item.get('emotions', {})
            # Normalizing keys to lowercase
            normalized_emotions = {k.lower(): v for k, v in raw_emotions.items()}
            
            final_emotions = {}
            for em in ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']:
                final_emotions[em] = normalized_emotions.get(em, {"score": 0.0, "duration": 0.0})
                
            parsed_data.append({
                'name': item.get('name', 'N/A'),
                'emotions': final_emotions
            })
            
        return jsonify({
            'data': parsed_data,
            'last_update': datetime.now().isoformat(),
            'total_students': len(parsed_data)
        })
    except Exception as e:
        print(f"Error loading {user_mode} data: {e}")
        return jsonify({'data': [], 'total_students': 0})

@app.route("/get_input_text", methods=["GET"])
@login_required
def get_input_text_api():
    user_mode = session.get('user_mode', 'real')
    if user_mode == "simulation":
        # Generate a string representation from simulation_data.json
        try:
            with open("simulation_data.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            output = []
            for student in data:
                ems = student['emotions']
                em_str = " ".join([f"{k}={v['score']} ({v['duration']}min)" for k, v in ems.items()])
                output.append(f"{student['name']}: {em_str}")
            return jsonify({"input_text": " | ".join(output)})
        except:
            return jsonify({"input_text": ""})
    else:
        with data_lock:
            return jsonify({"input_text": current_model_output})

# ── Auto-start video processor if default mode is video ──────
if DATA_SOURCE == "video":
    start_video_processor()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

