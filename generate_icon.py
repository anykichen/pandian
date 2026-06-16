"""
生成应用程序图标
运行此脚本生成 icon.ico 文件
"""
from PIL import Image, ImageDraw

# 创建一个 256x256 的图标
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
images = []

for size in sizes:
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 计算尺寸
    w, h = size
    margin = w // 8
    
    # 绘制圆角矩形背景
    draw.rounded_rectangle(
        [margin, margin, w - margin - 1, h - margin - 1],
        radius=w // 6,
        fill=(66, 133, 244, 255)  # Google Blue
    )
    
    # 绘制盘点"√"符号
    inner_margin = w // 3
    draw.rounded_rectangle(
        [inner_margin, inner_margin, w - inner_margin - 1, h - inner_margin - 1],
        radius=w // 8,
        fill=(52, 168, 83, 255)  # Green
    )
    
    # 绘制对勾
    check_points = [
        (w * 0.25, h * 0.5),
        (w * 0.42, h * 0.65),
        (w * 0.75, h * 0.35)
    ]
    draw.line(check_points, fill=(255, 255, 255, 255), width=max(1, w // 10))
    
    images.append(img)

# 保存为 ICO 文件
images[0].save('icon.ico', format='ICO', sizes=[(s[0], s[1]) for s in sizes], append_images=images[1:])
print('图标已生成: icon.ico')
