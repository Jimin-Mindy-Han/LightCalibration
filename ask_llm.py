# input = script
# output = color_option
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# OpenAI API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
temperature_number = 0

def load_script(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    return script

LIGHTING_OPTIONS = {
    "cold": 8500,
    "default": 5500,
    "warm": 2500
}

def output_lighting_option(script_path) -> dict:
    """ask LLM and output lighting option"""
    client = OpenAI()
    script = load_script(script_path)

    PROMPT = f"""
    SCRIPT:
    {script}

    You are a lighting control assistant for virtual production.

    Your task is to select exactly one lighting option based on the script.

    Available options:
    - cold: 8500K, for cold, tense, lonely, blue, night, sterile, or suspenseful scenes. 
    - default: 5500K, for neutral, ordinary, or unspecified lighting.
    - warm: 2500K, for warm, emotional, nostalgic, cozy, intimate, sunset, or soft scenes.

    Return only valid JSON in this format:
    {{
        "lighting_temperature": "cold" | "default" | "warm",
        "reason": "short reason"
    }}

    If the script does not clearly imply a lighting mood, choose default.
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
        temperature = "default"

    if temperature == "cold":
        temperature_number = 8500
    elif temperature == "default":
        temperature_number = 5500
    elif temperature == "warm":
        temperature_number = 2500
    output = {
        "lighting_temperature": temperature_number,
        "reason": answer.get("reason", "")
    }

    return output

if __name__ == "__main__":
    output = output_lighting_option("Script/script_cold.txt")
    print(output)