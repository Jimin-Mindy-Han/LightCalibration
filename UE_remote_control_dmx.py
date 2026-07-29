import requests
from urllib.parse import quote

def dmx_remote_control(temperature):
    BASE = "http://127.0.0.1:30011"
    preset = quote("NewRemoteControlPreset", safe="")
    # prop = quote("Linear Color Input", safe="")
    prop = quote("Temperature Input", safe="")
    prop_dmx_enabled = quote("DmxEnabled", safe="")

    # payload = {
    #     "PropertyValue": {
    #         "R": 1.5,
    #         "G": 0.2,
    #         "B": 0.5,
    #         "A": 1.5
    #     },
    #     "GenerateTransaction": True
    # }

    payload = {
        "PropertyValue": temperature,
        "GenerateTransaction": True
    }

    payload_dmx_enabled = {
        "PropertyValue": True,
        "GenerateTransaction": True
    }

    url = f"{BASE}/remote/preset/{preset}/property/{prop}"
    dmx_flag_url = f"{BASE}/remote/preset/{preset}/property/{prop_dmx_enabled}"

    r = requests.put(url, json=payload)
    dmx_flag_r = requests.put(dmx_flag_url, json=payload_dmx_enabled)

    print(r.status_code)
    print(dmx_flag_r.status_code)
    print(r.text)
    print(dmx_flag_r.text)

if __name__ == "__main__":
    dmx_remote_control(8500)