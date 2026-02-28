import streamlit as st
from rembg import remove
from PIL import Image, ImageFilter, ImageOps
import io

# ================= 页面配置 =================
st.set_page_config(page_title="高清证件照 - 6寸排版专业版", page_icon="📸", layout="wide")

# ================= 工具函数 =================
def mm_to_px(mm, dpi=300):
    """将毫米转换为像素 (基于300 DPI)"""
    return int((mm / 25.4) * dpi)

def create_6inch_layout(img, dpi=300):
    """将单张证件照排版到 6寸照片纸 (4x6英寸)"""
    # 6寸照片标准尺寸为 102mm * 152mm
    # 300 DPI 下像素约为 1205 * 1795 (通常取整为 1200 * 1800)
    canvas_w = mm_to_px(152, dpi) # 横向打印
    canvas_h = mm_to_px(102, dpi)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    
    img_w, img_h = img.size
    margin = 40  # 留白边距，防止冲印被切掉
    gap = 20     # 照片之间的间隙
    
    x, y = margin, margin
    count = 0
    
    # 自动循环填充
    while y + img_h <= canvas_h - margin:
        while x + img_w <= canvas_w - margin:
            # 添加极细边框方便裁剪
            bordered_img = ImageOps.expand(img, border=1, fill=(220, 220, 220))
            canvas.paste(bordered_img, (x, y))
            x += img_w + gap
            count += 1
        x = margin
        y += img_h + gap
        
    return canvas, count

# ================= UI 界面 =================
st.title("📸 高清证件照大师 (6寸排版版)")
st.markdown("---")

with st.sidebar:
    st.header("1. 尺寸规格")
    mode = st.radio("选择模式", ["标准尺寸", "自定义尺寸 (mm)"])
    
    if mode == "标准尺寸":
        size_label = st.selectbox("预设尺寸", ["一寸 (25x35mm)", "二寸 (35x49mm)", "小二寸 (33x48mm)"])
        presets = {
            "一寸 (25x35mm)": (25, 35),
            "二寸 (35x49mm)": (35, 49),
            "小二寸 (33x48mm)": (33, 48)
        }
        target_mm = presets[size_label]
    else:
        col_w, col_h = st.columns(2)
        with col_w:
            w_mm = st.number_input("宽 (mm)", value=25)
        with col_h:
            h_mm = st.number_input("高 (mm)", value=35)
        target_mm = (w_mm, h_mm)

    st.write(f"🔍 目标像素: {mm_to_px(target_mm[0])} x {mm_to_px(target_mm[1])} px")
    
    st.divider()
    st.header("2. 底色选择")
    color_name = st.radio("底色", ["蓝色", "红色", "白色"])
    color_map = {"蓝色": (0, 191, 255), "红色": (255, 0, 0), "白色": (255, 255, 255)}

    st.divider()
    st.header("3. 打印选项")
    do_layout = st.checkbox("生成6寸(4R)排版图", value=True)

# ================= 主逻辑 =================
uploaded_file = st.file_uploader("上传照片", type=["jpg", "png", "jpeg"])

if uploaded_file:
    if st.button("✨ 立即生成"):
        with st.spinner("AI 正在深度处理..."):
            # 1. 抠图与填色
            input_img = Image.open(uploaded_file)
            no_bg_bytes = remove(uploaded_file.getvalue())
            no_bg_img = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")
            
            # 创建彩色底版
            bg = Image.new("RGBA", no_bg_img.size, color_map[color_name] + (255,))
            combined = Image.alpha_composite(bg, no_bg_img).convert("RGB")
            
            # 2. 毫米转像素并缩放裁剪
            target_w_px = mm_to_px(target_mm[0])
            target_h_px = mm_to_px(target_mm[1])
            
            # 比例缩放
            ratio = max(target_w_px / combined.width, target_h_px / combined.height)
            new_size = (int(combined.width * ratio), int(combined.height * ratio))
            final_single = combined.resize(new_size, Image.Resampling.LANCZOS)
            
            # 中心裁剪
            left = (final_single.width - target_w_px) / 2
            top = (final_single.height - target_h_px) / 2
            final_single = final_single.crop((left, top, left + target_w_px, top + target_h_px))
            
            # 3. 锐化细节
            final_single = final_single.filter(ImageFilter.SHARPEN)
            
            # 4. 展示与下载
            st.subheader("✅ 生成结果")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(final_single, caption="单张 300 DPI 预览")
                buf_s = io.BytesIO()
                final_single.save(buf_s, format="JPEG", quality=95, dpi=(300, 300))
                st.download_button("📥 下载单张", buf_s.getvalue(), "single.jpg", "image/jpeg")

            if do_layout:
                with col2:
                    layout_img, count = create_6inch_layout(final_single)
                    st.image(layout_img, caption=f"6寸排版预览 (已容纳 {count} 张)")
                    buf_l = io.BytesIO()
                    layout_img.save(buf_l, format="JPEG", quality=95, dpi=(300, 300))
                    st.download_button("📥 下载6寸排版图 (可直冲)", buf_l.getvalue(), "layout_6inch.jpg", "image/jpeg")
                    
                    st.success(f"💡 打印小贴士：前往照相馆告诉店员“冲印6寸照片”，或者自备6寸相纸，打印时选择“实际大小”即可。")
