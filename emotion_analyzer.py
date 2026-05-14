import json
import re
import google.generativeai as genai
from groq import Groq
import os

EMOTION_VI = {
    "Angry":   "Tức giận",
    "Disgust": "Ghê tởm",
    "Fear":    "Sợ hãi",
    "Happy":   "Vui vẻ",
    "Sad":     "Buồn bã",
    "Surprise":"Ngạc nhiên",
    "Neutral": "Bình thường",
}


class StudentEmotionAnalyzer:
    def __init__(self, GEMINI_API_KEY: str = None, GROQ_API_KEY: str = None, **kwargs):
        # Setup Gemini
        self.gemini_enabled = False
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                self.gemini_enabled = True
            except Exception as e:
                print(f"[ERROR] Failed to init Gemini: {e}")

        # Setup Groq
        self.groq_enabled = False
        if GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                self.groq_enabled = True
            except Exception as e:
                print(f"[ERROR] Failed to init Groq: {e}")

    def analyze_and_generate_report(self, json_file_path: str, use_ai: bool = True) -> str:
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "Chưa có dữ liệu cảm xúc để phân tích."
        return self.generate_report_from_data(data, use_ai)

    def analyze_from_text(self, input_text: str, use_ai: bool = True) -> str:
        """Phân tích từ chuỗi text thô (định dạng: Tên: Cảm xúc=Score (Duration) | ...)"""
        if not input_text:
            return "Không có dữ liệu văn bản để phân tích."
        
        # Chuyển đổi text thô sang cấu trúc dữ liệu JSON để tái sử dụng logic
        students = []
        entries = input_text.strip().split('|')
        for entry in entries:
            entry = entry.strip()
            if not entry or ':' not in entry: continue
            name, raw_emotions = entry.split(':', 1)
            emotions = {}
            # Regex để bắt: Angry=0.19 (1.98min)
            pattern = r'(\w+)=([0-9.]+)\s*\(([0-9.]+)min\)'
            matches = re.findall(pattern, raw_emotions)
            for emo, score, duration in matches:
                emotions[emo] = {
                    "score": float(score),
                    "duration": float(duration) # Giữ nguyên đơn vị phút
                }
            if emotions:
                students.append({"name": name.strip(), "emotions": emotions})
        
        return self.generate_report_from_data(students, use_ai)

    def generate_report_from_data(self, students_data: list, use_ai: bool = True) -> str:
        if not students_data:
            return "Chưa có dữ liệu học sinh để phân tích."

        students = [s for s in students_data if isinstance(s, dict) and s.get("name") != "Unknown"]
        if not students:
            students = [s for s in students_data if isinstance(s, dict)]

        summary = self._build_summary(students)
        if not use_ai:
            return summary

        prompt = f"""Bạn là chuyên gia tư vấn tâm lý giáo dục và phân tích hành vi lớp học. 
Dưới đây là dữ liệu cảm xúc thu thập được từ một tiết học:

{self._build_raw_summary(students)}

Yêu cầu viết báo cáo đánh giá mang tính ĐỊNH TÍNH chuyên sâu, chi tiết và có chiều sâu. 
Phân tích kỹ lưỡng các xu hướng cảm xúc, nguyên nhân có thể có và tác động đến hiệu quả học tập.
BẠN PHẢI TẠO RA 2 PHIÊN BẢN: TIẾNG VIỆT VÀ TIẾNG ANH.

Cấu trúc mỗi bản gồm:
1. Không khí và trạng thái tinh thần chung (Phân tích chi tiết về năng lượng và tinh thần của lớp).
2. Phân tích nhóm học sinh nổi bật (Nhận xét về các nhóm học sinh có biểu hiện cảm xúc tương đồng).
3. ĐIỂM CẦN CẢI THIỆN (Chỉ ra các vấn đề cụ thể cần lưu ý).
4. KHUYẾN NGHỊ SƯ PHẠM (Đưa ra các giải pháp, kỹ thuật giảng dạy cụ thể để tối ưu hóa không khí lớp học).

LƯU Ý QUAN TRỌNG: 
- KHÔNG sử dụng bất kỳ định dạng Markdown nào (không **, không #).
- Chỉ viết văn bản thuần túy (Plain text).
- KHÔNG viết phần kết luận chung chung.
- Ngăn cách 2 phiên bản bằng chuỗi ký tự chính xác này: [---LANG-SPLIT---] (Tiếng Việt trước, Tiếng Anh sau).
- Ngôn ngữ chuyên nghiệp, tinh tế, giàu tính chuyên môn sư phạm.
- Viết dài, chi tiết và có sức thuyết phục."""

        return self._call_ai(prompt, summary)

    def generate_report(self, raw_output_string: str) -> str:
        """Alias cho analyze_from_text dùng trong scheduler"""
        return self.analyze_from_text(raw_output_string, use_ai=True)

    def _call_ai(self, prompt: str, fallback_summary: str) -> str:
        errors = []
        if self.gemini_enabled:
            try:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                errors.append(f"Gemini: {str(e)}")
        
        if self.groq_enabled:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                errors.append(f"Groq: {str(e)}")

        error_info = "\n".join(errors)
        if error_info:
            return self._fallback(f"Cả Gemini và Groq đều gặp lỗi:\n{error_info}", fallback_summary)
        return self._fallback("Không có API Key nào khả dụng.", fallback_summary)

    def _fallback(self, reason: str, summary: str) -> str:
        return f"⚠️ {reason}\n\n{summary}"

    def _build_summary(self, students: list) -> str:
        if not students:
            return "Không có dữ liệu học sinh.\n\n[---LANG-SPLIT---]\n\nNo student data available."
        
        # VI Version
        lines_vi = [f"📊 Báo Cáo Cảm Xúc — {len(students)} học sinh\n{'─'*40}"]
        for student in students:
            name     = student.get("name", "?")
            emotions = student.get("emotions", {})
            dominant = max(emotions.items(), key=lambda x: x[1].get("score", 0), default=(None, {}))
            dom_name = EMOTION_VI.get(dominant[0], dominant[0]) if dominant[0] else "—"
            dom_pct  = dominant[1].get("score", 0) * 100
            lines_vi.append(f"\n👤 {name}  (chủ đạo: {dom_name} {dom_pct:.0f}%)")
            for emo, stats in emotions.items():
                score    = stats.get("score", 0) * 100
                duration = stats.get("duration", 0)
                bar      = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                lines_vi.append(f"   {EMOTION_VI.get(emo, emo):<12} {bar} {score:4.0f}%  ({duration:.1f}min)")
        
        # EN Version
        lines_en = [f"📊 Emotion Report — {len(students)} students\n{'─'*40}"]
        for student in students:
            name     = student.get("name", "?")
            emotions = student.get("emotions", {})
            dominant = max(emotions.items(), key=lambda x: x[1].get("score", 0), default=(None, {}))
            dom_name = dominant[0].capitalize() if dominant[0] else "—"
            dom_pct  = dominant[1].get("score", 0) * 100
            lines_en.append(f"\n👤 {name}  (dominant: {dom_name} {dom_pct:.0f}%)")
            for emo, stats in emotions.items():
                score    = stats.get("score", 0) * 100
                duration = stats.get("duration", 0)
                bar      = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                lines_en.append(f"   {emo.capitalize():<12} {bar} {score:4.0f}%  ({duration:.1f}min)")
        
        return "\n".join(lines_vi) + "\n\n[---LANG-SPLIT---]\n\n" + "\n".join(lines_en)

    def _build_raw_summary(self, students: list) -> str:
        lines = []
        for student in students:
            name  = student.get("name", "?")
            parts = [f"{e}: {v.get('score',0):.2f} ({v.get('duration',0):.1f}min)"
                     for e, v in student.get("emotions", {}).items()]
            lines.append(f"- {name}: {', '.join(parts)}")
        return "\n".join(lines) if lines else "Không có dữ liệu.\n\n[---LANG-SPLIT---]\n\nNo data available."
