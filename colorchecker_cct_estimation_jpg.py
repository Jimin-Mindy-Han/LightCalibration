import cv2
import numpy as np
import colour
import os
import csv

folder_path = "camera_specific_cct_calibration_reference_images"
csv_path = "camera_specific_cct_calibration_reference_images/cct_estimation_results.csv"
results = []

for filename in sorted(os.listdir(folder_path)):
    if not filename.lower().endswith(".jpg"):
        continue

    image_path = os.path.join(folder_path, filename)
    image = cv2.imread(image_path)

    CCT_list = []

    # opencv BGR -> RGB 변환
    preview_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # sRGB [0,255] -> [0,1] 변환
    srgb = preview_rgb.astype(np.float32) / 255.0

    # sRGB -> Linear RGB
    linear_rgb = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4
    )

    # Linear sRGB -> CIE XYZ
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

    # 표시 이미지 좌표 -> 원본 이미지 좌표
    x1 = round(x1 / scale)
    y1 = round(y1 / scale)
    w1 = round(w1 / scale)
    h1 = round(h1 / scale)

    colorchecker = image[y1:y1+h1, x1:x1+w1]

    for i in range(4):

        x2, y2, w2, h2 = cv2.selectROI(
            "Select gray patch",
            colorchecker
        )

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

    CCT = np.mean(CCT_list)

    target_cct = int(os.path.splitext(filename)[0].replace("K", ""))

    results.append([target_cct, CCT])

    print(filename, "CCT:", CCT, "K")

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["target_cct", "estimated_cct"])
    writer.writerows(results)