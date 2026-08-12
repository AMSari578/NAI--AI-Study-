from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.exams.router import router as exams_router
from app.modules.materials.reader import router as material_reader_router
from app.modules.materials.router import router as materials_router
from app.modules.planning.router import router as planning_router
from app.modules.review.router import router as review_router
from app.modules.study.library import router as study_library_router
from app.modules.study.router import router as study_router


api_router = APIRouter()

for router in (
    auth_router,
    materials_router,
    ai_router,
    study_library_router,
    dashboard_router,
    study_router,
    material_reader_router,
    review_router,
    planning_router,
    exams_router,
):
    api_router.include_router(router)
