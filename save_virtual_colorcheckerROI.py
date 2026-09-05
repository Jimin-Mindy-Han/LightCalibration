import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

import cv2
import numpy as np
import json


# ==========================================
# 설정
# ==========================================

IMAGE_PATH = "colorchecker_calibration_result/virtual_colorchecker/R85G0B85.hdr"  # .hdr 파일 경로

JSON_PATH = "colorchecker_calibration_result/virtual_colorchecker/colorchecker_rois.json"


# ==========================================
# 1. HDR / EXR 읽기
# ==========================================

hdr = cv2.imread(
    IMAGE_PATH,
    cv2.IMREAD_UNCHANGED
)

if hdr is None:
    raise RuntimeError(f"이미지를 읽을 수 없습니다: {IMAGE_PATH}")

print("HDR shape:", hdr.shape)
print("HDR dtype:", hdr.dtype)
print("HDR min/max:", np.min(hdr), np.max(hdr))


# ==========================================
# 2. ROI 선택용 8-bit 이미지 생성
#
# 중요:
# 원본 hdr 값은 건드리지 않고,
# 화면 표시용 이미지만 변환합니다.
# ==========================================

display = hdr.copy()

# OpenCV는 BGR 순서
# 너무 밝은 HDR 값을 보기 좋게 간단히 tone mapping
display = np.maximum(display, 0.0)

# Reinhard 형태의 간단한 display mapping
display = display / (1.0 + display)

# linear -> sRGB에 가까운 display gamma
display = np.power(display, 1.0 / 2.2)

display = np.clip(display * 255.0, 0, 255).astype(np.uint8)


# ==========================================
# 3. ColorChecker 24개 ROI 선택
#
# 좌표 체계:
#
# (1,1) ........ (1,6)
#
# (2,1) ........ (2,6)
#
# (3,1) ........ (3,6)
#
# (4,1) ........ (4,6)
#
# ==========================================

rois = []

for row in range(1, 5):
    for col in range(1, 7):

        patch_name = f"({row}, {col})"

        # 네 모서리에 설명 추가
        position_description = ""

        if row == 1 and col == 1:
            position_description = "좌상단"
        elif row == 1 and col == 6:
            position_description = "우상단"
        elif row == 4 and col == 1:
            position_description = "좌하단"
        elif row == 4 and col == 6:
            position_description = "우하단"

        print()
        print(f"패치 {patch_name}를 드래그하세요.", end="")

        if position_description:
            print(f"  <-- {position_description}")
        else:
            print()

        # ROI 선택
        # 반환값: x, y, width, height
        x, y, w, h = cv2.selectROI(
            "Select ColorChecker Patch",
            display,
            showCrosshair=True,
            fromCenter=False
        )

        if w == 0 or h == 0:
            cv2.destroyAllWindows()
            raise RuntimeError(
                f"패치 {patch_name} ROI 선택이 취소되었습니다."
            )

        roi_info = {
            "row": row,
            "column": col,
            "patch": patch_name,

            "position_description": position_description,

            "x_min": int(x),
            "y_min": int(y),
            "x_max": int(x + w - 1),
            "y_max": int(y + h - 1),

            "width": int(w),
            "height": int(h)
        }

        rois.append(roi_info)


cv2.destroyAllWindows()


# ==========================================
# 4. JSON 저장
# ==========================================

output = {
    "coordinate_system": {
        "description": "ColorChecker: 4 rows x 6 columns",
        "top_left": "(1, 1) = 좌상단",
        "top_right": "(1, 6) = 우상단",
        "bottom_left": "(4, 1) = 좌하단",
        "bottom_right": "(4, 6) = 우하단"
    },

    "image": {
        "path": IMAGE_PATH,
        "width": int(hdr.shape[1]),
        "height": int(hdr.shape[0])
    },

    "patches": rois
}


with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=4
    )


# ==========================================
# 결과 출력
# ==========================================

print()
print("ROI 저장 완료")
print(f"JSON: {JSON_PATH}")

print()
print("Corner 확인:")
print("(1, 1) = 좌상단")
print("(1, 6) = 우상단")
print("(4, 1) = 좌하단")
print("(4, 6) = 우하단")