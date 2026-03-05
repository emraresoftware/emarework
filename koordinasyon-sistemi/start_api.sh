#!/bin/bash
# API Sunucu Başlatma Scripti

cd "/Users/emre/Desktop/Emare/yazılım ekibi/koordinasyon-sistemi"

echo "🚀 Hive Coordinator API başlatılıyor..."
echo "📍 Port: 8000"
echo "🌐 URL: http://127.0.0.1:8000"
echo "📚 Swagger: http://127.0.0.1:8000/docs"
echo ""

python3 -B -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
