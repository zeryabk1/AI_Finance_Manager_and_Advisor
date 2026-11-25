"""
Turns a logo image (PNG/JPG, ideally square, at least 256x256) into
app_icon.ico - the file build_exe.bat looks for to brand the .exe.

Usage (from this folder, on the machine you'll build the exe on):
    python make_icon.py path\to\your_logo.png

Requires Pillow (already a dependency of this project, so it should
already be installed - if not: python -m pip install pillow).
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Run: python -m pip install pillow")
    sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python make_icon.py path\\to\\your_logo.png")
        sys.exit(1)

    source = Path(sys.argv[1])
    if not source.exists():
        print(f"Can't find {source}")
        sys.exit(1)

    img = Image.open(source).convert("RGBA")

    # Make it square by padding (not stretching) if it isn't already,
    # so the logo doesn't look squashed in the taskbar/title bar.
    if img.width != img.height:
        side = max(img.width, img.height)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        img = square

    out_path = Path(__file__).parent / "app_icon.ico"
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(out_path, format="ICO", sizes=sizes)

    # Also drop a favicon.ico into static/img for the browser tab icon.
    favicon_dir = Path(__file__).parent / "static" / "img"
    favicon_dir.mkdir(parents=True, exist_ok=True)
    img.save(favicon_dir / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    print(f"Wrote {out_path}")
    print(f"Wrote {favicon_dir / 'favicon.ico'}")
    print("Now run build_exe.bat to rebuild the exe with your logo.")


if __name__ == "__main__":
    main()
