from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models
from app.database.schema import PostCreate, PostUpdate, PostResponse, PaginatedPostsResponse


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_posts(self, skip: int, limit: int) -> PaginatedPostsResponse:
        count_result = await self.db.execute(select(func.count()).select_from(models.Post))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
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

    async def create_post(self, post_data: PostCreate, user_id: int) -> models.Post:
        # (old_code) take maximum Id from the list and create a new Id by adding 1 to it
        # new_id = max(post["id"] for post in posts) + 1 if posts else 1
        new_post = models.Post(
            title=post_data.title,
            content=post_data.content,
            user_id=user_id,
        )
        self.db.add(new_post)
        await self.db.commit()
        await self.db.refresh(new_post, attribute_names=["author"])
        return new_post

    async def get_post_by_id(self, post_id: int) -> models.Post:
        result = await self.db.execute(
            select(models.Post)
            .options(selectinload(models.Post.author))
            .where(models.Post.id == post_id)
        )
        post = result.scalars().first()
        if not post:
            # json handling error
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        return post

    async def update_post_full(self, post_id: int, post_data: PostCreate, user_id: int) -> models.Post:
        post = await self.get_post_by_id(post_id)

        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

        # update all the fields from post!
        post.title = post_data.title
        post.content = post_data.content

        await self.db.commit()
        await self.db.refresh(post, attribute_names=["author"])
        return post

    async def update_post_partial(self, post_id: int, post_data: PostUpdate, user_id: int) -> models.Post:
        post = await self.get_post_by_id(post_id)

        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")

        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        await self.db.commit()
        await self.db.refresh(post, attribute_names=["author"])
        return post

    async def delete_post(self, post_id: int, user_id: int) -> None:
        post = await self.get_post_by_id(post_id)

        if post.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")

        await self.db.delete(post)
        await self.db.commit()