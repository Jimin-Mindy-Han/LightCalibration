import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import glob
import cv2
import numpy as np
import json
import csv

# ==========================================
# 설정
# ==========================================

IMAGE_DIR = "colorchecker_calibration_result/test/virtual_colorchecker/"
JSON_PATH = "colorchecker_calibration_result/virtual_colorchecker/colorchecker_rois.json"

CSV_DIR = "colorchecker_calibration_result/test/virtual_colorchecker/XYZ/"

# ==========================================
# 1. HDR 읽기
# ==========================================
virtual_files = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.hdr")))
for virtual_file in virtual_files:
    IMAGE_PATH = virtual_file

    hdr_bgr = cv2.imread(
        IMAGE_PATH,
        cv2.IMREAD_UNCHANGED
    )

    if hdr_bgr is None:
        raise RuntimeError(f"이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    # print("HDR shape:", hdr_bgr.shape)
    # print("HDR dtype:", hdr_bgr.dtype)
    # print("HDR min/max:", np.min(hdr_bgr), np.max(hdr_bgr))


    # ==========================================
    # 2. BGR -> RGB
    #
    # UE SceneColor HDR은 이미 linear이므로
    # sRGB inverse transfer function은 적용하지 않음
    # ==========================================

    hdr_rgb = cv2.cvtColor(hdr_bgr, cv2.COLOR_BGR2RGB)

    hdr_rgb = hdr_rgb.astype(np.float64)


    # ==========================================
    # 3. Linear sRGB / Rec.709 -> CIE XYZ
    #
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
    # 5. 각 ROI 평균 RGB -> CIE XYZ
    # ==========================================

    for patch in roi_data["patches"]:

        x_min = patch["x_min"]
        y_min = patch["y_min"]
        x_max = patch["x_max"]
        y_max = patch["y_max"]

        roi = hdr_rgb[
            y_min:y_max + 1,
            x_min:x_max + 1
        ]

        if roi.size == 0:
            raise RuntimeError(
                f'{patch["patch"]} ROI가 비어 있습니다.'
            )

        # ROI 평균 linear RGB
        mean_rgb = np.mean(
            roi,
            axis=(0, 1)
        )

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
    # 6. CSV 저장
    # ==========================================
    xyz_filename = os.path.splitext(os.path.basename(virtual_file))[0]
    CSV_PATH = CSV_DIR + xyz_filename + ".csv"

    with open(
        CSV_PATH,
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
    print(f"CSV: {CSV_PATH}")