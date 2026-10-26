import json
import re

p = "ai/clinical_kb_data.json"
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

for c in data["conditions"]:
    old = c.get("name", "")
    new = re.sub(r"\s+of\s+[A-Za-z\s]+$", "", old).strip()
    c["name"] = new

with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print("Updated multiple word of suffixes in clinical_kb_data.json")
