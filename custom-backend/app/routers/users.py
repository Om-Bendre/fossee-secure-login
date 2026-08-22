from fastapi import APIRouter, Depends
from ..deps import get_current_user
from ..models import User

router = APIRouter()

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "profile": {
            "fullName": current_user.full_name,
            "displayName": current_user.display_name,
            "bio": current_user.bio,
            "role": current_user.role,
        },
    }
