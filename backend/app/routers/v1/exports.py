from fastapi import APIRouter

router = APIRouter(prefix="/exports", tags=["exports"])

@router.get("/")
def get_exports():
    return {"message": "Exports API"}
