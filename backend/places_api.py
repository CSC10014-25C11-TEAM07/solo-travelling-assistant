"""F01 contract: GET recommendations, repeated interests, authenticated, max 3."""

from functools import lru_cache
from importlib import import_module
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from place_catalog import PlaceCatalog
from place_models import INTEREST_LABELS

router = APIRouter(prefix="/api/v1/places", tags=["Gợi ý địa điểm F01"])
bearer = HTTPBearer(auto_error=False)


def authenticate(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        return JSONResponse(status_code=401, content={
            "code": "AUTH_REQUIRED", "message": "Vui lòng đăng nhập.",
        })
    try:
        auth = import_module("auth")
    except ModuleNotFoundError as error:
        if error.name != "auth":
            raise
        # PR #12 owns authentication. Fail closed until it is available.
        return JSONResponse(status_code=503, content={
            "code": "AUTH_NOT_READY", "message": "Dịch vụ tài khoản chưa được ghép.",
        })
    return auth.session_response(credentials)


@lru_cache(maxsize=1)
def get_catalog():
    return PlaceCatalog.load()


class Recommendation(BaseModel):
    place_id: str
    name: str
    image_url: str | None
    reason: str


class Recommendations(BaseModel):
    places: list[Recommendation]


@router.get("/recommendations", response_model=Recommendations, responses={
    401: {"description": "Phiên đăng nhập không hợp lệ hoặc thiếu Bearer token"},
    422: {"description": "VALIDATION_ERROR, field interests"},
    503: {"description": "Dịch vụ tài khoản chưa được ghép"},
})
def recommendations(
    interests: Annotated[list[str] | None, Query(description=(
        "Mã sở thích; lặp interests cho nhiều lựa chọn: nature, coffee, culture, food"
    ))] = None,
    account=Depends(authenticate),
    catalog: PlaceCatalog = Depends(get_catalog),
):
    if isinstance(account, JSONResponse):
        return account
    if not interests or any(value not in INTEREST_LABELS for value in interests):
        return JSONResponse(status_code=422, content={
            "code": "VALIDATION_ERROR",
            "message": "Chọn ít nhất một sở thích hợp lệ: nature, coffee, culture, food.",
            "field": "interests",
        })
    return catalog.recommend(interests)
