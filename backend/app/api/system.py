"""System APIs."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    """Basic health-check endpoint."""
    return {"code": 0, "message": "success", "data": {"status": "ok"}}

