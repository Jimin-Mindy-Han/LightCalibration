import pandas as pd
import glob
import os
import numpy as np


# ==========================================
# 설정
# ==========================================

BASELINE_DIR = "/colorchecker_calibration_result/test/test_error_result/baseline_error/"

CALIBRATED_DIR = "/colorchecker_calibration_result/test/test_error_result/calibrated_error/"

OUTPUT_DIR = "C:/Users/jimin/LightControl/colorchecker_calibration_result/test/test_error_result/"

results = []
files = sorted(glob.glob(os.path.join(CALIBRATED_DIR, "*.csv")))
for file in files:
    filename = os.path.splitext(os.path.basename(file))[0]
    CALIBRATED_CSV = file
    # ==========================================
    # 1. CSV 읽기
    # ==========================================

    calibrated_df = pd.read_csv(CALIBRATED_CSV)

    baseline_files = sorted(glob.glob(os.path.join(BASELINE_DIR, "*.csv")))
    for baseline_file in baseline_files:
        baseline_filename = os.path.splitext(os.path.basename(baseline_file))[0]
        if filename == baseline_filename:
            print(baseline_filename)
            baseline_df = pd.read_csv(baseline_file)
            # ==========================================
            # 2. 필요한 column만 사용
            # ==========================================

            baseline_df = baseline_df[
                ["virtual_light", "mean_xyz_error"]
            ].rename(
                columns={
                    "mean_xyz_error": "baseline_error"
                }
            )


            calibrated_df = calibrated_df[
                ["virtual_light", "mean_xyz_error"]
            ].rename(
                columns={
                    "mean_xyz_error": "calibrated_error"
                }
            )


            # ==========================================
            # 3. virtual_light 기준으로 병합
            # ==========================================

            result_df = pd.merge(
                baseline_df,
                calibrated_df,
                on="virtual_light",
                how="inner"
            )


            # ==========================================
            # 4. Improvement 계산
            #
            # 양수  -> calibration 후 개선
            # 0     -> 변화 없음
            # 음수  -> calibration 후 악화
            # ==========================================

            result_df["improvement"] = (
                (
                    result_df["baseline_error"]
                    - result_df["calibrated_error"]
                )
                / result_df["baseline_error"]
                * 100.0
            )


            # ==========================================
            # 5. CSV 저장
            # ==========================================
            OUTPUT_CSV = OUTPUT_DIR + filename + ".csv"
            result_df.to_csv(
                OUTPUT_CSV,
                index=False,
                encoding="utf-8-sig"
            )

            results.append(result_df["improvement"])

            print(result_df)
            print()
            print("저장 완료")
            print(OUTPUT_CSV)
print(np.mean(results))