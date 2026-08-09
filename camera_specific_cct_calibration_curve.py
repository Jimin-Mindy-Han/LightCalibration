import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import cv2
import colour

# -------------------------
# 1. Calibration curve 생성
# -------------------------

df = pd.read_csv("camera_specific_cct_calibration_reference_images/cct_estimation_results.csv")

target_cct = df["target_cct"].values
estimated_cct = df["estimated_cct"].values

idx = np.argsort(estimated_cct)
estimated_cct = estimated_cct[idx]
target_cct = target_cct[idx]

calibration_curve = interp1d(
    estimated_cct,
    target_cct,
    kind="linear",
    fill_value="extrapolate"
)

# -------------------------
# 2. 색온도 이미지 테스트
# -------------------------

image = cv2.imread(
    "camera_specific_cct_calibration_reference_images/8500K.jpg"
)

CCT_list = []

# BGR -> RGB
preview_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# sRGB [0,255] -> [0,1]
srgb = preview_rgb.astype(np.float32) / 255.0

# sRGB -> Linear RGB
linear_rgb = np.where(
    srgb <= 0.04045,
    srgb / 12.92,
    ((srgb + 0.055) / 1.055) ** 2.4
)

# Linear RGB -> XYZ
M = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041]
], dtype=np.float32)

xyz_image = linear_rgb @ M.T

scale = 0.7

display = cv2.resize(
    image,
    None,
    fx=scale,
    fy=scale
)

x1, y1, w1, h1 = cv2.selectROI(
    "Select colorchecker patches",
    display,
    showCrosshair=True,
    fromCenter=False
)

cv2.destroyAllWindows()

x1 = round(x1 / scale)
y1 = round(y1 / scale)
w1 = round(w1 / scale)
h1 = round(h1 / scale)

colorchecker = image[y1:y1+h1, x1:x1+w1]

# -------------------------
# 3. Gray patch 선택
# -------------------------

for i in range(4):

    display_c = cv2.resize(
        colorchecker,
        None,
        fx=2,
        fy=2
    )

    x2, y2, w2, h2 = cv2.selectROI(
        "Select gray patch",
        display_c,
    )

    x2 = round(x2 / 2)
    y2 = round(y2 / 2)
    w2 = round(w2 / 2)
    h2 = round(h2 / 2)

    x = x1 + x2
    y = y1 + y2
    w = w2
    h = h2

    cv2.destroyAllWindows()

    gray_xyz = xyz_image[y:y+h, x:x+w]

    X, Y, Z = gray_xyz.reshape(-1, 3).mean(axis=0)

    total = X + Y + Z

    chroma_x = X / total
    chroma_y = Y / total

    CCT = colour.xy_to_CCT(
        np.array([chroma_x, chroma_y]),
        method="McCamy 1992"
    )

    CCT_list.append(CCT)

# -------------------------
# 4. CCT 추정 및 calibration
# -------------------------

measured_cct = np.mean(CCT_list)

corrected_cct = float(calibration_curve(measured_cct))

print("Measured CCT:", measured_cct, "K")
print("Error Before Correction:", 100*(abs(measured_cct-8500)/8500), "%")
print("Corrected CCT:", corrected_cct, "K")
print("Ground Truth:", 8500, "K")
print("Error After Correction:", 100*(abs(corrected_cct - 8500)/8500), "%")