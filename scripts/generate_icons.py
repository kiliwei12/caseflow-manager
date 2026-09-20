"""Generate CaseFlow desktop icons for macOS and Windows builds."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build_assets"
OUTPUT.mkdir(exist_ok=True)

size = 1024
image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((48, 48, 976, 976), radius=220, fill="#FFF0A8", outline="#1C1C1E", width=28)
draw.rounded_rectangle((150, 150, 874, 874), radius=170, fill="#5B76FE")

font_candidates = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
font = None
for candidate in font_candidates:
    if Path(candidate).exists():
        font = ImageFont.truetype(candidate, 560)
        break
if font is None:
    font = ImageFont.load_default()

text = "C"
box = draw.textbbox((0, 0), text, font=font)
width, height = box[2] - box[0], box[3] - box[1]
draw.text(((size - width) / 2, (size - height) / 2 - box[1] - 18), text, font=font, fill="#FFFFFF")

master = OUTPUT / "CaseFlow-1024.png"
image.save(master)
image.save(OUTPUT / "CaseFlow.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

iconset = OUTPUT / "CaseFlow.iconset"
iconset.mkdir(exist_ok=True)
for point_size in (16, 32, 128, 256, 512):
    image.resize((point_size, point_size), Image.Resampling.LANCZOS).save(iconset / f"icon_{point_size}x{point_size}.png")
    image.resize((point_size * 2, point_size * 2), Image.Resampling.LANCZOS).save(iconset / f"icon_{point_size}x{point_size}@2x.png")

print(master)
