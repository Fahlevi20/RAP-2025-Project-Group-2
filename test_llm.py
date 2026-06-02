"""
Test script: cek apakah OpenRouter LLM bisa dipanggil
Fitur: auto-retry pada rate limit + fallback ke model lain
"""
import os
import sys
import time

print("=== Test OpenRouter LLM ===")

# Ambil API key dari env atau file
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    key_file = "/mnt/project/api-key.txt"
    if not os.path.exists(key_file):
        key_file = "/home/ros/rap/Gruppe2/api-key.txt"
    if os.path.exists(key_file):
        with open(key_file) as f:
            api_key = f.read().strip().split("\n")[-1]

if not api_key:
    print("ERROR: API key tidak ditemukan!")
    sys.exit(1)

print(f"API Key ditemukan: {api_key[:20]}...")

try:
    from langchain_openai import ChatOpenAI
    print("✅ langchain_openai berhasil diimport")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Daftar model free yang dicoba secara berurutan
MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-4-31b-it:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openai/gpt-oss-20b:free",
]

MAX_RETRIES = 3
RETRY_DELAY = 35  # detik — sesuai Retry-After dari API

for model in MODELS:
    print(f"\n--- Mencoba model: {model} ---")
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Attempt {attempt}/{MAX_RETRIES}...")
            response = llm.invoke("Say 'Hello from OpenRouter!' and nothing else.")
            print(f"\n✅ LLM BERHASIL dengan model: {model}")
            print(f"Response: {response.content}")
            print(f"\n=== REKOMENDASI: Gunakan model '{model}' di rosa_summit.py ===")
            sys.exit(0)

        except Exception as e:
            err = str(e)
            if "429" in err:
                if attempt < MAX_RETRIES:
                    print(f"⚠️  Rate limited — tunggu {RETRY_DELAY}s lalu retry...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"❌ Rate limit terus — skip ke model berikutnya")
            elif "404" in err:
                print(f"❌ Model tidak tersedia — skip")
                break
            else:
                print(f"❌ Error: {e}")
                break

print("\n❌ Semua model gagal. Coba lagi nanti.")
sys.exit(1)
