import requests
from urllib.parse import quote
import time

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

def ColorCheckerCapture():
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

def main():
    values = [0, 85, 170, 255]
    for r in values:
        for g in values:
            for b in values:
                light_value = {
                "r": r,
                "g": g,
                "b": b,
            }
                print(light_value)
                dmx_remote_control(light_value)
                time.sleep(2)
                ColorCheckerCapture()

if __name__ == "__main__":
    main()