import streamlit as st
from rembg import remove
from PIL import Image
import io

# 设置页面配置
st.set_page_config(page_title="AI 证件照大师", layout="centered")

st.title("📸 AI 智能证件照制作")
st.write("上传一张照片，秒变专业证件照！")

# 1. 参数设置
with st.sidebar:
    st.header("⚙️ 制作设置")
    
    # 尺寸选择
    size_option = st.selectbox("选择尺寸", ["一寸 (295x413)", "二寸 (413x579)"])
    size_map = {
        "一寸 (295x413)": (295, 413),
        "二寸 (413x579)": (413, 579)
    }
    
    # 颜色选择
    color_name = st.radio("选择底色", ["蓝色", "红色", "白色"])
    color_map = {
        "蓝色": (0, 191, 255),
        "红色": (255, 0, 0),
        "白色": (255, 255, 255)
    }

# 2. 图片上传
uploaded_file = st.file_uploader("选择你的照片...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 展示原图
    input_image = Image.open(uploaded_file)
    st.image(input_image, caption="原始图片", width=200)
    
    if st.button("✨ 开始制作"):
        with st.spinner("AI 正在努力抠图中，请稍候..."):
            try:
                # 抠图
                input_bytes = uploaded_file.getvalue()
                output_bytes = remove(input_bytes)
                no_bg_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                # 创建底色
                bg_color = color_map[color_name]
                final_photo = Image.new("RGBA", no_bg_img.size, bg_color)
                final_photo.paste(no_bg_img, (0, 0), no_bg_img)
                final_photo = final_photo.convert("RGB")
                
                # 裁剪缩放
                target_size = size_map[size_option]
                # 保持比例缩放并裁剪
                ratio = max(target_size[0]/final_photo.width, target_size[1]/final_photo.height)
                new_size = (int(final_photo.width*ratio), int(final_photo.height*ratio))
                final_photo = final_photo.resize(new_size, Image.LANCZOS)
                
                left = (final_photo.width - target_size[0]) / 2
                top = (final_photo.height - target_size[1]) / 2
                final_photo = final_photo.crop((left, top, left + target_size[0], top + target_size[1]))
                
                # 显示结果
                st.success("处理成功！")
                st.image(final_photo, caption="生成效果")
                
                # 准备下载
                buf = io.BytesIO()
                final_photo.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 下载证件照",
                    data=byte_im,
                    file_name="my_id_photo.jpg",
                    mime="image/jpeg"
                )
            except Exception as e:
                st.error(f"处理出错啦: {e}")