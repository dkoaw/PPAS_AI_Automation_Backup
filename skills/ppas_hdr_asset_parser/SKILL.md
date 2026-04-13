---
name: PPAS HDR Asset Parser
description: Scan the designated asset library for HDR files and their corresponding thumbnails, returning a structured categorized dictionary for UI rendering.
---

# PPAS HDR Asset Parser

## 核心职责 (Core Responsibilities)
本技能负责驻守 `X:\AI_Automation\AI_Asset_lib\hdr_lighting_pic_for_lighting` 目录，执行递归扫描以发现所有的环境光贴图(`.hdr`, `.exr`)，并探测同名代理图片(`.png`, `.jpg`)。最终吐出供 Qt 画廊使用的流式数据源。

## 使用场景 (Usage Scenario)
为 `HDR 光照图管理器 (Qt 面板)` 提供绝对底层的数据依托，剥离了 Qt 界面在主线程慢速扫描高位深图像导致线程假死的问题。

## 输入输出 (I/O)
* **输入**: 根目录字符串路径。
* **输出**: 嵌套结构字典。例如:
```json
{
    "City_night": [
        {
            "name": "City_night_01",
            "hdr_path": "X:\\...\\City_night_01.hdr",
            "thumbnail_path": "X:\\...\\City_night_01.jpg"
        }
    ]
}
```
