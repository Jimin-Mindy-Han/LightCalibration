import os
import glob
import pandas as pd
import numpy as np
import time
import obsws_python as obs
import requests
from urllib.parse import quote
import cv2

# ==========================================
# 설정
# ==========================================

PHYSICAL_DIR = "./gt/physical_colorchecker/XYZ/"

VIRTUAL_DIR = "./gt/virtual_colorchecker/XYZ/"



# ==========================================
# XYZ error 계산
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

    # patch별 XYZ Euclidean error
    errors = np.sqrt(
        (merged["X_physical"] - merged["X_virtual"]) ** 2
        + (merged["Y_physical"] - merged["Y_virtual"]) ** 2
        + (merged["Z_physical"] - merged["Z_virtual"]) ** 2
    )

    return errors.mean()

def sort_min_error_virtual_light(physical_dir, virtual_dir):
    physical_files = glob.glob(physical_dir + "*.csv")

    for physical_csv in physical_files:
        # ==========================================
        # 모든 virtual light와 비교
        # ==========================================

        results = []

        virtual_files = glob.glob(os.path.join(virtual_dir, "*.csv"))

        for virtual_csv in virtual_files:
            mean_error = calculate_mean_xyz_error(
                physical_csv,
                virtual_csv
            )

            filename = os.path.basename(virtual_csv)

            results.append({
                "virtual_light": filename,
                "mean_xyz_error": mean_error
            })

        # ==========================================
        # error가 작은 순서대로 정렬
        # ==========================================

        results_df = pd.DataFrame(results)

        results_df = results_df.sort_values(
            "mean_xyz_error",
            ascending=True
        ).reset_index(drop=True)

        # ==========================================
        # 가장 가까운 virtual light
        # ==========================================

        best = results_df.iloc[0]

        print("Best virtual light:")
        print(best["virtual_light"])

        print("Mean XYZ error:")
        print(best["mean_xyz_error"])

        # # 전체 결과 확인
        # print("\nAll results:")
        # print(results_df)

        # ==========================================
        # CSV 저장
        # ==========================================

        gt_filename = os.path.splitext(os.path.basename(physical_csv))[0]
        OUTPUT_PATH = f"gt/colorchecker_based_reconstruction/GT_{gt_filename}.csv"

        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        results_df.to_csv(
            OUTPUT_PATH,
            index=False
        )

        print(f"\nSaved to: {OUTPUT_PATH}")

def find_mean_error_virtual_light(gt_dir):
    # ==========================================
    # 각 GT에서 최소 error virtual light 추출
    # ==========================================

    results = []

    gt_files = glob.glob(os.path.join(gt_dir, "GT_*.csv"))

    for gt_csv in gt_files:
        df = pd.read_csv(gt_csv)

        # mean_xyz_error가 가장 작은 행
        best = df.loc[df["mean_xyz_error"].idxmin()]

        # GT physical light는 파일명에서 추출
        gt_physical_light = os.path.splitext(
            os.path.basename(gt_csv)
        )[0].replace("GT_", "")

        # virtual light의 .csv 제거
        virtual_light = os.path.splitext(
            best["virtual_light"]
        )[0]

        results.append({
            "gt_physical_light": gt_physical_light,
            "virtual_light": virtual_light,
            "mean_xyz_error": best["mean_xyz_error"],
        })

    # ==========================================
    # 하나의 CSV로 저장
    # ==========================================

    results_df = pd.DataFrame(results)
    OUTPUT_PATH = "./gt/colorchecker_based_reconstruction/best_virtual_light_pairs.csv"

    results_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(results_df)
    print(f"\nSaved to: {OUTPUT_PATH}")

import os
import re
import pandas as pd
import numpy as np


def estimate_physical_light_from_virtual_light(best_virtual_light_pairs_path):

    # ==========================================
    # CCM 경로
    # 현재 코드 파일의 상위 폴더 기준
    # ==========================================

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)

    ccm_path = os.path.join(
        parent_dir,
        "colorchecker_calibration_result/error_result/calibration_matrix.csv"
    )

    df = pd.read_csv(best_virtual_light_pairs_path)

    # ==========================================
    # CCM 불러오기
    # ==========================================

    ccm_df = pd.read_csv(
        ccm_path,
        index_col=0
    )

    M = ccm_df.to_numpy(dtype=float)

    estimated_physical_light = []

    for virtual_light in df["virtual_light"]:
        # ==========================================
        # Virtual light 이름에서 RGB 추출
        # 예: R128G213B43
        # ==========================================

        match = re.search(
            r"R(\d+)G(\d+)B(\d+)",
            virtual_light
        )

        if match is None:
            raise ValueError(f"Invalid virtual light format: {virtual_light}")

        virtual_rgb = np.array([
            float(match.group(1)),
            float(match.group(2)),
            float(match.group(3))
        ])


        # ==========================================
        # 0~1 범위로 정규화
        # ==========================================

        virtual_rgb = virtual_rgb / 255.0


        # ==========================================
        # v = M p
        # → p = M+ v
        # ==========================================

        M_pinv = np.linalg.pinv(M)

        estimated_rgb = M_pinv @ virtual_rgb


        # ==========================================
        # 다시 0~255 범위로 변환
        # ==========================================

        estimated_rgb = estimated_rgb * 255.0
        estimated_rgb = np.rint(estimated_rgb).astype(int)

        # 조명 입력 범위를 벗어나는 값 방지
        estimated_rgb = np.clip(
            estimated_rgb,
            0,
            255
        )
        R, G, B = map(int, estimated_rgb)

        print("Virtual light: ", virtual_light)
        print("Estimated physical RGB:", estimated_rgb)

        estimated_physical_light.append(f"R{R}G{G}B{B}")

    df["estimated_physical_light"] = estimated_physical_light

    # 기존 CSV에 덮어쓰기
    df.to_csv(
        best_virtual_light_pairs_path,
        index=False
    )

    print(df)

HOST = "localhost"
PORT = 4455
PASSWORD = "000000"

def dmx_remote_control(lighting_condition: dict):
    BASE = "http://127.0.0.1:30010"
    preset = quote("NewRemoteControlPreset", safe="")
    prop = quote("Linear Color Input", safe="")
    # prop2 = quote("Intensity Input", safe="")
    prop_dmx_enabled = quote("DmxEnabled", safe="")

    payload = {
        "PropertyValue": {
            "R": lighting_condition["r"]/255,
            "G": lighting_condition["g"]/255,
            "B": lighting_condition["b"]/255,
            "A": 1.5 # 실제 쓰이지는 않는 값
        },
        "GenerateTransaction": True
    }

    # payload2 = {
    #     "PropertyValue": lighting_condition["i"]*20/255,
    #     "GenerateTransaction": True
    # }

    payload_dmx_enabled = {
        "PropertyValue": True,
        "GenerateTransaction": True
    }

    url = f"{BASE}/remote/preset/{preset}/property/{prop}"
    # url2 = f"{BASE}/remote/preset/{preset}/property/{prop2}"
    dmx_flag_url = f"{BASE}/remote/preset/{preset}/property/{prop_dmx_enabled}"

    r = requests.put(url, json=payload)
    dmx_flag_r = requests.put(dmx_flag_url, json=payload_dmx_enabled)
    # intensity_r = requests.put(url2, json=payload2)

    print(r.status_code)
    print(dmx_flag_r.status_code)
    # print(intensity_r.status_code)
    print(r.text)
    print(dmx_flag_r.text)
    # print(intensity_r.text)

def obsCapture(filename):
    client = obs.ReqClient(
        host=HOST,
        port=PORT,
        password=PASSWORD
    )

    source_name = "sony a7r4"
    save_dir = "./gt/estimated_physical_light_capture/"
    save_path = os.path.abspath(os.path.join(save_dir, filename))

    client.save_source_screenshot(
        source_name,
        "png",
        save_path,
        1920,
        1080,
        100
    )

    print("saved:", save_path)

def CaptureSubjectResponse(estimated_physical_light_pairs_path):
    df = pd.read_csv(estimated_physical_light_pairs_path)

    for _, row in df.iterrows():

        gt_light = row["gt_physical_light"]
        virtual_light = row["virtual_light"]
        estimated_light = row["estimated_physical_light"]

        match = re.search(
            r"R(\d+)G(\d+)B(\d+)",
            estimated_light
        )

        if match is None:
            raise ValueError(
                f"Invalid physical light format: {estimated_light}"
            )


        R = int(match.group(1))
        G = int(match.group(2))
        B = int(match.group(3))

        light_value = {
            "r": R,
            "g": G,
            "b": B,
        }

        filename = (
            f"GT_{gt_light}_"
            f"V_{virtual_light}_"
            f"P_{estimated_light}.png"
        )


        print(light_value)
        print(filename)

        dmx_remote_control(light_value)
        time.sleep(3)
        obsCapture(filename)

# ==========================================
# sRGB -> Linear RGB
# ==========================================

def srgb_to_linear(rgb):

    rgb = rgb / 255.0

    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4
    )

# ==========================================
# Linear RGB -> XYZ (D65)
# ==========================================

def linear_rgb_to_xyz(rgb_linear):

    matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])

    return matrix @ rgb_linear

# ==========================================
# ROI의 평균 XYZ 계산
# ==========================================

def calculate_roi_xyz(image_path, roi):

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(image_path)

    # OpenCV BGR -> RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    x, y, w, h = roi

    crop = image[
           y:y + h,
           x:x + w
           ].astype(np.float64)

    # 1. ROI의 각 픽셀을 sRGB -> linear RGB
    linear_crop = srgb_to_linear(crop)

    # 2. linear RGB 상태에서 ROI 평균 RGB
    mean_rgb = linear_crop.mean(axis=(0, 1))

    # 3. mean linear RGB -> XYZ
    xyz = linear_rgb_to_xyz(mean_rgb)

    return xyz

# ==========================================
# GT 이미지 찾기
# ==========================================

def find_gt_image(gt_dir, gt_light):

    image_files = []

    for ext in ["*.png"]:
        image_files.extend(
            glob.glob(os.path.join(gt_dir, ext))
        )

    for path in image_files:

        filename = os.path.basename(path)

        if gt_light in filename:
            return path

    raise FileNotFoundError(
        f"GT image not found: {gt_light}"
    )

# ==========================================
# XYZ -> Lab (D65)
# ==========================================

def xyz_to_lab(xyz):

    # D65 white point
    Xn = 0.95047
    Yn = 1.00000
    Zn = 1.08883

    x = xyz[0] / Xn
    y = xyz[1] / Yn
    z = xyz[2] / Zn

    delta = 6 / 29

    def f(t):
        if t > delta ** 3:
            return t ** (1 / 3)
        else:
            return t / (3 * delta ** 2) + 4 / 29

    fx = f(x)
    fy = f(y)
    fz = f(z)

    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)

    return np.array([L, a, b])


# ==========================================
# Delta E 1976
# ==========================================

def calculate_delta_e(lab1, lab2):

    return np.linalg.norm(
        lab1 - lab2
    )

def main(sample_image_path, gt_dir, estimated_dir, output_csv_path):
    # ------------------------------------------
    # ROI 선택
    # ------------------------------------------

    sample = cv2.imread(sample_image_path)

    if sample is None:
        raise FileNotFoundError(sample_image_path)

    roi = cv2.selectROI(
        "Select Skin ROI",
        sample,
        showCrosshair=True,
        fromCenter=False
    )

    cv2.destroyAllWindows()

    roi = tuple(map(int, roi))

    print("Selected ROI:", roi)

    # ------------------------------------------
    # estimated 이미지 탐색
    # ------------------------------------------

    estimated_files = glob.glob(
        os.path.join(
            estimated_dir,
            "*.png"
        )
    )

    results = []

    for estimated_path in estimated_files:

        filename = os.path.basename(
            estimated_path
        )

        # 예:
        # GT_R25G209B24_V_R128G213B43_P_R94G136B255.png

        gt_match = re.search(
            r"GT_(R\d+G\d+B\d+)",
            filename
        )

        estimated_match = re.search(
            r"_P_(R\d+G\d+B\d+)",
            filename
        )

        if gt_match is None or estimated_match is None:
            print("Skip:", filename)
            continue

        gt_light = gt_match.group(1)
        estimated_light = estimated_match.group(1)

        # GT 이미지 찾기
        gt_path = find_gt_image(
            gt_dir,
            gt_light
        )

        # XYZ 계산
        gt_xyz = calculate_roi_xyz(
            gt_path,
            roi
        )

        estimated_xyz = calculate_roi_xyz(
            estimated_path,
            roi
        )

        # ------------------------------------------
        # XYZ Euclidean error
        # ------------------------------------------

        xyz_error = np.linalg.norm(
            gt_xyz - estimated_xyz
        )

        # ------------------------------------------
        # XYZ -> Lab
        # ------------------------------------------

        gt_lab = xyz_to_lab(
            gt_xyz
        )

        estimated_lab = xyz_to_lab(
            estimated_xyz
        )

        # ------------------------------------------
        # Delta E
        # ------------------------------------------

        delta_e = calculate_delta_e(
            gt_lab,
            estimated_lab
        )

        results.append({
            "gt_light": gt_light,
            "estimated_light": estimated_light,
            "xyz_error": xyz_error,
            "delta_e": delta_e
        })

    # ------------------------------------------
    # 결과 저장
    # ------------------------------------------

    results_df = pd.DataFrame(results)

    mean_xyz_error = results_df[
        "xyz_error"
    ].mean()

    mean_delta_e = results_df[
        "delta_e"
    ].mean()

    mean_row = pd.DataFrame([{
        "gt_light": "MEAN",
        "estimated_light": "",
        "xyz_error": mean_xyz_error,
        "delta_e": mean_delta_e
    }])

    results_df = pd.concat(
        [results_df, mean_row],
        ignore_index=True
    )

    results_df.to_csv(
        output_csv_path,
        index=False
    )

    print(results_df)
    print("\nMean XYZ Error:", mean_xyz_error)
    print("Mean Delta E:", mean_delta_e)
    print("Saved:", output_csv_path)

if __name__ == "__main__":

    # 각 GT light에 대해 error가 최소인 virtual light를 찾아서 저장
    # GT_DIR = "./gt/colorchecker_based_reconstruction/"
    # find_mean_error_virtual_light(GT_DIR)

    # 위에서 구한 virtual light에 대해 CCM으로 대응하는 physical light 찾아서 pairs 파일 수정하며 저장
    best_virtual_light_pairs_path = "./gt/colorchecker_based_reconstruction/best_virtual_light_pairs.csv"
    # estimate_physical_light_from_virtual_light(best_virtual_light_pairs_path)

    # 각 pairs에 대해서 촬영 loop
    # CaptureSubjectResponse(best_virtual_light_pairs_path)

    # GT의 skin 과 복원된 skin ROI의 RGB error 비교 및 저장
    sample_image_path = "./gt/estimated_physical_light_capture/GT_R180G174B116_V_R128G128B128_P_R180G174B116.png"
    gt_dir = "./gt/physical_colorchecker/"
    estimated_dir = "./gt/estimated_physical_light_capture/"
    output_csv = "./gt/skin_appearance_reconstruction_error.csv"
    main(sample_image_path, gt_dir, estimated_dir, output_csv)