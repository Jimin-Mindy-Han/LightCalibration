import os
import glob
import pandas as pd


# ==========================================
# 설정
# ==========================================

INPUT_DIR = (
    "colorchecker_calibration_result/error_result/"
)

OUTPUT_CSV = (
    "colorchecker_calibration_result/error_result/best_virtual_physical_pairs.csv"
)


# ==========================================
# 1. top3 파일 전체 찾기
# ==========================================

top3_files = sorted(
    glob.glob(
        os.path.join(
            INPUT_DIR,
            "top3_virtual_*_xyz.csv"
        )
    )
)


results = []


# ==========================================
# 2. 각 파일에서 최소 error 1개 추출
# ==========================================

for csv_path in top3_files:

    df = pd.read_csv(csv_path)

    # mean_xyz_error가 가장 작은 행
    best_row = df.loc[
        df["mean_xyz_error"].idxmin()
    ]

    virtual_light = str(
        best_row["virtual_light"]
    )

    # 뒤의 "_xyz.csv" 제거
    virtual_light = virtual_light.replace(
        "_xyz.csv",
        ""
    )

    results.append({
        "virtual_light": virtual_light,
        "physical_light": best_row["physical_light"],
        "mean_error": best_row["mean_xyz_error"]
    })


# ==========================================
# 3. 하나의 CSV로 저장
# ==========================================

result_df = pd.DataFrame(
    results,
    columns=[
        "virtual_light",
        "physical_light",
        "mean_error"
    ]
)

result_df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# 결과 출력
# ==========================================

print(result_df)

print()
print("저장 완료")
print(OUTPUT_CSV)