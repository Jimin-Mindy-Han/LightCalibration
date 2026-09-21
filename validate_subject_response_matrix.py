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
from itertools import product


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
    save_dir = "C:/Users/jimin/LightControl/subject_response/validate/"
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
    values = [43, 128, 213]
    for r in values:
        for g in values:
            for b in values:
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
            OUTPUT_CSV_PATH = IMAGE_DIR + image_filename + ".csv"

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

def main(CSV_DIR):
    # M으로 P 추측
    responses = []
    P = np.array(list(product([43, 128, 213], repeat=3)), dtype=float).T

    P = P / 255.0
    print(P.shape)
    print("gt_physical_light: ")
    print(P)

    # gt_skin 불러오기
    values = [43, 128, 213]
    for r in values:
        for g in values:
            for b in values:
                filename = f"R{r}G{g}B{b}I255.csv"
                CSV_PATH = CSV_DIR + filename
                df = pd.read_csv(CSV_PATH)
                response = df[["R", "G", "B"]].iloc[0].to_numpy(dtype=float)
                responses.append(response)
    gt_skin = np.column_stack(responses)
    print("gt_skin:")
    print(gt_skin)

    # probe light로 계산한 response matrix 불러오기
    M = np.loadtxt("subject_response/probe7_response_matrix.csv", delimiter=",")

    #  값 추정
    est_skin = M @ P
    print("estimated_skin: ")
    print(est_skin)

    # pred skin과 gt skin의 error 계산
    diff = est_skin - gt_skin
    error = np.sqrt(np.sum(diff**2, axis=0))
    print(f"skin_error: {error}")
    mean_error = np.mean(error)
    print(f"mean_error: {mean_error}")

    df = pd.DataFrame({
        "physical_R": P[0]*255,
        "physical_G": P[1]*255,
        "physical_B": P[2]*255,

        "est_skin_R": est_skin[0],
        "est_skin_G": est_skin[1],
        "est_skin_B": est_skin[2],

        "gt_skin_R": gt_skin[0],
        "gt_skin_G": gt_skin[1],
        "gt_skin_B": gt_skin[2],

        "rgb_error": error
    })

    df.to_csv(CSV_DIR + "probe7_skin_prediction_result.csv", index=False)


if __name__ == "__main__":
    IMAGE_DIR = "C:/Users/jimin/LightControl/subject_response/validate/"
    JSON_PATH = "C:/Users/jimin/LightControl/subject_response/subject_rois.json"
    # 1. subject response capture
    # CaptureSubjectResponse()
    # 2. RGB 평균값 내기
    # meanRGB(IMAGE_DIR, JSON_PATH)
    # 3. M으로 S 추측 후, pred_S와 gt_S의 차이 계산하기
    main(IMAGE_DIR)
