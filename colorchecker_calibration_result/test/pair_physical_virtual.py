import re
import pandas as pd

TXT_PATH = "physical_virtual_pairs.txt"
OUTPUT_CSV = "physical_virtual_pairs.csv"

with open(TXT_PATH, "r", encoding="utf-8") as f:
    text = f.read()

pattern = re.compile(
    r"Virtual Light:\s*"
    r"\{'r': (\d+), 'g': (\d+), 'b': (\d+)\}\s*"
    r"Calculated Physical Light:\s*"
    r"\{'r': (\d+), 'g': (\d+), 'b': (\d+)\}"
)

matches = pattern.findall(text)

results = []

for vr, vg, vb, pr, pg, pb in matches:

    vr, vg, vb = int(vr), int(vg), int(vb)
    pr, pg, pb = int(pr), int(pg), int(pb)

    results.append({
        "virtual_r": vr,
        "virtual_g": vg,
        "virtual_b": vb,
        "physical_r": pr,
        "physical_g": pg,
        "physical_b": pb,
        "virtual_file": f"R{vr}G{vg}B{vb}.csv",
        "physical_file": f"R{pr}G{pg}B{pb}.csv"
    })

df = pd.DataFrame(results)
df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

print(df)