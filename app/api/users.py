from logging import exception
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status, UploadFile, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.database.schema import (
    UserCreate, UserPublic, UserPrivate, UserUpdate, Token, PaginatedPostsResponse, ForgotPasswordRequest,
    ResetPasswordRequest, ChangePasswordRequest
)
from app.core.config import settings
from app.core.auth import CurrentUser
from app.services.users_service import UserService

router = APIRouter()

async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(db)

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: Annotated[UserService, Depends(get_user_service)]):
    return await service.create_user(user)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    from_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.authenticate_user(from_data.username, from_data.password)

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(request_data: ForgotPasswordRequest, background_tasks: BackgroundTasks,
                          service: Annotated[UserService, Depends(get_user_service)]):
    return await service.forgot_password(request_data, background_tasks)

@router.post("/reset-password", status_code=status.HTTP_202_ACCEPTED)
async def reset_password(request_data: ResetPasswordRequest, service: Annotated[UserService, Depends(get_user_service)]):
    return await service.reset_password(request_data)

@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(password_data: ChangePasswordRequest, current_user: CurrentUser,
                          service: Annotated[UserService, Depends(get_user_service)]):
    return await service.change_password(password_data, current_user)

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.get_user(user_id)

@router.get("/{user_id}/posts", response_model=PaginatedPostsResponse)
async def get_user_posts(user_id: int, service: Annotated[UserService, Depends(get_user_service)],
    skip: Annotated[int, Query(ge=0)] = 0, limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page,
):
    return await service.get_user_posts(user_id=user_id, skip=skip, limit=limit)

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int, user_update: UserUpdate, current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.update_user(user_id, user_update, current_user.id)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)]
):
    await service.delete_user(user_id, current_user.id)

@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(user_id: int, file: UploadFile, current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.upload_profile_picture(user_id, file, current_user)

@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(user_id: int, current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.delete_user_picture(user_id, current_user)