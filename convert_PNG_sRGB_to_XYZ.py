import cv2
import numpy as np
import json
import csv


# ==========================================
# 설정
# ==========================================

IMAGE_PATH = "colorchecker_calibration_result/physical_colorchecker/Blue85.png"
JSON_PATH = "colorchecker_calibration_result/physical_colorchecker/colorchecker_rois.json"

OUTPUT_CSV_PATH = "colorchecker_calibration_result/physical_colorchecker/colorchecker_xyz.csv"


# ==========================================
# 1. PNG 읽기
# ==========================================

png_bgr = cv2.imread(IMAGE_PATH, cv2.IMREAD_COLOR)

if png_bgr is None:
    raise RuntimeError(f"이미지를 읽을 수 없습니다: {IMAGE_PATH}")

# OpenCV BGR -> RGB
png_rgb = cv2.cvtColor(png_bgr, cv2.COLOR_BGR2RGB)

# 0~255 -> 0~1
srgb = png_rgb.astype(np.float64) / 255.0


# ==========================================
# 2. sRGB -> Linear RGB
# inverse sRGB transfer function
# ==========================================

def srgb_to_linear(srgb):
    return np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4
    )


linear_rgb = srgb_to_linear(srgb)


# ==========================================
# 3. Linear sRGB -> CIE XYZ
#
# sRGB / Rec.709 primaries
# D65 white point
# ==========================================

RGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041]
])


# ==========================================
# 4. ROI 정보 읽기
# ==========================================

with open(JSON_PATH, "r", encoding="utf-8") as f:
    roi_data = json.load(f)


results = []


# ==========================================
# 5. 각 ROI의 평균 Linear RGB -> XYZ
# ==========================================

for patch in roi_data["patches"]:

    x_min = patch["x_min"]
    y_min = patch["y_min"]
    x_max = patch["x_max"]
    y_max = patch["y_max"]

    roi = linear_rgb[
        y_min:y_max + 1,
        x_min:x_max + 1
    ]

    # ROI의 평균 linear RGB
    mean_rgb = np.mean(roi, axis=(0, 1))

    # Linear RGB -> XYZ
    xyz = RGB_TO_XYZ @ mean_rgb

    X = float(xyz[0])
    Y = float(xyz[1])
    Z = float(xyz[2])

    result = {
        "row": patch["row"],
        "column": patch["column"],
        "patch": patch["patch"],
        "X": X,
        "Y": Y,
        "Z": Z
    }

    results.append(result)

    print(
        f'{patch["patch"]} '
        f'X={X:.6f}, '
        f'Y={Y:.6f}, '
        f'Z={Z:.6f}'
    )


# ==========================================
# 6. XYZ만 CSV 저장
# ==========================================

with open(
    OUTPUT_CSV_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "row",
            "column",
            "patch",
            "X",
            "Y",
            "Z"
        ]
    )

    writer.writeheader()
    writer.writerows(results)


print()
print("CIE XYZ 계산 완료")
print(f"CSV: {OUTPUT_CSV_PATH}")