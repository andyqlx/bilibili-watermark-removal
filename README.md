# B站视频去水印工具

去除 Bilibili 视频右上角的"bilibili"标志和 UP 主名称水印。

## 原理

1. 从多帧提取最大亮度图 → 获得水印图案
2. 自适应阈值定位文字区域
3. 连通域分析过滤噪声 → 紧贴矩形 mask
4. Navier-Stokes 逐帧修复

## 安装

```bash
pip install opencv-python numpy
```

## 使用

```bash
python3 remove_watermark.py input.mp4 output.mp4
```

输出为 mp4v 编码（体积较大），建议用 ffmpeg 重新压缩：

```bash
ffmpeg -i output.mp4 -c:v libx264 -preset fast -crf 20 -movflags +faststart final.mp4
```

## 效果

| 视频 | 水印边缘 | 去后边缘 | 去除率 | 背景保真 |
|------|----------|----------|--------|----------|
| 横屏 720p | 1682 | 0 | 100% | std 不变 |
| 横屏 720p #2 | 1896 | 288 | 85% | std 保留 99.6% |

## 工作原理

- **自适应阈值**：`cv2.adaptiveThreshold(blockSize=21, C=4)` 从多帧 max 图提取文字
- **连通域过滤**：`cv2.connectedComponentsWithStats` 筛选文字区域（80 < area < 15000）
- **紧贴矩形**：pad=0，不做额外膨胀，减少对背景的干扰
- **NS 修复**：`cv2.inpaint(radius=8, INPAINT_NS)` 填入自然纹理

## 参数调整

如果默认参数效果不佳，可修改脚本中的：
- `blockSize`：自适应阈值块大小（21），增大可减少误检
- `C`：阈值常数（4），增大可减少 mask 覆盖
- `area` 范围：连通域面积过滤条件
- `radius`：修复半径（8），影响填充自然度

## License

MIT
