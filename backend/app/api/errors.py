from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": jsonable_encoder(exc.errors(), custom_encoder={ValueError: str})}})

    @app.exception_handler(IntegrityError)
    async def integrity_error(_: Request, __: IntegrityError):
        return JSONResponse(status_code=409, content={"success": False, "error": {"code": "DUPLICATE_OR_INVALID_REFERENCE", "message": "A unique value already exists or a referenced record is invalid", "details": {}}})
