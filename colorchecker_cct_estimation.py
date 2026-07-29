import cv2
import numpy as np
import colour
import rawpy

# image = cv2.imread('cct_estimation_reference_images/2500K_grayscale.ARW')
raw_image = rawpy.imread('cct_estimation_reference_images/5500K.ARW')
# image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
CCT_list = []

# 좌표 선택용 이미지
preview_rgb = raw_image.postprocess(
    output_color=rawpy.ColorSpace.sRGB,
    use_camera_wb=False,
    use_auto_wb=False,
    no_auto_bright=True,
    output_bps=8
)

# 실제 계산용 선형 XYZ 이미지
xyz_image = raw_image.postprocess(
    output_color=rawpy.ColorSpace.XYZ,
    use_camera_wb=False,
    use_auto_wb=False,
    no_auto_bright=True,
    gamma=(1, 1),
    output_bps=16
).astype(np.float32) / 65535.0

scale = 0.3  # 화면에 맞게 조절
display = cv2.resize(
    cv2.cvtColor(preview_rgb, cv2.COLOR_RGB2BGR),
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

# 표시 이미지 좌표 → 원본 현상 이미지 좌표
x1 = round(x1 / scale)
y1 = round(y1 / scale)
w1 = round(w1 / scale)
h1 = round(h1 / scale)

colorchecker = cv2.cvtColor(preview_rgb, cv2.COLOR_RGB2BGR)
colorchecker = colorchecker[y1:y1+h1,x1:x1+w1]

for i in range(0, 4):
    # 두번째 선택
    x2, y2, w2, h2 = cv2.selectROI("Select gray patch", colorchecker)
    # 원본 이미지 기준 gray patch 좌표
    x = x1 + x2
    y = y1 + y2
    w = w2
    h = h2

    cv2.destroyAllWindows()

    gray_xyz = xyz_image[y:y + h, x:x + w]

    X, Y, Z = gray_xyz.reshape(-1, 3).mean(axis=0)
    total = X + Y + Z
    x = X / total
    y = Y / total

    CCT = colour.xy_to_CCT(np.array([x, y]), method="McCamy 1992")
    CCT_list.append(CCT)

CCT = np.mean(CCT_list, axis=0)
print("CCT:", CCT, "K")