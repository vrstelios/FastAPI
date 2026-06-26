from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.database.schema import PostCreate, PostResponse, PostUpdate, PaginatedPostsResponse
from app.core.auth import CurrentUser
from app.services.posts_service import PostService

router = APIRouter()

async def get_post_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PostService:
    return PostService(db)

@router.get("", response_model=PaginatedPostsResponse)
async def get_posts(
    service: Annotated[PostService, Depends(get_post_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_posts(skip=skip, limit=limit)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.create_post(post_data, current_user.id)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.get_post_by_id(post_id)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int,
    post_data: PostCreate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.update_post_full(post_id, post_data, current_user.id)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.update_post_partial(post_id, post_data, current_user.id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    await service.delete_post(post_id, current_user.id)