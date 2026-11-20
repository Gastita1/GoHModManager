from PIL import Image, ImageDraw

def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)

for size in [256]:
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 背景圆角方块
    rounded(d, (4, 4, S - 4, S - 4), int(S * 0.22), (27, 32, 41, 255))
    # 橙色描边
    d.rounded_rectangle((4, 4, S - 4, S - 4), radius=int(S * 0.22), outline=(226, 112, 58, 255), width=max(2, S // 42))
    # 三条递增的“加载顺序”横条
    bar_h = int(S * 0.10)
    gap = int(S * 0.075)
    widths = [0.36, 0.50, 0.64]
    colors = [(150, 74, 39, 255), (190, 92, 48, 255), (226, 112, 58, 255)]
    total = bar_h * 3 + gap * 2
    y = (S - total) // 2
    for i, wf in enumerate(widths):
        w = int(S * wf)
        x = (S - w) // 2
        d.rounded_rectangle((x, y, x + w, y + bar_h), radius=bar_h // 2, fill=colors[i])
        y += bar_h + gap
    # 底部小圆点（启用指示）
    r = int(S * 0.045)
    d.ellipse((S // 2 - r, int(S * 0.79), S // 2 + r, int(S * 0.79) + r * 2), fill=(78, 197, 140, 255))
    img.save(r"C:\Users\时雨时衣\Documents\deepseek-harness\default-workspace\GoHModManager\assets\app.png")
    img.save(r"C:\Users\时雨时衣\Documents\deepseek-harness\default-workspace\GoHModManager\assets\app.ico",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon ok")
