#!/bin/bash
# API Server başlatma scripti

set -e

cd "$(dirname "$0")"

echo "🚀 Hive Coordinator API başlatılıyor..."

# Virtual environment kontrolü
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment bulunamadı. Oluşturuluyor..."
    python3 -m venv .venv
fi

# Aktivasyon
source .venv/bin/activate

# Dependency kurulumu
echo "📦 Paketler kontrol ediliyor..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# .env kontrolü
if [ ! -f ".env" ]; then
    echo "⚠️  .env dosyası bulunamadı. .env.example kopyalanıyor..."
    cp .env.example .env
    echo "✏️  Lütfen .env dosyasını düzenleyin!"
fi

# Database migration (Alembic varsa)
if [ -f "alembic.ini" ]; then
    echo "🗄️  Database migration çalıştırılıyor..."
    alembic upgrade head
fi

# API başlat
echo "✅ API başlatılıyor: http://localhost:8000"
export PYTHONPATH="$(pwd)"
exec python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
