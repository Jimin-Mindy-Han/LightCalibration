import numpy as np
import pandas as pd
from urllib.parse import quote
import requests
import time
import obsws_python as obs

HOST = "localhost"
PORT = 4455
PASSWORD = "000000"

# ==========================================
# 설정
# ==========================================

MATRIX_CSV_PATH = "colorchecker_calibration_result/error_result/calibration_matrix.csv"


def calculate_pseudo_inv_matrix(MATRIX_CSV_PATH):
    # ==========================================
    # 1. Calibration matrix 읽기
    # ==========================================

    matrix_df = pd.read_csv(
        MATRIX_CSV_PATH,
        index_col=0
    )

    M = matrix_df.to_numpy(dtype=np.float64)

    print("Calibration Matrix M:")
    print(M)

    # ==========================================
    # 2. Pseudo-inverse 계산
    #
    # V = M @ P
    # P = pinv(M) @ V
    # ==========================================

    M_inv = np.linalg.pinv(M)

    return M_inv

# ==========================================
# 3. Virtual RGB -> Physical RGB
# ==========================================

def virtual_to_physical_rgb(M_inv, virtual_light):

    # Virtual RGB는 0~1
    virtual_rgb = np.array(
        [virtual_light["r"], virtual_light["g"], virtual_light["b"]],
        dtype=np.float64
    )

    # Physical RGB 계산
    physical_rgb = M_inv @ virtual_rgb

    # 범위를 벗어난 값 제한
    physical_rgb = np.clip(
        physical_rgb,
        0,
        255
    )

    # 실제 조명 제어용 정수값
    physical_rgb = np.round(
        physical_rgb
    ).astype(int)

    return {
        "r": int(physical_rgb[0]),
        "g": int(physical_rgb[1]),
        "b": int(physical_rgb[2]),
    }


# ==========================================
# 4. 테스트
# ==========================================
def dmx_remote_control(virtual_light: dict, physical_light: dict):
    BASE = "http://127.0.0.1:30010"
    preset = quote("NewRemoteControlPreset", safe="")
    prop_virtual = quote("Linear Color Input", safe="")
    # prop2 = quote("Intensity Input", safe="")
    prop_physical_red = quote("Dmx Red", safe="")
    prop_physical_green = quote("Dmx Green", safe="")
    prop_physical_blue = quote("Dmx Blue", safe="")
    prop_dmx_enabled = quote("DmxEnabled", safe="")

    payload = {
        "PropertyValue": {
            "R": virtual_light["r"]/255,
            "G": virtual_light["g"]/255,
            "B": virtual_light["b"]/255,
            "A": 1.5 # 실제 쓰이지는 않는 값
        },
        "GenerateTransaction": True
    }

    # payload2 = {
    #     "PropertyValue": lighting_condition["i"]*20/255,
    #     "GenerateTransaction": True
    # }

    payload3 = {
        "PropertyValue": physical_light["r"],
        "GenerateTransaction": True
    }

    payload4 = {
        "PropertyValue": physical_light["g"],
        "GenerateTransaction": True
    }

    payload5 = {
        "PropertyValue": physical_light["b"],
        "GenerateTransaction": True
    }

    payload_dmx_enabled = {
        "PropertyValue": True,
        "GenerateTransaction": True
    }

    url = f"{BASE}/remote/preset/{preset}/property/{prop_virtual}"
    # url2 = f"{BASE}/remote/preset/{preset}/property/{prop2}"
    url3 = f"{BASE}/remote/preset/{preset}/property/{prop_physical_red}"
    url4 = f"{BASE}/remote/preset/{preset}/property/{prop_physical_green}"
    url5 = f"{BASE}/remote/preset/{preset}/property/{prop_physical_blue}"
    dmx_flag_url = f"{BASE}/remote/preset/{preset}/property/{prop_dmx_enabled}"

    r = requests.put(url, json=payload)
    dmx_flag_r = requests.put(dmx_flag_url, json=payload_dmx_enabled)
    # intensity_r = requests.put(url2, json=payload2)
    red_r = requests.put(url3, json=payload3)
    green_r = requests.put(url4, json=payload4)
    blue_r = requests.put(url5, json=payload5)

    print(r.status_code)
    print(dmx_flag_r.status_code)
    # print(intensity_r.status_code)
    print(red_r.status_code)
    print(green_r.status_code)
    print(blue_r.status_code)

    print(r.text)
    print(dmx_flag_r.text)
    # print(intensity_r.text)
    print(red_r.text)
    print(green_r.text)
    print(blue_r.text)

# ==========================================
# virtual colorchecker 캡처
# ==========================================
def ColorCheckerCapture_virtual():
    URL = "http://127.0.0.1:30010"
    PRESET = quote("NewRemoteControlPreset", safe="")
    FUNCTION = quote("Capture Color Checker", safe="")

    payload = {
        "Parameters": {},
        "GenerateTransaction": True
    }

    response = requests.put(
        f"{URL}/remote/preset/{PRESET}/function/{FUNCTION}",
        json=payload
    )

    print(response.status_code)
    print(response.text)

def ColorCheckerCapture_physical(filename):
    client = obs.ReqClient(
        host=HOST,
        port=PORT,
        password=PASSWORD
    )

    source_name = "sony a7r4"
    save_dir = "/colorchecker_calibration_result/test/baseline/"
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

if __name__ == "__main__":

    M_inv = calculate_pseudo_inv_matrix(MATRIX_CSV_PATH)

    values = [43, 128, 213]

    for r in values:
        for g in values:
            for b in values:
                virtual_light = {
                    "r": r,
                    "g": g,
                    "b": b
                }

                # physical_light = virtual_to_physical_rgb(M_inv, virtual_light)

                print()
                print("Virtual Light:")
                print(virtual_light)

                # print()
                # print("Calculated Physical Light:")
                # print(physical_light)

                dmx_remote_control(virtual_light, virtual_light)
                time.sleep(3)
                # phy_r = physical_light["r"]
                # phy_g = physical_light["g"]
                # phy_b = physical_light["b"]
                filename = f"R{r}G{g}B{b}.png"
                ColorCheckerCapture_physical(filename)
