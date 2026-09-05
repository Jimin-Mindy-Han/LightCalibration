import os
import glob
import pandas as pd
import numpy as np


# ==========================================
# 설정
# ==========================================

PHYSICAL_DIR = "colorchecker_calibration_result/physical_colorchecker/XYZ/"

VIRTUAL_DIR = "colorchecker_calibration_result/virtual_colorchecker/XYZ/"

OUTPUT_DIR = "colorchecker_calibration_result/error_result/"



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


virtual_values = [0, 85, 170, 255]
for r in virtual_values:
    for g in virtual_values:
        for b in virtual_values:
            virtual_name = f"R{r}G{g}B{b}_xyz.csv"
            VIRTUAL_CSV = VIRTUAL_DIR + virtual_name

            if not os.path.exists(VIRTUAL_CSV):
                print(f"파일 없음, 건너뜀: {VIRTUAL_CSV}")
                continue
            # ==========================================
            # Physical CSV 전체 순회
            # ==========================================

            physical_files = sorted(
                glob.glob(os.path.join(PHYSICAL_DIR, "*.csv"))
            )

            results = []

            for physical_csv in physical_files:

                physical_name = os.path.splitext(
                    os.path.basename(physical_csv)
                )[0]

                mean_error = calculate_mean_xyz_error(
                    physical_csv,
                    VIRTUAL_CSV
                )

                results.append({
                    "virtual_light": virtual_name,
                    "physical_light": physical_name,
                    "mean_xyz_error": mean_error
                })

                print(
                    f"{virtual_name} vs {physical_name} "
                    f"-> mean XYZ error = {mean_error:.6f}"
                )


            # ==========================================
            # 결과 CSV 저장
            # ==========================================

            result_df = pd.DataFrame(results)
            OUTPUT_CSV = OUTPUT_DIR + "virtual_" + virtual_name

            result_df.to_csv(
                OUTPUT_CSV,
                index=False,
                encoding="utf-8-sig"
            )

            print()
            print("저장 완료")
            print(OUTPUT_CSV)