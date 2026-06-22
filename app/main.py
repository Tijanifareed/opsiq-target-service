from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import os

# Logging setup — writes to logs/app.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("target-service")

app = FastAPI(title="OpsIQ Target Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# HEALTHY endpoint — proof the service is live
@app.get("/health")
def health():
    return {"status": "ok"}


# BROKEN endpoint 1 — NullPointerError
# Missing null check on user_id
@app.get("/users/{user_id}")
def get_user(user_id: str):
    logger.error(f"NullPointerError: user_id '{user_id}' resolved to None during DB lookup")
    raise HTTPException(
        status_code=500,
        detail="NullPointerError: user_id resolved to None during DB lookup"
    )


# BROKEN endpoint 2 — DB connection timeout
@app.get("/orders")
def get_orders():
    logger.error("DBConnectionError: connection timeout after 30s — pool exhausted")
    raise HTTPException(
        status_code=500,
        detail="DBConnectionError: connection timeout after 30s — pool exhausted"
    )


# BROKEN endpoint 3 — Infinite loop / timeout
@app.get("/reports")
def get_reports():
    logger.error("TimeoutError: report generation exceeded 60s limit — possible infinite loop in aggregation")
    raise HTTPException(
        status_code=500,
        detail="TimeoutError: report generation exceeded 60s limit"
    )


# BROKEN endpoint 4 — Auth misconfiguration
@app.get("/admin")
def get_admin():
    logger.error("AuthConfigError: JWT secret is None — AUTH_SECRET env var not set")
    raise HTTPException(
        status_code=500,
        detail="AuthConfigError: JWT secret is None — AUTH_SECRET env var not set"
    )


# BROKEN endpoint 5 — Memory leak
@app.get("/exports")
def get_exports():
    logger.error("MemoryError: heap allocation failed — possible memory leak in export buffer")
    raise HTTPException(
        status_code=500,
        detail="MemoryError: heap allocation failed during export"
    )


# Log fetcher endpoint — OpsIQ agent calls this
# Returns last N lines of the log file
@app.get("/logs")
def get_logs(lines: int = 50):
    try:
        with open("logs/app.log", "r") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
            return {"logs": "".join(recent)}
    except FileNotFoundError:
        return {"logs": ""}