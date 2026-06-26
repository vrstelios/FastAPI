from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status, UploadFile
from PIL import UnidentifiedImageError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import selectinload

from app.models import models
from app.core.config import settings
from app.utils.image_utils import delete_profile_image, process_profile_image
from app.database.schema import (
    UserCreate, UserUpdate, Token, PaginatedPostsResponse, PostResponse
)
from app.core.auth import (
    hash_password, verify_password, create_access_token
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> models.User:
        result = await self.db.execute(
            # database query
            select(models.User).where(func.lower(models.User.username) == user_data.username.lower()),
        )
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        result = await self.db.execute(
            select(models.User).where(func.lower(models.User.email) == user_data.email.lower()),
        )
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

        new_user = models.User(
            username=user_data.username,
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, username_email: str, password: str) -> Token:
        # Look up user by email (case-insensitive)
        # Note: OAuth2PasswordRequestFrom uses "username" field, but we treat it as email
        result = await self.db.execute(
            select(models.User).where(func.lower(models.User.email) == username_email.lower()),
        )
        user = result.scalars().first()

        # Verify user exist and password is correct
        # Don't reveal which oe failed (security best practice)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token with user id as subject
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )

        return Token(access_token=access_token, token_type="bearer")

    async def get_user(self, user_id: int) -> models.User:
        result = await self.db.execute(
            # database query
            select(models.User).where(models.User.id == user_id)
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    async def get_user_posts(self, user_id: int, skip: int, limit: int) -> PaginatedPostsResponse:
        await self.get_user_by_id(user_id)

        count_result = await self.db.execute(
            select(func.count()).select_from(models.Post).where(models.Post.user_id == user_id),
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .where(models.Post.user_id == user_id)
            .order_by(models.Post.date_posted.desc())
            .offset(skip)
            .limit(limit),
        )
        posts = result.scalars().all()

        has_more = skip + len(posts) < total

        return PaginatedPostsResponse(
            posts=[PostResponse.model_validate(post) for post in posts],
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more,
        )

    async def update_user(self, user_id: int, user_update: UserUpdate, current_user_id: int) -> models.User:
        if user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

        user = await self.get_user_by_id(user_id)

        if user_update.username is not None and user_update.username.lower() != user.username.lower():
            result = await self.db.execute(
                select(models.User).where(func.lower(models.User.username) == user_update.username.lower()),
            )
            if result.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
            user.username = user_update.username

        if user_update.email is not None and user_update.email.lower() != user.email.lower():
            result = await self.db.execute(
                select(models.User).where(func.lower(models.User.email) == user_update.email.lower()),
            )
            if result.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
            user.email = user_update.email.lower()

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: int, current_user_id: int) -> None:
        if user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user")

        user = await self.get_user_by_id(user_id)
        old_filename = user.image_file

        await self.db.delete(user)
        await self.db.commit()

        if old_filename:
            delete_profile_image(old_filename)

    async def upload_profile_picture(self, user_id: int, file: UploadFile, current_user: models.User) -> models.User:
        if current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user's picture")

        content = await file.read()
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
            )

        try:
            new_filename = await run_in_threadpool(process_profile_image, content)
        except UnidentifiedImageError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
            ) from err

        old_filename = current_user.image_file
        current_user.image_file = new_filename

        await self.db.commit()
        await self.db.refresh(current_user)

        # first save the image and after delete it, protect more from fail save
        if old_filename:
            delete_profile_image(old_filename)

        return current_user

    async def delete_user_picture(self, user_id: int, current_user: models.User) -> models.User:
        if current_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this user's picture")

        old_filename = current_user.image_file
        if old_filename is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No profile picture to delete")

        current_user.image_file = None
        await self.db.commit()
        await self.db.refresh(current_user)

        delete_profile_image(old_filename) # delete the file

        return current_user