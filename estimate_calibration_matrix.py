import re
import numpy as np
import pandas as pd


# ==========================================
# 설정
# ==========================================

CSV_PATH = (
    "colorchecker_calibration_result/error_result/best_virtual_physical_pairs.csv"
)

OUTPUT_MATRIX_PATH = (
    "colorchecker_calibration_result/error_result/calibration_matrix.csv"
)


# ==========================================
# 1. RGB 문자열 파싱
# ==========================================

def parse_virtual_rgb(name):
    """
    예:
    R128G255B0
    -> [128, 255, 0]
    """

    match = re.search(
        r"R([0-9.]+)G([0-9.]+)B([0-9.]+)",
        str(name)
    )

    if match is None:
        raise ValueError(f"Virtual RGB 파싱 실패: {name}")

    return [
        float(match.group(1)),
        float(match.group(2)),
        float(match.group(3))
    ]


def parse_physical_rgb(name):
    """
    예:
    R128G255B0I170
    -> [128, 255, 0]

    intensity I는 무시
    """

    match = re.search(
        r"R([0-9.]+)G([0-9.]+)B([0-9.]+)",
        str(name)
    )

    if match is None:
        raise ValueError(f"Physical RGB 파싱 실패: {name}")

    return [
        float(match.group(1)),
        float(match.group(2)),
        float(match.group(3))
    ]


# ==========================================
# 2. CSV 읽기
# ==========================================

df = pd.read_csv(CSV_PATH)


# ==========================================
# 3. RGB 추출
#
# 각 column이 하나의 RGB 샘플이 되도록 구성
#
# P shape = 3 x N
# V shape = 3 x N
# ==========================================

P = np.array(
    [
        parse_physical_rgb(x)
        for x in df["physical_light"]
    ],
    dtype=np.float64
).T

V = np.array(
    [
        parse_virtual_rgb(x)
        for x in df["virtual_light"]
    ],
    dtype=np.float64
).T


# ==========================================
# 4. Physical RGB 0~255 -> 0~1
# ==========================================


print("Physical RGB matrix shape:", P.shape)
print("Virtual RGB matrix shape :", V.shape)


# ==========================================
# 5. Calibration Matrix 계산
#
# V = M @ P
#
# M = V @ pinv(P)
# ==========================================

M = V @ np.linalg.pinv(P)


# ==========================================
# 6. 결과 출력
# ==========================================

print()
print("Calibration Matrix M")
print()

print(M)


# ==========================================
# 7. Matrix 저장
#
# [Rv]   [m11 m12 m13] [Rp]
# [Gv] = [m21 m22 m23] [Gp]
# [Bv]   [m31 m32 m33] [Bp]
# ==========================================

matrix_df = pd.DataFrame(
    M,
    index=[
        "R_virtual",
        "G_virtual",
        "B_virtual"
    ],
    columns=[
        "R_physical",
        "G_physical",
        "B_physical"
    ]
)

matrix_df.to_csv(
    OUTPUT_MATRIX_PATH,
    encoding="utf-8-sig"
)


print()
print("저장 완료")
print(OUTPUT_MATRIX_PATH)


# ==========================================
# 8. Fitting error 확인
# ==========================================

V_pred = M @ P

errors = np.linalg.norm(
    V_pred - V,
    axis=0
)

print()
print("Mean RGB fitting error:")
print(errors.mean()/255)