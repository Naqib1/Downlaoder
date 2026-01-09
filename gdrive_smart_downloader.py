import streamlit as st
import yt_dlp
import os
import time
import glob
import re
import subprocess

# إعدادات الصفحة
st.set_page_config(
    page_title="GDrive Smart Downloader",
    page_icon="🧠",
    layout="centered"
)

# تصميم CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(45deg, #00C9FF, #92FE9D);
        color: #0e1117;
        font-weight: bold;
        font-size: 1.1rem;
        border: none;
        transition: 0.4s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 201, 255, 0.4);
    }
    .title-text {
        text-align: center;
        background: -webkit-linear-gradient(#00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3rem;
        margin-bottom: 0.2rem;
    }
    .subtitle-text {
        text-align: center;
        color: #aaa;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .ffmpeg-warning {
        padding: 15px;
        border-radius: 10px;
        background-color: rgba(255, 75, 75, 0.1);
        border: 1px solid #FF4B4B;
        color: #FF4B4B;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# التحقق من وجود FFmpeg
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except:
        return False

has_ffmpeg = check_ffmpeg()

st.markdown('<h1 class="title-text">🧠 GDrive Smart</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">التحميل الذكي - يتكيف مع إمكانيات جهازك تلقائياً</p>', unsafe_allow_html=True)

if not has_ffmpeg:
    st.markdown("""
    <div class="ffmpeg-warning">
        ⚠️ <b>تنبيه: برنامج FFmpeg غير مثبت على جهازك!</b><br>
        التطبيق سيعمل في "الوضع المتوافق" وسيقوم بتحميل أفضل جودة مدمجة (غالباً 720p). 
        لفتح جودات 1080p و 4K، يرجى تثبيت FFmpeg.
    </div>
    """, unsafe_allow_html=True)
    with st.expander("🛠️ كيف أثبت FFmpeg؟ (لفتح الجودات العالية)"):
        st.markdown("""
        1. حمل النسخة المناسبة لويندوز من [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
        2. فك الضغط عن الملف وانقل مجلد `bin` لمكان ثابت (مثلاً `C:\\ffmpeg`).
        3. أضف المسار لمتغيرات البيئة (Environment Variables -> Path).
        4. أعد تشغيل الجهاز.
        """)

# واجهة المدخلات
url = st.text_input("🔗 رابط الفيديو:", placeholder="ضع رابط جوجل درايف هنا...")

col1, col2 = st.columns(2)
with col1:
    # إذا لم يوجد ffmpeg، نلغي خيارات الدمج الإجبارية
    if has_ffmpeg:
        merge_option = st.radio("🛠️ خيار الدمج:", ["تلقائي (أفضل جودة)", "إجباري (MP4)", "إجباري (MKV)"])
    else:
        st.warning("خيارات الدمج معطلة لغياب FFmpeg")
        merge_option = "تلقائي (أفضل جودة)"
with col2:
    speed_limit = st.select_slider("🚀 السرعة القصوى:", options=["عادية", "سريعة", "قصوى"], value="قصوى")

# قسم الكوكيز
with st.expander("🔑 إعدادات الوصول (Cookies)"):
    uploaded_cookies = st.file_uploader("ارفع ملف cookies.txt:", type=["txt"])

def progress_hook(d):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        st.session_state.status = f"📥 جاري التحميل: {p} | السرعة: {d.get('_speed_str', 'N/A')}"

def download_smart(url, cookie_path, merge_opt, speed, has_ff):
    fragments = 8 if speed == "عادية" else (16 if speed == "سريعة" else 32)
    
    # منطق اختيار الجودة الذكي
    if has_ff:
        # إذا وجد ffmpeg، نطلب أفضل فيديو + أفضل صوت
        format_selection = "bestvideo+bestaudio/best"
    else:
        # إذا لم يوجد، نطلب أفضل ملف واحد يحتوي على (فيديو + صوت) معاً
        format_selection = "best"
    
    output_id = int(time.time())
    output_template = f"smart_video_{output_id}.%(ext)s"
    
    ydl_opts = {
        "format": format_selection,
        "outtmpl": output_template,
        "concurrent_fragment_downloads": fragments,
        "cookiefile": cookie_path if cookie_path else None,
        "progress_hooks": [progress_hook],
        "nocheckcertificate": True,
        "quiet": True,
    }

    # إضافة خيارات الدمج فقط إذا وجد ffmpeg
    if has_ff:
        ext = "mp4" if "MP4" in merge_opt else ("mkv" if "MKV" in merge_opt else None)
        if ext:
            ydl_opts["merge_output_format"] = ext

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # التأكد من وجود الملف (قد يتغير الامتداد بعد التحميل)
            if os.path.exists(filename):
                return True, filename
            
            # البحث عن الملف الفعلي
            base_name = filename.rsplit('.', 1)[0]
            files = glob.glob(f"{base_name}.*")
            if files:
                return True, max(files, key=os.path.getctime)
            
            return False, "لم يتم العثور على الملف بعد التحميل"
        except Exception as e:
            return False, str(e)

if st.button("🧠 ابدأ التحميل الذكي"):
    if not url:
        st.error("❌ يرجى إدخال الرابط!")
    else:
        cookie_tmp_path = None
        if uploaded_cookies:
            cookie_tmp_path = f"temp_cookies_{int(time.time())}.txt"
            with open(cookie_tmp_path, "wb") as f:
                f.write(uploaded_cookies.getbuffer())

        status_container = st.empty()
        
        with st.spinner("جاري التحميل..."):
            success, result = download_smart(url, cookie_tmp_path, merge_option, speed_limit, has_ffmpeg)
            
            if success:
                status_container.success("✨ اكتمل التحميل بنجاح!")
                with open(result, "rb") as f:
                    st.download_button(
                        label="💾 حفظ الفيديو على جهازك",
                        data=f,
                        file_name=os.path.basename(result),
                        mime="video/mp4"
                    )
                st.balloons()
            else:
                st.error(f"❌ حدث خطأ: {result}")

        if cookie_tmp_path and os.path.exists(cookie_tmp_path):
            os.remove(cookie_tmp_path)

st.markdown("---")
st.caption("تم التطوير بواسطة Manus AI - نسخة ذكية تتخطى أخطاء FFmpeg")
