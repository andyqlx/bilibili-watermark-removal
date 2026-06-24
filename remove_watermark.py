#!/usr/bin/env python3
"""
B站视频去水印工具 - v9
Adaptive threshold + component rectangles + NS inpainting

用法:
    python3 remove_watermark.py input.mp4 output.mp4

依赖:
    pip install opencv-python numpy
"""

import cv2
import numpy as np
import sys


def remove_watermark(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open {input_path}")
        sys.exit(1)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Input: {w}x{h}, {fps:.1f}fps, {total} frames")

    # Step 1: 多帧 max 提取水印图案
    max_frame = None
    sample_step = max(1, total // 80)
    for frm in range(30, total, sample_step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frm)
        ret, f = cap.read()
        if not ret:
            continue
        r = f[0:130, w - 460 : w].astype(np.float32)
        max_frame = r if max_frame is None else np.maximum(max_frame, r)

    # Step 2: 自适应阈值找文字
    max_img = max_frame.astype(np.uint8)
    gray = cv2.cvtColor(max_img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 4
    )
    inverted = 255 - binary

    # Step 3: 连通域过滤，组件矩形 (pad=5)
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        inverted, connectivity=8
    )
    mask = np.zeros((130, 460), dtype=np.uint8)
    kept = 0
    pad = 5
    for i in range(1, n_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        if 80 < area < 15000 and x > 5:
            x1 = max(0, stats[i, cv2.CC_STAT_LEFT] - pad)
            y1 = max(0, stats[i, cv2.CC_STAT_TOP] - pad)
            x2 = min(460, x1 + stats[i, cv2.CC_STAT_WIDTH] + 2 * pad)
            y2 = min(130, y1 + stats[i, cv2.CC_STAT_HEIGHT] + 2 * pad)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            kept += 1

    pct = 100 * np.sum(mask > 0) / mask.size
    print(f"Mask: {kept}/{n_labels - 1} components, {pct:.1f}% coverage")

    # Step 4: 逐帧 NS 修复
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[0:130, w - 460 : w] = mask

    out = cv2.VideoWriter(
        output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h)
    )

    for i in range(total):
        ret, frame = cap.read()
        if not ret:
            break
        result = cv2.inpaint(frame, full_mask, 8, cv2.INPAINT_NS)
        out.write(result)
        if (i + 1) % 400 == 0:
            print(f"  {i+1}/{total} ({100*(i+1)/total:.0f}%)", flush=True)

    cap.release()
    out.release()
    print(f"Done! Output: {output_path}")
    print("Tip: Re-encode with H.264 to reduce file size:")
    print(f"  ffmpeg -i {output_path} -c:v libx264 -crf 20 output.mp4")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 remove_watermark.py input.mp4 output.mp4")
        sys.exit(1)
    remove_watermark(sys.argv[1], sys.argv[2])
