import urllib.request
import json

API_KEY = open("/home/ros/rap/Gruppe2/api-key.txt").read().strip()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

free_models = [m["id"] for m in data["data"] if ":free" in m["id"]]
print("=== Free models tersedia di OpenRouter ===")
for m in free_models:
    print(f"  - {m}")
print(f"\nTotal: {len(free_models)} model gratis")
