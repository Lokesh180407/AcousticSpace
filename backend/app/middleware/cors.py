from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI, origins_csv: str) -> None:
    """Add CORS middleware.

    Args:
        app: FastAPI app.
        origins_csv: Comma-separated list of origins.
    """
    origins = [o.strip() for o in origins_csv.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

