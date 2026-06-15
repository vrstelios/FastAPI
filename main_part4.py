from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas import PostCreate, PostResponse

""" Pydantic Schemas - Request and Response Validation """

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
        {
            "id": 1,
            "author": "Stelios",
            "title": "FastAPI is Awesome",
            "content": "This framework is really easy to use and super fast.",
            "date_posted": "April 20, 2025",
        },
        {
            "id": 2,
            "author": "Stelios",
            "title": "Python is a Great for Web development",
            "content": "Python is a greate language for web development, and FastAPI  makes it even better.",
            "date_posted": "April 21, 2025",
        },
    ]

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts

@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    # take maximum Id from the list and create a new Id by adding 1 to it
    new_id = max(post["id"] for post in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "April 23m 2025",
    }
    posts.append(new_post)
    return new_post

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            title = post['title'][:50]
            return templates.TemplateResponse(
                request,
                "post.html",
                {"post": post, "title": title},
            )
    # json handling error
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    # json handling error
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

# html handling error
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please try again."
    )

    if request.url.path.startswith("/api"):
        return  JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return  templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message
        },
        status_code=exception.status_code,
    )

# handling validation errors
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()}
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
