import streamlit as st
from rembg import remove
from PIL import Image, ImageFilter, ImageOps, ImageEnhance  # 引入 ImageEnhance
import io
import numpy as np
import mediapipe as mp

# ================= 初始化 AI 人脸检测 =================
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

# ================= 页面配置 =================
st.set_page_config(page_title="AI 证件照大师 - 全能版", page_icon="👤", layout="wide")

# ================= 工具函数 =================
def mm_to_px(mm, dpi=300):
    return int((mm / 25.4) * dpi)

def ai_smart_crop(img, target_w, target_h):
    """使用 AI 检测人脸并实现黄金比例裁剪"""
    img_array = np.array(img.convert("RGB"))
    results = face_detection.process(img_array)
    
    img_w, img_h = img.size
    
    if results.detections:
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        
        face_center_x = (bbox.xmin + bbox.width / 2) * img_w
        face_center_y = (bbox.ymin + bbox.height / 2) * img_h
        
        # 设定比例：人脸中心在垂直 40% 处
        crop_width = img_w
        crop_height = (target_h / target_w) * crop_width
        
        if crop_height > img_h:
            crop_height = img_h
            crop_width = (target_w / target_h) * crop_height
            
        left = max(0, face_center_x - crop_width / 2)
        top = max(0, face_center_y - crop_height * 0.4)
        right = min(img_w, left + crop_width)
        bottom = min(img_h, top + crop_height)
        
        if right == img_w: left = max(0, right - crop_width)
        if bottom == img_h: top = max(0, bottom - crop_height)
        
        return img.crop((left, top, right, bottom)).resize((target_w, target_h), Image.Resampling.LANCZOS)
    else:
        # 降级方案：中心裁剪
        ratio = max(target_w / img_w, target_h / img_h)
        new_size = (int(img_w * ratio), int(img_h * ratio))
        temp_img = img.resize(new_size, Image.Resampling.LANCZOS)
        l = (temp_img.width - target_w) / 2
        t = (temp_img.height - target_h) / 2
        return temp_img.crop((l, t, l + target_w, t + target_h))

def create_6inch_layout(img, dpi=300):
    """6寸(4R)排版：102mm * 152mm"""
    canvas_w, canvas_h = mm_to_px(152, dpi), mm_to_px(102, dpi)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    img_w, img_h = img.size
    margin, gap = 40, 20
    x, y, count = margin, margin, 0
    
    while y + img_h <= canvas_h - margin:
        while x + img_w <= canvas_w - margin:
            bordered = ImageOps.expand(img, border=1, fill=(220, 220, 220))
            canvas.paste(bordered, (x, y))
            x += img_w + gap
            count += 1
        x, y = margin, y + img_h + gap
        
    return canvas, count

# ================= UI 布局 =================
st.title("👤 AI Pro 证件照大师 (全能版)")
st.caption("AI 对齐 | 300 DPI | 6寸排版 | 面部提亮")
st.markdown("---")

with st.sidebar:
    st.header("1. 规格设定")
    mode = st.radio("模式", ["标准尺寸", "自定义(mm)"])
    if mode == "标准尺寸":
        size_label = st.selectbox("预设", ["一寸 (25x35mm)", "二寸 (35x49mm)"])
        presets = {"一寸 (25x35mm)": (25, 35), "二寸 (35x49mm)": (35, 49)}
        target_mm = presets[size_label]
    else:
        colw, colh = st.columns(2)
        target_mm = (colw.number_input("宽", 25), colh.number_input("高", 35))
    
    st.header("2. 样式设定")
    color_name = st.selectbox("背景颜色", ["蓝色", "红色", "白色"])
    color_map = {"蓝色": (0, 191, 255), "红色": (255, 0, 0), "白色": (255, 255, 255)}
    
    # 🌟 新增：面部提亮滑块
    brightness_factor = st.slider("✨ 面部提亮 (美白)", 1.0, 1.5, 1.1, step=0.05, help="1.0 为原图亮度，越大越亮。")

    st.header("3. 高级选项")
    use_ai_crop = st.checkbox("开启 AI 人脸自动对齐", value=True)

# ================= 主逻辑 =================
uploaded_file = st.file_uploader("上传照片", type=["jpg", "png", "jpeg"])

if uploaded_file:
    if st.button("🚀 开始生成高清证件照"):
        with st.spinner("AI 正在抠图、对齐并优化肤色..."):
            try:
                # 1. 抠图与换底
                no_bg_bytes = remove(uploaded_file.getvalue())
                no_bg_img = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")
                bg = Image.new("RGBA", no_bg_img.size, color_map[color_name] + (255,))
                combined = Image.alpha_composite(bg, no_bg_img).convert("RGB")
                
                # 2. 智能裁剪
                tw, th = mm_to_px(target_mm[0]), mm_to_px(target_mm[1])
                if use_ai_crop:
                    final_single = ai_smart_crop(combined, tw, th)
                else:
                    # 基础缩放裁剪
                    img_w, img_h = combined.size
                    ratio = max(tw/img_w, th/img_h)
                    temp = combined.resize((int(img_w*ratio), int(img_h*ratio)), Image.Resampling.LANCZOS)
                    l, t = (temp.width-tw)/2, (temp.height-th)/2
                    final_single = temp.crop((l, t, l+tw, t+th))
                
                # 3. 细节优化
                final_single = final_single.filter(ImageFilter.SHARPEN) # 锐化

                # 🌟 新增：提亮（美白）核心代码
                if brightness_factor > 1.0:
                    enhancer = ImageEnhance.Brightness(final_single)
                    final_single = enhancer.enhance(brightness_factor) # 这就是那一行代码！
                
                # 4. 展示与下载
                st.subheader("✅ 生成结果")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(final_single, caption=f"单张 300 DPI (亮度 x{brightness_factor})")
                    buf_s = io.BytesIO()
                    final_single.save(buf_s, format="JPEG", quality=95, dpi=(300, 300))
                    st.download_button("📥 下载单张", buf_s.getvalue(), "single.jpg")
                
                with col2:
                    layout_img, count = create_6inch_layout(final_single)
                    st.image(layout_img, caption=f"6寸排版图 (容纳 {count} 张)")
                    buf_l = io.BytesIO()
                    layout_img.save(buf_l, format="JPEG", quality=95, dpi=(300, 300))
                    st.download_button("📥 下载 6 寸排版图 (可直冲)", buf_l.getvalue(), "layout.jpg")
                    
            except Exception as e:
                st.error(f"处理失败: {e}")