# subject specific 조명 반응 matrix 추정하기
import os
import cv2
import obsws_python as obs
import requests
from urllib.parse import quote
import json
import time
import numpy as np
import glob
import csv
import pandas as pd

# 1. 사진 촬영
# 2. 사진에서 피부 일부 crop
# 3. 해당 위치의 RGB 각각 평균내기(sRGB->LinearRGB)
# 4. P = [L_p1, L_p2, ..., L_pn], S = [C_M1, C_M2, ..., C_Mn], 단, 여기에서 L_pi는 physical light의 RGB 값을 의미하는 것이고, C_Mi는 피부의 색깔 RGB를 의미
# 5. M = SP+ 계산해서 Output (P+ = P^T(P(P^T))^(-1))

IMAGE_PATH = "C:/Users/jimin/LightControl/subject_response/R255G255B255I255.png"
JSON_PATH = "C:/Users/jimin/LightControl/subject_response/subject_rois.json"
OUTPUT_CSV_DIR = "C:/Users/jimin/LightControl/subject_response/"
IMAGE_DIR = "C:/Users/jimin/LightControl/subject_response/"

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
    save_dir = "C:/Users/jimin/LightControl/subject_response/"
    save_path = save_dir + filename

    client.save_source_screenshot(
        source_name,
        "png",
        save_path,
        1920,
        1080,
        100
    )

    print("saved:", save_path)

def CaptureSubjectResponse():
    # 1. 사진 촬영
    values = [{"r":255, "g":0, "b":0}, {"r":0, "g":255, "b":0}, {"r":0, "g":0, "b":255}]
    for value in values:
        r = value["r"]
        g = value["g"]
        b = value["b"]
        light_value = {
            "r": r,
            "g": g,
            "b": b,
        }
        filename = f"R{r}G{g}B{b}I255.png"
        print(light_value)
        dmx_remote_control(light_value)
        time.sleep(3)
        obsCapture(filename)

def SelectROI(IMAGE_PATH, JSON_PATH):
    # 2. 사진에서 피부 일부 crop


    png = cv2.imread(
        IMAGE_PATH,
        cv2.IMREAD_COLOR
    )

    if png is None:
        raise RuntimeError(f"이미지를 읽을 수 없습니다: {IMAGE_PATH}")

    display = png.copy()

    rois = []

    print(f"패치를 드래그하세요.", end="")

    x, y, w, h = cv2.selectROI(
        "Select ColorChecker Patch",
        display,
        showCrosshair=True,
        fromCenter=False
    )

    if w == 0 or h == 0:
        cv2.destroyAllWindows()
        raise RuntimeError(
            f"패치 ROI 선택이 취소되었습니다."
        )

    roi_info = {
        "x_min": int(x),
        "y_min": int(y),
        "x_max": int(x + w - 1),
        "y_max": int(y + h - 1),

        "width": int(w),
        "height": int(h)
    }

    rois.append(roi_info)

    cv2.destroyAllWindows()

    output = {
        "coordinate_system": {
            "description": "Subject Response Patch",
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

        print()
        print("ROI 저장 완료")
        print(f"JSON: {JSON_PATH}")

def meanRGB(IMAGE_DIR, JSON_PATH):
    # 3. 해당 위치의 RGB 각각 평균내기(sRGB->LinearRGB)
    subject_images = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")))
    for subject_image in subject_images:
        png_bgr = cv2.imread(subject_image, cv2.IMREAD_COLOR)

        if png_bgr is None:
            raise RuntimeError(f"이미지를 읽을 수 없습니다: {subject_image}")

        # OpenCV BGR -> RGB
        png_rgb = cv2.cvtColor(png_bgr, cv2.COLOR_BGR2RGB)

        # 0~255 -> 0~1
        srgb = png_rgb.astype(np.float64) / 255.0

        # ==========================================
        # 2. sRGB -> Linear RGB
        # inverse sRGB transfer function
        # ==========================================

        linear_rgb = np.where(
            srgb <= 0.04045,
            srgb / 12.92,
            ((srgb + 0.055) / 1.055) ** 2.4
        )

        with open(JSON_PATH, "r", encoding="utf-8") as f:
            roi_data = json.load(f)

        results = []
        for patch in roi_data["patches"]:
            x_min = patch["x_min"]
            y_min = patch["y_min"]
            x_max = patch["x_max"]
            y_max = patch["y_max"]

            roi = linear_rgb[
                  y_min:y_max + 1,
                  x_min:x_max + 1
                  ]

            # ROI의 평균 linear RGB
            mean_rgb = np.mean(roi, axis=(0, 1))

            result = {
                "R": mean_rgb[0],
                "G": mean_rgb[1],
                "B": mean_rgb[2],
            }

            results.append(result)

            print(
                f'R={mean_rgb[0]:.6f}, '
                f'G={mean_rgb[1]:.6f}, '
                f'B={mean_rgb[2]:.6f}'
            )

            image_filename = os.path.splitext(os.path.basename(subject_image))[0]
            OUTPUT_CSV_PATH = OUTPUT_CSV_DIR + image_filename + ".csv"
            
            with open(
                    OUTPUT_CSV_PATH,
                    "w",
                    newline="",
                    encoding="utf-8-sig"
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "R",
                        "G",
                        "B"
                    ]
                )

                writer.writeheader()
                writer.writerows(results)

            print()
            print(f"CSV: {OUTPUT_CSV_PATH}")

def EstimateSubjectResponse(CSV_DIR):
    # 4. P = [L_p1, L_p2, ..., L_pn], S = [C_M1, C_M2, ..., C_Mn], 단, 여기에서 L_pi는 physical light의 RGB 값을 의미하는 것이고, C_Mi는 피부의 색깔 RGB를 의미
    # 5. M = SP+ 계산해서 Output (P+ = P^T(P(P^T))^(-1))
    P = np.array([
        [255, 0, 0, 255, 255, 0, 255],  # R
        [0, 255, 0, 255, 0, 255, 255],  # G
        [0, 0, 255, 0, 255, 255, 255]  # B
    ], dtype=float)

    P = P / 255.0

    responses = []
    values = [{"r": 255, "g": 0, "b": 0}, {"r": 0, "g": 255, "b": 0}, {"r": 0, "g": 0, "b": 255}, {"r": 255, "g": 255, "b": 0}, {"r": 255, "g": 0, "b": 255}, {"r": 0, "g": 255, "b": 255}, {"r": 255, "g": 255, "b": 255}]
    for value in values:
        r = value["r"]
        g = value["g"]
        b = value["b"]
        filename = f"R{r}G{g}B{b}I255.csv"
        CSV_PATH = CSV_DIR + filename
        df = pd.read_csv(CSV_PATH)
        response = df[["R", "G", "B"]].iloc[0].to_numpy(dtype=float)
        responses.append(response)
    S = np.column_stack(responses)
    print(S)
    M = S @ np.linalg.pinv(P)
    print(M)

    np.savetxt("subject_response/probe7_response_matrix.csv", M, delimiter=",")


if __name__ == "__main__":
    EstimateSubjectResponse(OUTPUT_CSV_DIR)
    # meanRGB(IMAGE_DIR, JSON_PATH)