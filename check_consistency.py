import json
from pathlib import Path
from collections import Counter

base_dir = Path("script_to_lighting_outputs")
num_attempts = 5
num_scripts = 15

for script_num in range(1, num_scripts + 1):
    temperatures = []

    for attempt_num in range(1, num_attempts + 1):
        file_path = (
            base_dir
            / f"attempt{attempt_num}"
            / f"script{script_num}_output.json"
        )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            temperature = int(data["lighting_temperature"])
            temperatures.append(temperature)

        except FileNotFoundError:
            print(f"파일 없음: {file_path}")
        except (KeyError, ValueError, TypeError) as e:
            print(f"형식 오류: {file_path} - {e}")

    counts = Counter(temperatures)
    is_consistent = len(counts) == 1 and len(temperatures) == num_attempts

    print(f"\nScript {script_num}")
    print(f"결과: {temperatures}")
    print(f"선택 횟수: {dict(counts)}")
    print(f"항상 같은 옵션: {'Yes' if is_consistent else 'No'}")