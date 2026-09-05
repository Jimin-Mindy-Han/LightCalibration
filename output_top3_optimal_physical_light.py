import os
import pandas as pd


# ==========================================
# 설정
# ==========================================

VIRTUAL_DIR = (
    "colorchecker_calibration_result/error_result/"
)

OUTPUT_DIR = (
    "colorchecker_calibration_result/error_result/"
)

virtual_values = [0, 85, 170, 255]
for r in virtual_values:
    for g in virtual_values:
        for b in virtual_values:
            filename = f"virtual_R{r}G{g}B{b}_xyz.csv"
            VIRTUAL_PATH = VIRTUAL_DIR + filename

            if not os.path.exists(VIRTUAL_PATH):
                print(f"파일 없음, 건너뜀: {VIRTUAL_PATH}")
                continue
            # ==========================================
            # 1. CSV 읽기
            # ==========================================

            df = pd.read_csv(VIRTUAL_PATH)


            # ==========================================
            # 2. mean_xyz_error 기준 상위 3개 추출
            # ==========================================

            top3 = (
                df.sort_values(
                    by="mean_xyz_error",
                    ascending=True
                )
                .head(3)
                .copy()
            )


            # ==========================================
            # 3. 필요한 column만 선택
            # ==========================================

            result = top3[
                [
                    "virtual_light",
                    "physical_light",
                    "mean_xyz_error"
                ]
            ]


            # ==========================================
            # 4. 출력
            # ==========================================

            print("Top 3 physical light conditions:")
            print()

            for _, row in result.iterrows():
                print(
                    f'Virtual: {row["virtual_light"]}, '
                    f'Physical: {row["physical_light"]}, '
                    f'Error: {row["mean_xyz_error"]:.6f}'
                )


            # ==========================================
            # 5. CSV 저장
            # ==========================================
            output_filename = f"top3_virtual_R{r}G{g}B{b}_xyz.csv"
            OUTPUT_PATH = OUTPUT_DIR + output_filename
            result.to_csv(
                OUTPUT_PATH,
                index=False,
                encoding="utf-8-sig"
            )

            print()
            print("저장 완료")
            print(OUTPUT_PATH)