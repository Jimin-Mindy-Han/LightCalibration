import cv2
import numpy as np
import json


# ==========================================
# 설정
# ==========================================

IMAGE_PATH = "colorchecker_calibration_result/physical_colorchecker/R0G85B255I255.png"

JSON_PATH = "colorchecker_calibration_result/physical_colorchecker/colorchecker_rois.json"


# ==========================================
# 1. PNG 읽기
# ==========================================

png = cv2.imread(
    IMAGE_PATH,
    cv2.IMREAD_COLOR
)

if png is None:
    raise RuntimeError(f"이미지를 읽을 수 없습니다: {IMAGE_PATH}")

print("PNG shape:", png.shape)
print("PNG dtype:", png.dtype)
print("PNG min/max:", np.min(png), np.max(png))


# ==========================================
# 2. ROI 선택용 이미지
#
# PNG는 이미 8-bit sRGB 이미지이므로
# 별도의 tone mapping이나 gamma 변환 없이
# 그대로 표시합니다.
#
# OpenCV 내부 채널 순서는 BGR입니다.
# ==========================================

display = png.copy()


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
        "width": int(png.shape[1]),
        "height": int(png.shape[0])
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