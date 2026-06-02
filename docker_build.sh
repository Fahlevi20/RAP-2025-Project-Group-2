#!/bin/bash
# docker_build.sh — build dengan cache, auto-retry kalau gagal

IMAGE_NAME="rap-gruppe2:latest"
BUILD_DIR="/home/fahlevi/RAP-2025-Project-Group-2"
MAX_RETRIES=3
RETRY_DELAY=10

echo "============================================"
echo " Docker Build Script — dengan cache & retry"
echo "============================================"

for attempt in $(seq 1 $MAX_RETRIES); do
    echo ""
    echo ">>> Attempt $attempt of $MAX_RETRIES..."
    echo ""

    # Pakai cache (tanpa --no-cache) supaya layer yang sudah berhasil tidak diulangi
    if docker build -t "$IMAGE_NAME" "$BUILD_DIR" 2>&1; then
        echo ""
        echo "✅ Build BERHASIL pada attempt $attempt!"
        exit 0
    else
        EXIT_CODE=$?
        echo ""
        echo "❌ Build GAGAL pada attempt $attempt (exit code: $EXIT_CODE)"

        if [ $attempt -lt $MAX_RETRIES ]; then
            echo "   Menunggu ${RETRY_DELAY}s sebelum retry (menggunakan cache dari layer sebelumnya)..."
            sleep $RETRY_DELAY
        fi
    fi
done

echo ""
echo "❌ Build gagal setelah $MAX_RETRIES percobaan."
echo "   Cek log di atas untuk detail error."
exit 1
