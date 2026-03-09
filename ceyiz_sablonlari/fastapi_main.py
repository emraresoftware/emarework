# {{PROJE_AD}} — FastAPI Giriş Noktası

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.core.app:create_app",
        host="0.0.0.0",
        port={{PROJE_PORT}},
        reload=True,
        factory=True,
    )
