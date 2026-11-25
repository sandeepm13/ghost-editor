"""On-screen text of rendered frames with RapidOCR (rapidocr-onnxruntime), for broll_qa.py's caption check on Windows.
The Windows twin of ocr_text.js (macOS Vision): same arguments, same output, so broll_qa.py reads both the same way.

    python scripts/ocr_text_rapid.py img1.jpg img2.jpg ...  -> one JSON line per image on stdout:
      {"img": path, "w": W, "h": H, "lines": [{"text": s, "conf": c, "box": [x, y, w, h] (pixels, origin top-left)}]}

RapidOCR's detector returns a 4-point polygon per text line; the box is its axis-aligned bounds. Its boxes are taller
than Vision's for the same font size (the detector pads each line), so broll_qa.py divides by its own measured ratio
(CAP_RATIO_RAPID). The bundled models (PP-OCRv4 Chinese/English) read Latin text, not Cyrillic.
"""
import json
import sys

import cv2
from rapidocr_onnxruntime import RapidOCR


def main(paths):
    engine = RapidOCR()
    for path in paths:
        img = cv2.imread(path)
        if img is None:
            print(json.dumps({"img": path, "error": "unreadable"}), flush=True)
            continue
        H, W = img.shape[:2]
        try:
            res, _ = engine(img)
        except Exception as e:  # noqa: BLE001 - one bad frame must not lose the others
            print(json.dumps({"img": path, "error": f"ocr failed: {e}"}), flush=True)
            continue
        lines = []
        for quad, text, conf in res or []:
            xs, ys = [float(p[0]) for p in quad], [float(p[1]) for p in quad]
            x0, y0 = max(0.0, min(xs)), max(0.0, min(ys))
            x1, y1 = min(float(W), max(xs)), min(float(H), max(ys))
            lines.append({"text": text, "conf": float(conf), "box": [x0, y0, x1 - x0, y1 - y0]})
        print(json.dumps({"img": path, "w": W, "h": H, "lines": lines}), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
