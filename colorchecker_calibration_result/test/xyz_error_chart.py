import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 설정
# ==========================================

INPUT_DIR = "C:/Users/jimin/LightControl/colorchecker_calibration_result/test/test_error_result/"
OUTPUT_DIR = INPUT_DIR

# ==========================================
# 1. CSV 파일 모두 읽기
# ==========================================

csv_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))

dfs = []

for csv_file in csv_files:
    df = pd.read_csv(csv_file)

    # 필요한 열이 있는 파일만 사용
    required_columns = {
        "virtual_light",
        "baseline_error",
        "calibrated_error"
    }

    if required_columns.issubset(df.columns):
        dfs.append(df)

result_df = pd.concat(dfs, ignore_index=True)

print(result_df)


# ==========================================
# 2. 전체 평균 계산
# ==========================================

mean_baseline = result_df["baseline_error"].mean()
mean_calibrated = result_df["calibrated_error"].mean()

improvement = (
    (mean_baseline - mean_calibrated)
    / mean_baseline
    * 100
)

print("\n===== Overall Result =====")
print(f"Mean Baseline Error   : {mean_baseline:.6f}")
print(f"Mean Calibrated Error : {mean_calibrated:.6f}")
print(f"Improvement           : {improvement:.2f}%")


# ==========================================
# 3. Virtual RGB별 Baseline / Calibrated 비교
# ==========================================

x = np.arange(len(result_df))
width = 0.35

plt.figure(figsize=(12, 6))

plt.bar(
    x - width / 2,
    result_df["baseline_error"],
    width,
    label="Uncalib. Baseline"
)

plt.bar(
    x + width / 2,
    result_df["calibrated_error"],
    width,
    label="Calibrated"
)

plt.xlabel("Virtual RGB")
plt.ylabel("Mean XYZ Error")
plt.title("XYZ Error by Virtual RGB")

plt.xticks(
    x,
    result_df["virtual_light"],
    rotation=45,
    ha="right"
)

plt.legend()
plt.tight_layout()

plt.savefig(
    os.path.join(OUTPUT_DIR, "xyz_error_by_virtual_rgb.png"),
    dpi=300
)

plt.show()


# ==========================================
# 4. 전체 평균 Baseline / Calibrated 비교
# ==========================================

plt.figure(figsize=(5, 5))

plt.bar(
    ["Uncalib. Baseline", "Calibrated"],
    [mean_baseline, mean_calibrated]
)

plt.ylabel("Mean XYZ Error")
plt.title("Overall Mean XYZ Error")

plt.text(
    1.0,
    max(mean_baseline, mean_calibrated) * 1.00,
    f"{improvement:.2f}% reduction",
    ha="center"
)

plt.tight_layout()

plt.savefig(
    os.path.join(OUTPUT_DIR, "overall_mean_xyz_error.png"),
    dpi=300
)

plt.show()