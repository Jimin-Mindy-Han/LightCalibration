import os
import glob
import pandas as pd
import numpy as np


# ==========================================
# 설정
# ==========================================

BASELINE_DIR = "/colorchecker_calibration_result/test/baseline/XYZ/"
VIRTUAL_DIR = "/colorchecker_calibration_result/test/virtual_colorchecker/XYZ/"

OUTPUT_DIR = "C:/Users/jimin/LightControl/colorchecker_calibration_result/test/test_error_result/"



# ==========================================
# XYZ Euclidean error 계산 함수
# ==========================================

def calculate_mean_xyz_error(physical_csv, virtual_csv):

    physical_df = pd.read_csv(physical_csv)
    virtual_df = pd.read_csv(virtual_csv)

    # 같은 patch끼리 맞춤
    merged = pd.merge(
        physical_df,
        virtual_df,
        on=["row", "column", "patch"],
        suffixes=("_physical", "_virtual")
    )

    if len(merged) != 24:
        raise RuntimeError(
            f"패치 개수가 24개가 아닙니다: {physical_csv} "
            f"(matched patches = {len(merged)})"
        )

    # 패치별 XYZ Euclidean distance
    error = np.sqrt(
        (merged["X_physical"] - merged["X_virtual"]) ** 2
        + (merged["Y_physical"] - merged["Y_virtual"]) ** 2
        + (merged["Z_physical"] - merged["Z_virtual"]) ** 2
    )

    # 24개 patch 평균
    return float(error.mean())

virtual_files = sorted(glob.glob(os.path.join(VIRTUAL_DIR, "*.csv")))

for virtual_file in virtual_files:
    filename = xyz_filename = os.path.splitext(os.path.basename(virtual_file))[0]
    results = []

    virtual_csv = os.path.join(
        VIRTUAL_DIR,
        filename + ".csv"
    )

    physical_csv = os.path.join(
        BASELINE_DIR,
        filename + ".csv"
    )

    mean_error = calculate_mean_xyz_error(
        physical_csv,
        virtual_csv
    )

    results.append({
        "virtual_light": filename,
        "physical_light": filename,
        "mean_xyz_error": mean_error
    })

    print(
        f"{filename} "
        f"-> mean XYZ error = {mean_error:.6f}"
    )

    # ==========================================
    # 결과 CSV 저장
    # ==========================================

    result_df = pd.DataFrame(results)
    OUTPUT_CSV = OUTPUT_DIR + "virtual_" + filename + ".csv"

    result_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("저장 완료")
    print(OUTPUT_CSV)



