"""
Derviş Yetenekleri (Capabilities) Veritabanı
=============================================

Her Emare dervişinin detaylı yeteneklerini, iç/dış API'lerini,
sunduğu servisleri ve entegrasyon noktalarını tanımlar.

Bu modül:
- Dashboard'da derviş detay panelinde gösterilir
- Görev eşleştirmede kullanılır
- Dergah sohbet odasında derviş tanıtımları için referans olur
"""

from typing import Dict, List, Any

# ─────────────────────────────────────────────────────────────────────────────
# Derviş Yetenekleri Haritası
# ─────────────────────────────────────────────────────────────────────────────

DERVISH_CAPABILITIES: Dict[str, Dict[str, Any]] = {

    "emare-asistan": {
        "role": "AI Müşteri Hizmetleri Dervişi",
        "specialty": "Multi-tenant SaaS AI müşteri hizmetleri platformu",
        "internal_apis": [
            {"endpoint": "/api/chat", "method": "POST", "desc": "AI sohbet yanıtı üret"},
            {"endpoint": "/api/tenants", "method": "GET", "desc": "Tenant listesi"},
            {"endpoint": "/api/tenants/{id}/config", "method": "PUT", "desc": "Tenant ayarlarını güncelle"},
            {"endpoint": "/api/conversations", "method": "GET", "desc": "Sohbet geçmişi"},
            {"endpoint": "/api/analytics/dashboard", "method": "GET", "desc": "Kullanım analitikleri"},
            {"endpoint": "/api/templates", "method": "CRUD", "desc": "Mesaj şablonları yönetimi"},
            {"endpoint": "/api/webhooks/whatsapp", "method": "POST", "desc": "WhatsApp webhook alıcı"},
            {"endpoint": "/api/webhooks/telegram", "method": "POST", "desc": "Telegram webhook alıcı"},
        ],
        "external_apis": [
            {"name": "Google Gemini AI", "usage": "Doğal dil yanıt üretimi"},
            {"name": "WhatsApp Business API", "usage": "Mesaj gönderme/alma"},
            {"name": "Telegram Bot API", "usage": "Bot mesajlaşma"},
            {"name": "Instagram Graph API", "usage": "DM otomasyonu"},
        ],
        "services": ["AI Chat Engine", "Multi-tenant Yönetim", "Mesaj Şablonları", "Webhook İşleyici", "Analitik Dashboard"],
        "integrations": ["emarecloud", "emare-finance", "emareapi"],
        "ports": {"production": 8000, "local": None},
        "strengths": ["Çok kanallı iletişim", "AI yanıt üretimi", "Tenant izolasyonu", "Gerçek zamanlı mesajlaşma"],
    },

    "emarecloud": {
        "role": "Altyapı Yönetim Dervişi",
        "specialty": "Multi-tenant sunucu ve altyapı yönetim paneli",
        "internal_apis": [
            {"endpoint": "/api/servers", "method": "CRUD", "desc": "Sunucu yönetimi"},
            {"endpoint": "/api/ssh/execute", "method": "POST", "desc": "SSH komut çalıştır"},
            {"endpoint": "/api/firewall/rules", "method": "CRUD", "desc": "Firewall kural yönetimi"},
            {"endpoint": "/api/dns/zones", "method": "CRUD", "desc": "DNS zone yönetimi"},
            {"endpoint": "/api/lxd/containers", "method": "CRUD", "desc": "LXD container yönetimi"},
            {"endpoint": "/api/marketplace", "method": "GET", "desc": "Uygulama marketi"},
            {"endpoint": "/api/deploy/webhook/{secret}", "method": "POST", "desc": "Auto-deploy webhook"},
            {"endpoint": "/api/monitoring/status", "method": "GET", "desc": "Sunucu durumu izleme"},
        ],
        "external_apis": [
            {"name": "Cloudflare API", "usage": "DNS ve CDN yönetimi"},
            {"name": "LXD REST API", "usage": "Container orchestration"},
            {"name": "Let's Encrypt", "usage": "SSL sertifika otomasyonu"},
        ],
        "services": ["SSH Terminal (xterm.js)", "Firewall Manager", "DNS Manager", "LXD Orchestrator", "Auto-Deploy", "Marketplace", "Monitoring"],
        "integrations": ["emare-asistan", "emare-hosting", "emaregithub", "emareapi"],
        "ports": {"production": 5000, "local": None},
        "strengths": ["Sunucu yönetimi", "SSH otomasyonu", "Container orchestration", "Auto-deploy pipeline"],
    },

    "emare-finance": {
        "role": "Finans & İşletme Yönetimi Dervişi",
        "specialty": "Multi-tenant SaaS POS + işletme yönetim yazılımı",
        "internal_apis": [
            {"endpoint": "/api/invoices", "method": "CRUD", "desc": "Fatura yönetimi (e-Fatura)"},
            {"endpoint": "/api/pos/sales", "method": "POST", "desc": "POS satış işlemi"},
            {"endpoint": "/api/accounting/ledger", "method": "GET", "desc": "Muhasebe defteri"},
            {"endpoint": "/api/reports/financial", "method": "GET", "desc": "Finansal raporlar"},
            {"endpoint": "/api/sms/send", "method": "POST", "desc": "SMS gönderimi"},
            {"endpoint": "/api/marketing/campaigns", "method": "CRUD", "desc": "Pazarlama kampanyaları"},
            {"endpoint": "/api/ai-assistant", "method": "POST", "desc": "AI işletme asistanı"},
            {"endpoint": "/api/inventory", "method": "CRUD", "desc": "Stok yönetimi"},
        ],
        "external_apis": [
            {"name": "GIB e-Fatura API", "usage": "Elektronik fatura entegrasyonu"},
            {"name": "SMS Provider API", "usage": "Toplu SMS gönderimi"},
            {"name": "Banka API'leri", "usage": "Ödeme takibi"},
        ],
        "services": ["e-Fatura", "POS Satış", "Muhasebe", "Stok Yönetimi", "SMS Pazarlama", "AI Asistan", "Finansal Raporlama"],
        "integrations": ["emare-pos", "emare-asistan", "emareapi"],
        "ports": {"production": 8080, "local": None},
        "strengths": ["e-Fatura entegrasyonu", "Çok şubeli yönetim", "Finansal raporlama", "Pazarlama otomasyonu"],
    },

    "emare-pos": {
        "role": "POS & Adisyon Dervişi",
        "specialty": "Restoran/kafe web tabanlı POS + adisyon yönetim sistemi",
        "internal_apis": [
            {"endpoint": "/api/orders", "method": "CRUD", "desc": "Sipariş yönetimi"},
            {"endpoint": "/api/tables", "method": "CRUD", "desc": "Masa yönetimi"},
            {"endpoint": "/api/kitchen/queue", "method": "GET", "desc": "Mutfak kuyruğu"},
            {"endpoint": "/api/cash-register", "method": "POST", "desc": "Kasa işlemleri"},
            {"endpoint": "/api/menu", "method": "CRUD", "desc": "Menü yönetimi"},
            {"endpoint": "/api/reports/daily", "method": "GET", "desc": "Günlük rapor"},
        ],
        "external_apis": [],
        "services": ["Masa Yönetimi", "Adisyon Sistemi", "Mutfak Ekranı", "Kasa Yönetimi", "Menü Editörü", "Raporlama"],
        "integrations": ["emare-finance"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["Gerçek zamanlı sipariş takibi", "Mutfak-garson senkron", "Çoklu kasa desteği"],
    },

    "emaredesk": {
        "role": "Uzak Masaüstü Dervişi",
        "specialty": "Python + Web tabanlı uzak masaüstü yazılımı",
        "internal_apis": [
            {"endpoint": "/ws/screen", "method": "WS", "desc": "WebSocket ekran akışı"},
            {"endpoint": "/ws/input", "method": "WS", "desc": "Fare/klavye kontrolü"},
            {"endpoint": "/api/sessions", "method": "GET", "desc": "Aktif oturum listesi"},
            {"endpoint": "/api/connect", "method": "POST", "desc": "Yeni bağlantı başlat"},
        ],
        "external_apis": [],
        "services": ["Ekran Paylaşımı", "Uzak Kontrol", "Çoklu Oturum", "Düşük Gecikmeli Akış"],
        "integrations": ["emarecloud"],
        "ports": {"production": None, "local": 5000},
        "strengths": ["WebSocket gerçek zamanlı akış", "Düşük gecikme", "Platform bağımsız"],
    },

    "emaresetup": {
        "role": "Yazılım Fabrikası Dervişi",
        "specialty": "AI destekli yazılım fabrikası CLI — doğal dil ile modül üretimi",
        "internal_apis": [
            {"endpoint": "/api/generate", "method": "POST", "desc": "Doğal dil → kod üretimi"},
            {"endpoint": "/api/modules", "method": "CRUD", "desc": "Modül yönetimi"},
            {"endpoint": "/api/versions", "method": "GET", "desc": "Versiyon takibi"},
            {"endpoint": "/api/fleet/deploy", "method": "POST", "desc": "Filo dağıtımı"},
            {"endpoint": "/api/templates", "method": "GET", "desc": "Proje şablonları"},
        ],
        "external_apis": [
            {"name": "Google Gemini AI", "usage": "Kod üretimi"},
            {"name": "OpenAI API", "usage": "Alternatif AI motor"},
        ],
        "services": ["Kod Üretici", "Modül Yönetici", "Versiyon Kontrol", "Filo Dağıtım", "Şablon Motoru"],
        "integrations": ["emarehup", "emarecode", "emareapi"],
        "ports": {"production": None, "local": 8080},
        "strengths": ["Doğal dil → kod", "Çoklu AI motor", "Otomatik modül üretimi"],
    },

    "emarehup": {
        "role": "Yazılım Fabrikası Ana Üs Dervişi",
        "specialty": "DevM otonom geliştirme platformu (Node.js orchestrator)",
        "internal_apis": [
            {"endpoint": "/api/orchestrate", "method": "POST", "desc": "Otonom geliştirme başlat"},
            {"endpoint": "/api/agents", "method": "GET", "desc": "AI agent listesi"},
            {"endpoint": "/api/pipelines", "method": "CRUD", "desc": "CI/CD pipeline yönetimi"},
            {"endpoint": "/api/workspace", "method": "GET", "desc": "Çalışma alanı durumu"},
        ],
        "external_apis": [
            {"name": "Google Gemini AI", "usage": "AI orchestration"},
            {"name": "GitHub Copilot", "usage": "Kod önerisi"},
            {"name": "LangGraph", "usage": "Multi-agent workflow"},
        ],
        "services": ["Otonom Geliştirme", "AI Agent Orchestration", "CI/CD Pipeline", "Çalışma Alanı Yönetimi"],
        "integrations": ["emaresetup", "emarecode", "emaregithub"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Otonom yazılım geliştirme", "Multi-agent orchestration", "CI/CD entegrasyonu"],
    },

    "emarebot": {
        "role": "E-Ticaret Otomasyon Dervişi",
        "specialty": "Trendyol kozmetik mağazası müşteri yanıtlama uygulaması",
        "internal_apis": [
            {"endpoint": "desktop_app", "method": "GUI", "desc": "Tkinter masaüstü uygulaması"},
            {"endpoint": "/api/questions", "method": "GET", "desc": "Müşteri soruları"},
            {"endpoint": "/api/answers/generate", "method": "POST", "desc": "AI yanıt üret"},
        ],
        "external_apis": [
            {"name": "Trendyol Seller API", "usage": "Müşteri soruları çekme/yanıtlama"},
            {"name": "Google Gemini AI", "usage": "Akıllı yanıt üretimi"},
        ],
        "services": ["Otomatik Yanıt Üretimi", "Soru Analizi", "Benzerlik Eşleştirme", "Toplu Yanıt Gönderimi"],
        "integrations": [],
        "ports": {"production": None, "local": None},
        "strengths": ["Trendyol entegrasyonu", "AI yanıt kalitesi", "difflib benzerlik analizi"],
    },

    "emareoracle": {
        "role": "Veritabanı Motoru Dervişi",
        "specialty": "C dilinde sıfırdan yazılan tam ilişkisel veritabanı motoru (ZeusDB)",
        "internal_apis": [
            {"endpoint": "zeusdb_cli", "method": "CLI", "desc": "SQL komut satırı arayüzü"},
            {"endpoint": "zeusdb_api", "method": "C-API", "desc": "Yerleşik C kütüphane API'si"},
        ],
        "external_apis": [],
        "services": ["B+Tree İndeksleme", "WAL (Write-Ahead Log)", "ACID İşlemler", "SQL Parser", "Query Optimizer"],
        "integrations": ["emareai"],
        "ports": {"production": None, "local": 5432},
        "strengths": ["5016 satır C kodu", "ACID uyumlu", "Sıfırdan B+Tree", "Düşük seviye kontrol"],
    },

    "siberemare": {
        "role": "Siber Güvenlik Dervişi",
        "specialty": "Otomatik penetrasyon testi raporlama pipeline",
        "internal_apis": [
            {"endpoint": "/api/scan", "method": "POST", "desc": "Güvenlik taraması başlat"},
            {"endpoint": "/api/reports", "method": "GET", "desc": "Penetrasyon test raporları"},
            {"endpoint": "/api/vulnerabilities", "method": "GET", "desc": "Zafiyet listesi"},
        ],
        "external_apis": [
            {"name": "Claude 3.5 Sonnet", "usage": "Zafiyet analizi ve raporlama"},
            {"name": "GPT-4o", "usage": "Self-critique ve iyileştirme"},
            {"name": "Neo4j", "usage": "Saldırı grafiği"},
        ],
        "services": ["Penetrasyon Testi", "Zafiyet Tarama", "PDF Rapor Üretimi", "Multi-Agent Analiz", "Saldırı Grafiği"],
        "integrations": ["emarecloud", "emareidi"],
        "ports": {"production": None, "local": 8888},
        "strengths": ["LangGraph multi-agent", "Self-critique döngüsü", "Otomatik PDF rapor", "Neo4j saldırı grafiği"],
    },

    "emare-log": {
        "role": "ISS CRM/ERP Dervişi",
        "specialty": "ISS şirketleri için CRM + ERP + NOC paneli",
        "internal_apis": [
            {"endpoint": "/api/customers", "method": "CRUD", "desc": "Müşteri yönetimi"},
            {"endpoint": "/api/tickets", "method": "CRUD", "desc": "Teknik destek talepleri"},
            {"endpoint": "/api/mikrotik/logs", "method": "GET", "desc": "MikroTik log toplama (5651)"},
            {"endpoint": "/api/billing/invoices", "method": "CRUD", "desc": "Fatura yönetimi"},
            {"endpoint": "/api/noc/dashboard", "method": "GET", "desc": "NOC izleme paneli"},
            {"endpoint": "/api/sms/send", "method": "POST", "desc": "SMS bildirimi"},
        ],
        "external_apis": [
            {"name": "MikroTik RouterOS API", "usage": "Router log ve yönetimi"},
            {"name": "SMS Gateway API", "usage": "SMS gönderimi"},
        ],
        "services": ["CRM", "ERP", "NOC Panel", "5651 Log Yönetimi", "Faturalama", "Teknik Servis", "MikroTik Entegrasyonu"],
        "integrations": ["emare-finance", "emarecloud"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["5651 uyumlu log yönetimi", "MikroTik entegrasyonu", "Çok modüllü ISS yönetimi"],
    },

    "emare-makale": {
        "role": "İçerik Üretim Dervişi",
        "specialty": "Otomatik Türkçe makale üretim + yönetim + paylaşım",
        "internal_apis": [
            {"endpoint": "/api/articles/generate", "method": "POST", "desc": "AI makale üret"},
            {"endpoint": "/api/articles", "method": "CRUD", "desc": "Makale yönetimi"},
            {"endpoint": "/api/trends", "method": "GET", "desc": "Reddit/HN trend toplayıcı"},
            {"endpoint": "/api/publish", "method": "POST", "desc": "Makale yayınla"},
        ],
        "external_apis": [
            {"name": "OpenAI GPT-4o", "usage": "Makale üretimi"},
            {"name": "Reddit API", "usage": "Trend toplama"},
            {"name": "Hacker News API", "usage": "Trend toplama"},
        ],
        "services": ["AI Makale Üretimi", "Trend Analizi", "İçerik Yönetimi", "Otomatik Yayınlama"],
        "integrations": ["sosyal-medya-yonetim-araci"],
        "ports": {"production": 5000, "local": 5000},
        "strengths": ["Türkçe içerik üretimi", "Trend izleme", "Otomatik yayınlama"],
    },

    "yazilim-ekibi": {
        "role": "Koordinasyon Dervişi (Hive Coordinator)",
        "specialty": "9 Milyar düğümlü hiyerarşik yazılım ekibi koordinasyon sistemi",
        "internal_apis": [
            {"endpoint": "/api", "method": "GET", "desc": "Sistem durumu"},
            {"endpoint": "/nodes", "method": "CRUD", "desc": "Düğüm yönetimi"},
            {"endpoint": "/tasks", "method": "CRUD", "desc": "Görev dağıtımı"},
            {"endpoint": "/messages/directive", "method": "POST", "desc": "Emir gönder"},
            {"endpoint": "/messages/broadcast", "method": "POST", "desc": "Yayın gönder"},
            {"endpoint": "/messages/peer", "method": "POST", "desc": "P2P mesaj"},
            {"endpoint": "/workers", "method": "GET", "desc": "AI worker listesi"},
            {"endpoint": "/emare/projects", "method": "GET", "desc": "Ekosistem projeleri"},
            {"endpoint": "/emare/health", "method": "GET", "desc": "Ekosistem sağlık"},
            {"endpoint": "/analytics/overview", "method": "GET", "desc": "Analitik özet"},
            {"endpoint": "/emareulak/project", "method": "POST", "desc": "EmareUlak dağıtım"},
            {"endpoint": "/dergah/messages", "method": "GET", "desc": "Dergah sohbet mesajları"},
        ],
        "external_apis": [],
        "services": ["Hive Koordinasyon", "Görev Dağıtımı", "Mesaj Cascade", "EmareUlak Bridge", "Ekosistem İzleme", "AI Worker Yönetimi", "Dergah Sohbet Odası"],
        "integrations": ["*"],  # Tüm dervişlerle entegre
        "ports": {"production": 8000, "local": 8000},
        "strengths": ["9 milyar düğüm kapasitesi", "Hiyerarşik koordinasyon", "Otomatik görev dağıtımı", "Real-time dashboard"],
    },

    "emare-team": {
        "role": "Ekip Yönetim Dervişi",
        "specialty": "Emare ekibi için iç proje ve görev yönetim uygulaması",
        "internal_apis": [
            {"endpoint": "/api/projects", "method": "CRUD", "desc": "Proje yönetimi"},
            {"endpoint": "/api/tasks", "method": "CRUD", "desc": "Görev yönetimi (Kanban)"},
            {"endpoint": "/api/team/members", "method": "GET", "desc": "Ekip üyeleri"},
            {"endpoint": "/api/activity", "method": "GET", "desc": "Aktivite akışı"},
        ],
        "external_apis": [],
        "services": ["Kanban Board", "Proje Yönetimi", "Görev Takibi", "Aktivite Akışı"],
        "integrations": ["yazilim-ekibi"],
        "ports": {"production": 5001, "local": 5001},
        "strengths": ["Basit ve hızlı", "SPA mimari", "Kanban görünümü"],
    },

    "emarekatip": {
        "role": "Veri Toplayıcı Dervişi",
        "specialty": "Disk veri toplayıcı ve analizcisi — otomatik proje tarama",
        "internal_apis": [
            {"endpoint": "katip_cli", "method": "CLI", "desc": "Komut satırı tarayıcı"},
            {"endpoint": "/api/scan", "method": "POST", "desc": "Disk taraması başlat"},
            {"endpoint": "/api/reports", "method": "GET", "desc": "Tarama raporları"},
        ],
        "external_apis": [],
        "services": ["Proje Tarama", "Teknoloji Tespiti", "Rapor Üretimi", "Git Analizi"],
        "integrations": ["yazilim-ekibi", "emaregithub"],
        "ports": {"production": None, "local": None},
        "strengths": ["Otomatik teknoloji tespiti", "Git repo analizi", "Disk tarama"],
    },

    "emareulak": {
        "role": "İletişim Dervişi",
        "specialty": "Browser extension + WebSocket server — Chat izleyici ve analiz sistemi",
        "internal_apis": [
            {"endpoint": "/ws/chat", "method": "WS", "desc": "WebSocket chat akışı"},
            {"endpoint": "/api/chats", "method": "GET", "desc": "İzlenen sohbet listesi"},
            {"endpoint": "/api/analytics/chat", "method": "GET", "desc": "Chat analitiği"},
        ],
        "external_apis": [],
        "services": ["Chat İzleme", "WebSocket Server", "Chrome Extension", "Chat Analizi"],
        "integrations": ["yazilim-ekibi"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Gerçek zamanlı chat izleme", "Browser extension", "WebSocket"],
    },

    "emareads": {
        "role": "Tarayıcı Eklenti Dervişi",
        "specialty": "AI-powered çok yetenekli tarayıcı eklentisi",
        "internal_apis": [
            {"endpoint": "chrome_extension", "method": "EXT", "desc": "Chrome Extension API"},
            {"endpoint": "/api/ai/analyze", "method": "POST", "desc": "Sayfa analizi"},
        ],
        "external_apis": [
            {"name": "Chrome Extension API", "usage": "Tarayıcı entegrasyonu"},
        ],
        "services": ["Sayfa Analizi", "AI Asistan", "Reklam Yönetimi"],
        "integrations": ["emare-asistan"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Tarayıcı entegrasyonu", "AI sayfa analizi"],
    },

    "emareai": {
        "role": "Yapay Zeka Motoru Dervişi",
        "specialty": "Kendi yapay zeka motorumuz — LLaMA/Mistral fine-tuning, self-hosted AI",
        "internal_apis": [
            {"endpoint": "/api/generate", "method": "POST", "desc": "Metin üretimi"},
            {"endpoint": "/api/embeddings", "method": "POST", "desc": "Embedding vektörü"},
            {"endpoint": "/api/models", "method": "GET", "desc": "Yüklü model listesi"},
            {"endpoint": "/api/fine-tune", "method": "POST", "desc": "Fine-tuning başlat"},
            {"endpoint": "/v1/chat/completions", "method": "POST", "desc": "OpenAI uyumlu endpoint"},
        ],
        "external_apis": [
            {"name": "Hugging Face", "usage": "Model indirme"},
            {"name": "vLLM", "usage": "Yüksek performanslı inference"},
            {"name": "Ollama", "usage": "Yerel model yönetimi"},
        ],
        "services": ["LLM İnference", "Fine-tuning", "Embedding Üretimi", "Model Yönetimi", "OpenAI Uyumlu API"],
        "integrations": ["emare-asistan", "emarecode", "emaresetup", "siberemare"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["Self-hosted AI", "Fine-tuning", "OpenAI uyumlu API", "Çoklu model desteği"],
    },

    "emareos": {
        "role": "İşletim Sistemi Dervişi",
        "specialty": "NeuroKernel — AI-native işletim sistemi, Ring 0 AI çekirdeği",
        "internal_apis": [
            {"endpoint": "kernel_api", "method": "SYSCALL", "desc": "Kernel system call'ları"},
            {"endpoint": "neuroschedule", "method": "KERNEL", "desc": "AI-native süreç zamanlayıcı"},
        ],
        "external_apis": [],
        "services": ["NeuroKernel", "AI Scheduler", "Self-Optimizing", "Bare Metal Boot"],
        "integrations": ["emareai"],
        "ports": {"production": None, "local": None},
        "strengths": ["Ring 0 AI çekirdeği", "Rust ile yazılmış", "Self-optimizing zamanlayıcı"],
    },

    "emarecode": {
        "role": "Kod Üretici Dervişi",
        "specialty": "Cross-platform AI kod üretici — Multi-AI failover, doğal dil ile proje üretimi",
        "internal_apis": [
            {"endpoint": "/api/generate/code", "method": "POST", "desc": "Kod üret"},
            {"endpoint": "/api/generate/project", "method": "POST", "desc": "Proje iskeleti üret"},
            {"endpoint": "/api/models/status", "method": "GET", "desc": "AI model durumları"},
            {"endpoint": "/api/history", "method": "GET", "desc": "Üretim geçmişi"},
        ],
        "external_apis": [
            {"name": "Google Gemini AI", "usage": "Birincil kod üretici"},
            {"name": "OpenAI GPT-4o", "usage": "Failover AI motor"},
        ],
        "services": ["Kod Üretimi", "Proje İskeleti", "Multi-AI Failover", "Şablon Yönetimi"],
        "integrations": ["emaresetup", "emarehup"],
        "ports": {"production": 5000, "local": 5000},
        "strengths": ["Çoklu AI failover", "Doğal dil → proje", "Cross-platform"],
    },

    "emarecc": {
        "role": "Çağrı Merkezi Dervişi",
        "specialty": "OpenCC Çağrı Merkezi — Asterisk, tahsilat, AI transkripsiyon",
        "internal_apis": [
            {"endpoint": "/api/calls", "method": "CRUD", "desc": "Çağrı yönetimi"},
            {"endpoint": "/api/agents", "method": "GET", "desc": "Çağrı merkezi ajanları"},
            {"endpoint": "/api/wallboard", "method": "GET", "desc": "Gerçek zamanlı wallboard"},
            {"endpoint": "/api/transcribe", "method": "POST", "desc": "AI çağrı transkripsiyon"},
            {"endpoint": "/api/collection/campaigns", "method": "CRUD", "desc": "Tahsilat kampanyaları"},
        ],
        "external_apis": [
            {"name": "Asterisk AMI/ARI", "usage": "VoIP çağrı kontrolü"},
        ],
        "services": ["VoIP Çağrı Merkezi", "AI Transkripsiyon", "Screen Pop", "Wallboard", "Tahsilat Yönetimi"],
        "integrations": ["emare-finance", "emare-asistan"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Asterisk entegrasyonu", "AI transkripsiyon", "Gerçek zamanlı wallboard"],
    },

    "emare-vscode-asistan": {
        "role": "IDE Yoklama Dervişi",
        "specialty": "VS Code ayar senkronizasyon aracı",
        "internal_apis": [
            {"endpoint": "vscode_sync_cli", "method": "CLI", "desc": "Ayar senkronizasyonu"},
        ],
        "external_apis": [],
        "services": ["VS Code Ayar Senkronizasyonu", "Eklenti Yönetimi"],
        "integrations": ["emarecode"],
        "ports": {"production": None, "local": None},
        "strengths": ["Merkezi ayar yönetimi", "Çoklu VS Code desteği"],
    },

    "emareflow": {
        "role": "İş Akışı Otomasyon Dervişi",
        "specialty": "n8n benzeri React Flow tabanlı görsel iş akışı otomasyonu",
        "internal_apis": [
            {"endpoint": "/api/flows", "method": "CRUD", "desc": "İş akışı yönetimi"},
            {"endpoint": "/api/flows/{id}/execute", "method": "POST", "desc": "Akış çalıştır"},
            {"endpoint": "/api/nodes/registry", "method": "GET", "desc": "Kullanılabilir düğümler"},
            {"endpoint": "/api/executions", "method": "GET", "desc": "Çalıştırma geçmişi"},
        ],
        "external_apis": [],
        "services": ["Görsel Flow Builder", "22 Emare Proje Düğümü", "Otomasyon Motoru", "Yürütme Geçmişi"],
        "integrations": ["*"],  # Tüm Emare projeleri düğüm olarak
        "ports": {"production": None, "local": 3000},
        "strengths": ["React Flow görsel editör", "22 proje entegrasyonu", "Celery async yürütme"],
    },

    "emaresuperapp": {
        "role": "Süper Uygulama Dervişi",
        "specialty": "Tüm Emare hizmetlerini tek çatı altında birleştiren platform",
        "internal_apis": [
            {"endpoint": "/api/auth/login", "method": "POST", "desc": "JWT kimlik doğrulama"},
            {"endpoint": "/api/wallet", "method": "CRUD", "desc": "Dijital cüzdan"},
            {"endpoint": "/api/marketplace", "method": "GET", "desc": "Hizmet marketplaces"},
            {"endpoint": "/api/social/feed", "method": "GET", "desc": "Sosyal akış"},
            {"endpoint": "/api/analytics", "method": "GET", "desc": "Kullanıcı analitikleri"},
        ],
        "external_apis": [],
        "services": ["JWT Auth", "Dijital Cüzdan", "Marketplace", "Sosyal Platform", "Analitik"],
        "integrations": ["emare-asistan", "emare-finance", "emarepazar"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["Tek çatı altında 43 hizmet", "JWT/bcrypt güvenlik", "Modüler mimari"],
    },

    "emarefree": {
        "role": "Araştırma Dervişi",
        "specialty": "Dünya genelindeki ücretsiz hizmetleri araştıran ve toplayan sistem",
        "internal_apis": [
            {"endpoint": "free_cli", "method": "CLI", "desc": "Araştırma CLI"},
            {"endpoint": "/api/services", "method": "GET", "desc": "Bulunan hizmet listesi"},
            {"endpoint": "/api/scan", "method": "POST", "desc": "Yeni araştırma başlat"},
        ],
        "external_apis": [
            {"name": "GitHub API", "usage": "Açık kaynak hizmet tarama"},
            {"name": "Web Scraping", "usage": "7 kaynak tarama"},
        ],
        "services": ["Ücretsiz Hizmet Tarama", "20 Kategori", "1400+ Hizmet", "Otomatik İzleme"],
        "integrations": [],
        "ports": {"production": None, "local": None},
        "strengths": ["7 kaynak tarama", "20 kategori", "ThreadPool paralel tarama"],
    },

    "emareappliancedesk": {
        "role": "Teknik Servis Dervişi",
        "specialty": "Çok şubeli teknik servis ve cihaz onarım yönetim sistemi",
        "internal_apis": [
            {"endpoint": "/api/repairs", "method": "CRUD", "desc": "Onarım kayıtları"},
            {"endpoint": "/api/customers", "method": "CRUD", "desc": "Müşteri yönetimi"},
            {"endpoint": "/api/technicians", "method": "GET", "desc": "Teknisyen listesi"},
            {"endpoint": "/api/parts", "method": "CRUD", "desc": "Yedek parça stoku"},
            {"endpoint": "/api/invoices", "method": "CRUD", "desc": "Faturalama"},
        ],
        "external_apis": [],
        "services": ["Cihaz Onarım Takibi", "Müşteri Yönetimi", "Teknisyen Atama", "Yedek Parça", "Faturalama"],
        "integrations": ["emare-finance"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["Çok şubeli", "Laravel Breeze auth", "Onarım durumu takibi"],
    },

    "emareflux": {
        "role": "Veri Akışı Dervişi",
        "specialty": "Veri akışı ve olay tabanlı iş süreçleri otomasyon motoru",
        "internal_apis": [],
        "external_apis": [],
        "services": ["ETL Pipeline", "Event-Driven", "Kuyruk Yönetimi"],
        "integrations": ["emareflow"],
        "ports": {"production": None, "local": None},
        "strengths": ["Planlama aşamasında"],
    },

    "emaregithub": {
        "role": "GitHub Dervişi",
        "specialty": "Tüm Emare projelerini toplu GitHub'a repo oluşturup push eden otomasyon",
        "internal_apis": [
            {"endpoint": "github_cli", "method": "CLI", "desc": "Toplu repo yönetimi"},
            {"endpoint": "/api/repos", "method": "GET", "desc": "Repo listesi"},
            {"endpoint": "/api/webhooks/setup", "method": "POST", "desc": "Webhook kurulumu"},
            {"endpoint": "/api/push/all", "method": "POST", "desc": "Toplu push"},
        ],
        "external_apis": [
            {"name": "GitHub REST API", "usage": "Repo CRUD, webhook, push"},
            {"name": "GitHub Actions", "usage": "CI/CD pipeline"},
        ],
        "services": ["Toplu Repo Yönetimi", "Otomatik Push", "Webhook Kurulumu", "45/45 Repo Sync"],
        "integrations": ["emarecloud", "yazilim-ekibi"],
        "ports": {"production": None, "local": None},
        "strengths": ["45 repo otomatik yönetimi", "setup_webhooks.py", "Auto-deploy entegrasyonu"],
    },

    "emaregoogle": {
        "role": "Google Servis Dervişi",
        "specialty": "Google servisleri ve Google Cloud için otomasyon sistemi",
        "internal_apis": [
            {"endpoint": "/api/google/drive", "method": "CRUD", "desc": "Google Drive yönetimi"},
            {"endpoint": "/api/google/sheets", "method": "CRUD", "desc": "Google Sheets"},
            {"endpoint": "/api/google/gmail", "method": "POST", "desc": "Gmail otomasyonu"},
            {"endpoint": "/api/gcloud/instances", "method": "CRUD", "desc": "GCE instance yönetimi"},
        ],
        "external_apis": [
            {"name": "Google Drive API", "usage": "Dosya yönetimi"},
            {"name": "Google Sheets API", "usage": "Tablo yönetimi"},
            {"name": "Gmail API", "usage": "E-posta otomasyonu"},
            {"name": "Google Cloud Compute", "usage": "VM yönetimi"},
            {"name": "gcloud CLI", "usage": "Cloud altyapı yönetimi"},
        ],
        "services": ["12 Google Servisi", "Playwright Otomasyon", "Google Cloud Yönetimi", "HTTP API"],
        "integrations": ["emarecloud"],
        "ports": {"production": None, "local": 3131},
        "strengths": ["12 Google servisi desteği", "Playwright + WebKit", "gcloud CLI entegrasyonu"],
    },

    "emareidi": {
        "role": "Kimlik Yönetimi Dervişi",
        "specialty": "Merkezi kimlik ve erişim yönetimi (Identity Provider)",
        "internal_apis": [
            {"endpoint": "/api/auth/token", "method": "POST", "desc": "JWT token üret"},
            {"endpoint": "/api/users", "method": "CRUD", "desc": "Kullanıcı yönetimi"},
            {"endpoint": "/api/roles", "method": "CRUD", "desc": "Rol yönetimi (RBAC)"},
            {"endpoint": "/api/oauth2/authorize", "method": "GET", "desc": "OAuth2 yetkilendirme"},
        ],
        "external_apis": [],
        "services": ["SSO", "RBAC", "JWT/OAuth2", "Kullanıcı Yönetimi"],
        "integrations": ["*"],
        "ports": {"production": None, "local": None},
        "strengths": ["Planlama aşamasında — Merkezi kimlik alt yapısı"],
    },

    "emaresebil": {
        "role": "Ulaşım Dervişi",
        "specialty": "Araç paylaşımı ve mikromobilite platformu",
        "internal_apis": [],
        "external_apis": [],
        "services": ["Carpooling", "E-Scooter", "Güzergah Optimizasyonu"],
        "integrations": [],
        "ports": {"production": None, "local": None},
        "strengths": ["Planlama aşamasında"],
    },

    "emaretedarik": {
        "role": "Tedarik Zinciri Dervişi",
        "specialty": "Tedarik zinciri yönetim sistemi",
        "internal_apis": [
            {"endpoint": "/api/suppliers", "method": "CRUD", "desc": "Tedarikçi yönetimi"},
            {"endpoint": "/api/orders", "method": "CRUD", "desc": "Sipariş yönetimi"},
            {"endpoint": "/api/inventory", "method": "CRUD", "desc": "Stok takibi"},
        ],
        "external_apis": [],
        "services": ["Tedarikçi Yönetimi", "Sipariş Takibi", "Stok Yönetimi", "Maliyet Analizi"],
        "integrations": ["emare-finance"],
        "ports": {"production": None, "local": None},
        "strengths": ["Planlama aşamasında"],
    },

    "emare-dashboard": {
        "role": "Ekosistem İzleme Dervişi",
        "specialty": "Tüm Emare ekosistemini izleyen Flask tabanlı kontrol paneli",
        "internal_apis": [
            {"endpoint": "/", "method": "GET", "desc": "Dashboard ana sayfa"},
            {"endpoint": "/api/status", "method": "GET", "desc": "Genel durum"},
            {"endpoint": "/api/projects", "method": "GET", "desc": "Proje listesi"},
        ],
        "external_apis": [],
        "services": ["Ekosistem İzleme", "Proje Durumu", "Sağlık Kontrolü"],
        "integrations": ["yazilim-ekibi"],
        "ports": {"production": 5050, "local": 5050},
        "strengths": ["Basit Flask paneli", "Hızlı durum görünümü"],
    },

    "girhub": {
        "role": "Git Tarayıcı Dervişi",
        "specialty": "Git repo tarayıcı ve kod inceleme arayüzü",
        "internal_apis": [],
        "external_apis": [],
        "services": ["Repo Görüntüleme", "Diff Analizi", "Commit Geçmişi"],
        "integrations": ["emaregithub"],
        "ports": {"production": None, "local": None},
        "strengths": ["Planlama aşamasında"],
    },

    "sosyal-medya-yonetim-araci": {
        "role": "Sosyal Medya Dervişi",
        "specialty": "Sosyal medya hesaplarının merkezi yönetimi",
        "internal_apis": [
            {"endpoint": "/api/accounts", "method": "CRUD", "desc": "Hesap yönetimi"},
            {"endpoint": "/api/posts/schedule", "method": "POST", "desc": "İçerik zamanlama"},
            {"endpoint": "/api/analytics/social", "method": "GET", "desc": "Sosyal medya analitik"},
        ],
        "external_apis": [
            {"name": "Instagram Graph API", "usage": "Instagram yönetimi"},
            {"name": "Twitter/X API", "usage": "Tweet yönetimi"},
            {"name": "Facebook Graph API", "usage": "Sayfa yönetimi"},
        ],
        "services": ["İçerik Planlama", "Zamanlama", "Çoklu Platform", "Analitik"],
        "integrations": ["emare-makale"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Çoklu platform desteği", "Otomatik zamanlama"],
    },

    "emare-hosting": {
        "role": "Hosting Dervişi",
        "specialty": "Emare barındırma ve hosting altyapısı",
        "internal_apis": [
            {"endpoint": "/api/sites", "method": "CRUD", "desc": "Site yönetimi"},
            {"endpoint": "/api/domains", "method": "CRUD", "desc": "Domain yönetimi"},
        ],
        "external_apis": [],
        "services": ["Web Hosting", "Domain Yönetimi", "SSL"],
        "integrations": ["emarecloud"],
        "ports": {"production": None, "local": None},
        "strengths": ["emarecloud entegrasyonu"],
    },

    "emareintranet": {
        "role": "İç İletişim Dervişi",
        "specialty": "Emare iç iletişim ve intranet platformu",
        "internal_apis": [
            {"endpoint": "/api/posts", "method": "CRUD", "desc": "İç duyurular"},
            {"endpoint": "/api/messages", "method": "CRUD", "desc": "İç mesajlaşma"},
            {"endpoint": "/api/directory", "method": "GET", "desc": "Çalışan rehberi"},
        ],
        "external_apis": [],
        "services": ["İç Duyurular", "Mesajlaşma", "Çalışan Rehberi", "Doküman Paylaşımı"],
        "integrations": ["emare-team"],
        "ports": {"production": None, "local": 5000},
        "strengths": ["Flask tabanlı basit intranet"],
    },

    "emarecripto": {
        "role": "Kripto Dervişi",
        "specialty": "Kripto para ve blockchain entegrasyonu",
        "internal_apis": [
            {"endpoint": "/api/wallets", "method": "CRUD", "desc": "Cüzdan yönetimi"},
            {"endpoint": "/api/transactions", "method": "GET", "desc": "İşlem geçmişi"},
            {"endpoint": "/api/exchange/rates", "method": "GET", "desc": "Anlık kur bilgisi"},
        ],
        "external_apis": [
            {"name": "CoinGecko API", "usage": "Fiyat verileri"},
            {"name": "Blockchain RPC", "usage": "İşlem gönderimi"},
        ],
        "services": ["Cüzdan Yönetimi", "İşlem Takibi", "Kur İzleme"],
        "integrations": ["emare-token", "emare-finance"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["Blockchain entegrasyonu", "Çoklu chain desteği"],
    },

    "emarepazar": {
        "role": "Pazaryeri Dervişi",
        "specialty": "Emare ürün ve hizmet pazaryeri",
        "internal_apis": [
            {"endpoint": "/api/products", "method": "CRUD", "desc": "Ürün yönetimi"},
            {"endpoint": "/api/orders", "method": "CRUD", "desc": "Sipariş yönetimi"},
            {"endpoint": "/api/sellers", "method": "CRUD", "desc": "Satıcı yönetimi"},
            {"endpoint": "/api/payments", "method": "POST", "desc": "Ödeme işleme"},
        ],
        "external_apis": [
            {"name": "Stripe/PayTR", "usage": "Ödeme altyapısı"},
        ],
        "services": ["Ürün Yönetimi", "Sipariş Sistemi", "Satıcı Paneli", "Ödeme Entegrasyonu"],
        "integrations": ["emare-finance", "emaresuperapp"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["Çok satıcılı marketplace", "Ödeme entegrasyonu"],
    },

    "emareaimusic": {
        "role": "Müzik Üretim Dervişi",
        "specialty": "Yapay zeka destekli müzik üretim servisi",
        "internal_apis": [
            {"endpoint": "/api/generate/music", "method": "POST", "desc": "Müzik üret"},
            {"endpoint": "/api/tracks", "method": "GET", "desc": "Parça listesi"},
            {"endpoint": "/api/styles", "method": "GET", "desc": "Müzik stilleri"},
        ],
        "external_apis": [],
        "services": ["AI Müzik Üretimi", "Stil Seçimi", "Parça Yönetimi"],
        "integrations": ["emareai"],
        "ports": {"production": None, "local": 8000},
        "strengths": ["AI destekli müzik üretimi"],
    },

    "emare-token": {
        "role": "Token/Blockchain Dervişi",
        "specialty": "EMARE token ve blockchain kütüphanesi",
        "internal_apis": [
            {"endpoint": "token_lib", "method": "LIB", "desc": "Python token kütüphanesi"},
            {"endpoint": "/api/mint", "method": "POST", "desc": "Token mint"},
            {"endpoint": "/api/transfer", "method": "POST", "desc": "Token transfer"},
            {"endpoint": "/api/balance", "method": "GET", "desc": "Bakiye sorgula"},
        ],
        "external_apis": [],
        "services": ["Token Mint", "Transfer", "Bakiye Sorgulama", "Smart Contract"],
        "integrations": ["emarecripto"],
        "ports": {"production": None, "local": None},
        "strengths": ["Python pytest ile test edilen token sistemi"],
    },

    "emareapi": {
        "role": "API Dervişi — Merkezi API Koordinatörü",
        "specialty": "Tüm Emare servislerinin merkezi API gateway'i ve koordinasyon sistemi",
        "internal_apis": [
            {"endpoint": "/api/gateway/{service}/*", "method": "ANY", "desc": "API Gateway — tüm servislere proxy"},
            {"endpoint": "/api/registry", "method": "GET", "desc": "Kayıtlı servis listesi"},
            {"endpoint": "/api/registry/register", "method": "POST", "desc": "Yeni servis kaydet"},
            {"endpoint": "/api/health/all", "method": "GET", "desc": "Tüm servislerin sağlığı"},
            {"endpoint": "/api/rate-limit/config", "method": "CRUD", "desc": "Rate limiting ayarları"},
            {"endpoint": "/api/logs/access", "method": "GET", "desc": "Erişim logları"},
            {"endpoint": "/api/metrics", "method": "GET", "desc": "Prometheus metrikler"},
        ],
        "external_apis": [
            {"name": "Tüm Emare Servis API'leri", "usage": "Proxy ve yönlendirme"},
        ],
        "services": [
            "API Gateway", "Servis Registry", "Rate Limiting", "Sağlık Kontrolü",
            "Request Routing", "Metrik Toplama", "Erişim Logları", "Otomatik Failover"
        ],
        "integrations": ["*"],  # Tüm Emare servisleriyle
        "ports": {"production": None, "local": 9000},
        "strengths": [
            "Merkezi API gateway", "43 servis proxy", "Rate limiting",
            "Otomatik servis keşfi", "Failover mekanizması", "Prometheus metrikleri"
        ],
    },

    "emarewebdizayn": {
        "role": "Web Tasarım Dervişi",
        "specialty": "Web tasarım, UI/UX ve dijital ajans yönetim platformu",
        "internal_apis": [
            {"endpoint": "/api/projects", "method": "CRUD", "desc": "Tasarım projeleri"},
            {"endpoint": "/api/templates", "method": "GET", "desc": "UI şablonları"},
            {"endpoint": "/api/assets", "method": "CRUD", "desc": "Dijital varlık yönetimi"},
            {"endpoint": "/api/clients", "method": "CRUD", "desc": "Müşteri yönetimi"},
        ],
        "external_apis": [],
        "services": ["Tasarım Projeleri", "UI Şablonları", "Dijital Varlık Yönetimi", "Müşteri Paneli"],
        "integrations": ["emarecloud", "emare-hosting"],
        "ports": {"production": None, "local": 3000},
        "strengths": ["React + Next.js", "Tasarım odaklı platform"],
    },
}


def get_capabilities(dervish_id: str) -> Dict[str, Any]:
    """Belirli bir dervişin yeteneklerini döndür."""
    return DERVISH_CAPABILITIES.get(dervish_id, {})


def get_all_capabilities() -> Dict[str, Dict[str, Any]]:
    """Tüm dervişlerin yeteneklerini döndür."""
    return DERVISH_CAPABILITIES


def get_capabilities_summary() -> Dict[str, Any]:
    """Ekosistem yetenek özeti."""
    all_services = set()
    all_integrations = set()
    total_internal_apis = 0
    total_external_apis = 0

    for caps in DERVISH_CAPABILITIES.values():
        all_services.update(caps.get("services", []))
        for i in caps.get("integrations", []):
            if i != "*":
                all_integrations.add(i)
        total_internal_apis += len(caps.get("internal_apis", []))
        total_external_apis += len(caps.get("external_apis", []))

    return {
        "total_dervishes": len(DERVISH_CAPABILITIES),
        "total_services": len(all_services),
        "total_internal_apis": total_internal_apis,
        "total_external_apis": total_external_apis,
        "total_integrations": len(all_integrations),
        "roles": {did: c["role"] for did, c in DERVISH_CAPABILITIES.items()},
    }
