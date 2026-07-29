import base64
import cv2
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
import json

# OpenAI API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def extract_frames(video_path: str, ) -> list[str]:
    """
    영상에서 일정 시간 간격으로 프레임을 추출합니다.
    프레임은 Base64 문자열로 반환합니다.
    """
    cap = cv2.VideoCapture(video_path)

    interval_seconds = 1.0

    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise RuntimeError("영상 FPS를 읽을 수 없습니다.")

    frame_interval = max(1, round(fps * interval_seconds))

    encoded_frames = []
    frame_index = 0

    try:
        while True:
            success, frame = cap.read()

            if not success:
                break

            if frame_index % frame_interval == 0:
                encode_success, buffer = cv2.imencode(".jpg", frame)

                if encode_success:
                    base64_frame = base64.b64encode(buffer).decode("utf-8")
                    encoded_frames.append(base64_frame)
            frame_index += 1

    finally:
        cap.release()

    return encoded_frames


def analyze_video_with_vlm(video_path: str) -> str:
    """
    영상 프레임을 추출하고 VLM에 한 번에 전달합니다.
    """
    frames = extract_frames(video_path=video_path,)

    if not frames:
        raise RuntimeError("추출된 프레임이 없습니다.")

    content = [
        {
            "type": "input_text",
            "text": """
These images are frames sampled sequentially from one video.

Analyze the overall lighting of the video.

Select exactly one lighting option:
- cold: 8500K, for cold, tense, lonely, blue, night, sterile, or suspenseful scenes. 
- default: 5500K, for neutral, ordinary scenes.
- warm: 2500K, for warm, emotional, nostalgic, cozy, intimate, sunset, or soft scenes.

Return only valid JSON in this format:
{
    "lighting_temperature": "cold" | "default" | "warm",
    "reason": "short reason"
}
""",
        }
    ]

    for frame in frames:
        content.append(
            {
                "type": "input_image",
                "image_url": (
                    f"data:image/jpeg;base64,{frame}"
                ),
            }
        )

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
        temperature=0,
    )

    result = json.loads(response.output_text)
    return result


if __name__ == "__main__":
    videos_folder = Path("./result_videos")
    output_folder = Path("./video_lighting_evaluation_outputs")
    output_folder.mkdir(parents=True, exist_ok=True)

    num_attempts = 5

    for attempt in range(1, num_attempts + 1):
        attempt_folder = Path(output_folder / f"attempt{attempt}")
        attempt_folder.mkdir(parents=True, exist_ok=True)

        for video_path in sorted(videos_folder.glob("*.mp4")):
            result = analyze_video_with_vlm(video_path=video_path, )

            output = {
                "video_path": str(video_path),
                "lighting_temperature": result["lighting_temperature"],
                "reason": result["reason"]
            }

            output_path = attempt_folder / f"{video_path.stem}_output.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)