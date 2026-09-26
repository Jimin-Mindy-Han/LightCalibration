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


def calculate_roi_mean_rgb(image_path, roi):

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(image_path)

    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    x, y, w, h = roi

    crop = image[
        y:y + h,
        x:x + w
    ]

    mean_rgb = crop.mean(axis=(0, 1))

    return mean_rgb

def estimate_physical_light_from_skin(
    skin_rgb,
    response_matrix_path="./probe7_response_matrix.csv"
):
    # response matrix 불러오기
    matrix_df = pd.read_csv(
        response_matrix_path,
        header=None
    )

    M = matrix_df.to_numpy(dtype=float)

    # target skin RGB
    S = np.array(
        skin_rgb,
        dtype=float
    )

    # S = M P
    # -> P = M+ S
    M_pinv = np.linalg.pinv(M)

    physical_rgb = M_pinv @ S

    # 반올림 + 0~255 제한
    physical_rgb = np.rint(physical_rgb).astype(int)
    physical_rgb = np.clip(
        physical_rgb,
        0,
        255
    )

    return physical_rgb

if __name__ == "__main__":
    image_path = "./gt/physical_colorchecker/GT_R25G209B24.png"
    roi = (987, 166, 140, 62)
    gt_rgb = calculate_roi_mean_rgb(image_path, roi)
    gt_rgb = np.rint(gt_rgb).astype(int)

    print("GT skin RGB:", gt_rgb)

    physical_light = estimate_physical_light_from_skin(gt_rgb, )
    print("Estimated physical light:", physical_light)