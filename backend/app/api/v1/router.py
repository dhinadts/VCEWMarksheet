from fastapi import APIRouter

from app.api.v1.routes import academic, auth, marksheets, ocr, student_portal, submissions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(academic.router, tags=["academic"])
api_router.include_router(marksheets.router, prefix="/marksheets", tags=["marksheets"])
api_router.include_router(ocr.router, tags=["ocr"])
api_router.include_router(student_portal.router, prefix="/student-portal", tags=["student portal"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
