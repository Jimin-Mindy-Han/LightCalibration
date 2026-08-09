# input = script
# output = color_option
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# OpenAI API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
temperature_number = 0

# RGB
# def load_script(script_path):
#     with open(script_path, "r", encoding="utf-8") as f:
#         script = f.read()
#     return script
#
# LIGHTING_OPTIONS = {
#     "cold": {"r": 50, "g": 100, "b": 255},
#     "neutral": {"r": 255, "g": 255, "b": 255},
#     "warm": {"r": 255, "g": 100, "b": 50}
# }

# CCT
def load_script(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    return script

LIGHTING_OPTIONS = {
    "cold": 8500,
    "neutral": 5500,
    "warm": 2500
}

# RGB output
# def output_lighting_option(script_path) -> dict:
#     """ask LLM and output lighting option"""
#     client = OpenAI()
#
#     with open(script_path, "r", encoding="utf-8") as f:
#         script = f.read()
#
#     PROMPT = f"""
#     SCRIPT:
#     {script}
#
#     You are a lighting control assistant for virtual production.
#
#     Your task is to select exactly one lighting option based on the script.
#
#     Available options:
#     - cold: (R=160, G=200, B=255), for cold, tense, lonely, blue, night, sterile, or suspenseful scenes.
#     - neutral: (R=255, G=255, B=255), for neutral, ordinary, or unspecified lighting.
#     - warm: (R=255, G=180, B=120), for warm, emotional, nostalgic, cozy, intimate, sunset, or soft scenes.
#
#     Return only valid JSON in this format:
#     {{
#         "lighting_temperature": "cold" | "neutral" | "warm",
#         "reason": "short reason"
#     }}
#
#     If the script does not clearly imply a lighting mood, choose neutral.
#     """
#
#     response = client.responses.create(
#         model = "gpt-4.1",
#         input = [{
#             "role": "user",
#             "content": [
#                 {"type": "input_text", "text": PROMPT},
#             ]
#         }],
#         temperature = 0
#     )
#
#     answer = json.loads(response.output_text)
#
#     temperature = answer.get("lighting_temperature")
#
#     if temperature not in LIGHTING_OPTIONS:
#         temperature = "neutral"
#
#     if temperature == "cold":
#         temperature_number = LIGHTING_OPTIONS["cold"]
#     elif temperature == "neutral":
#         temperature_number = LIGHTING_OPTIONS["neutral"]
#     elif temperature == "warm":
#         temperature_number = LIGHTING_OPTIONS["warm"]
#
#     output = {
#         "script_path": str(script_path),
#         "script": script,
#         "lighting_temperature": temperature_number,
#         "reason": answer.get("reason", "")
#     }
#
#     return output

def output_lighting_option(script_path) -> dict:
    """ask LLM and output lighting option"""
    client = OpenAI()

    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()

    PROMPT = f"""
    SCRIPT:
    {script}

    You are a lighting control assistant for virtual production.

    Your task is to select exactly one lighting option based on the script.

    Available options:
    - cold: 8500K, for cold, tense, lonely, blue, night, sterile, or suspenseful scenes.
    - neutral: 5500K, for neutral, ordinary, or unspecified lighting.
    - warm: 2500K, for warm, emotional, nostalgic, cozy, intimate, sunset, or soft scenes.

    Return only valid JSON in this format:
    {{
        "lighting_temperature": "cold" | "neutral" | "warm",
        "reason": "short reason"
    }}

    If the script does not clearly imply a lighting mood, choose neutral.
    """

    response = client.responses.create(
        model = "gpt-4.1",
        input = [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": PROMPT},
            ]
        }],
        temperature = 0
    )

    answer = json.loads(response.output_text)

    temperature = answer.get("lighting_temperature")

    if temperature not in LIGHTING_OPTIONS:
        temperature = "neutral"

    if temperature == "cold":
        temperature_number = 8500
    elif temperature == "neutral":
        temperature_number = 5500
    elif temperature == "warm":
        temperature_number = 2500

    output = {
        "script_path": str(script_path),
        "script": script,
        "lighting_temperature": temperature_number,
        "reason": answer.get("reason", "")
    }

    return output

if __name__ == "__main__":
    input_path = Path("./scripts/1.txt")
    output_root = Path("script_to_lighting_outputs")

    num_attempts = 1

    for attempt in range(1, num_attempts + 1):
        attempt_folder = output_root / f"attempt{attempt}"
        attempt_folder.mkdir(parents=True, exist_ok=True,)

        try:
            output = output_lighting_option(input_path)

            output_path = (attempt_folder / f"{input_path.stem}_output.json")

            with open(output_path, "w", encoding="utf-8",) as f:
                json.dump(output, f, ensure_ascii=False, indent=2,)

            print(f"Attempt {attempt}, " f"Script {input_path.stem}: " f"{output['lighting_temperature']}")

        except Exception as error:
            print(f"Attempt {attempt}, " f"Script {input_path.stem} 오류: {error}")