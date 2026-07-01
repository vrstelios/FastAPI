import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

from app.models import models
from app.core.database import AsyncSessionLocal, engine
from app.main_part16 import app

POPULATE_IMAGES_DIR = Path("populate_images")

USERS = [
    {
        "username": "vrstelios",
        "email": "vrstelios@gmail.com",
        "password": "TestPassword1!",
        "image": "vr.png",
    },
    {
        "username": "DefaultDude",
        "email": "TestEmail2@test.com",
        "password": "TestPassword2!",
        # No image - uses default
    },
    {
        "username": "gopher",
        "email": "TestGopher@test.com",
        "password": "TestPassword3!",
        "image": "gopher.png",
    },
    {
        "username": "favicon-gopher",
        "email": "TestFaviconGopher@test.com",
        "password": "TestPassword4!",
        "image": "favicon-gopher.png",
    },
    {
        "username": "stick",
        "email": "TestStixk@test.com",
        "password": "TestPassword5!",
        "image": "stick.png",
    },
    {
        "username": "log",
        "email": "Testlog@test.com",
        "password": "TestPassword6!",
        "image": "log.png",
    },
]

POSTS = [
    {
        "title": "Why Golang is So Popular",
        "content": "Go combines simplicity, performance, and reliability. Its fast compilation times and efficient concurrency model make it a favorite for modern backend services."
    },
    {
        "title": "Getting Started with Go Modules",
        "content": "Go Modules make dependency management easy. Initialize a project with 'go mod init' and let Go handle versioning automatically."
    },
    {
        "title": "Understanding Goroutines",
        "content": "Goroutines are lightweight threads managed by the Go runtime. You can launch thousands of them with minimal overhead."
    },
    {
        "title": "Channels Explained",
        "content": "Channels provide safe communication between goroutines. They help avoid shared memory issues and simplify concurrent programming."
    },
    {
        "title": "Why Go Compiles So Fast",
        "content": "Go was designed for developer productivity. Incremental builds and a streamlined compiler allow projects to compile in seconds."
    },
    {
        "title": "Error Handling in Go",
        "content": "Go favors explicit error handling. Returning errors as values makes failures visible and encourages developers to handle them properly."
    },
    {
        "title": "Structs are Powerful",
        "content": "Structs allow you to group related data together. Combined with methods, they provide a clean way to model business logic."
    },
    {
        "title": "Interfaces in Golang",
        "content": "Interfaces define behavior rather than implementation. They help keep code flexible, testable, and loosely coupled."
    },
    {
        "title": "Building REST APIs with Gin",
        "content": "Gin is one of the most popular frameworks for Go. It offers excellent performance, middleware support, and a simple API."
    },
    {
        "title": "Fiber: Fast and Minimal",
        "content": "Fiber is inspired by Express.js but built for Go. It focuses on speed and developer productivity."
    },
    {
        "title": "Dependency Injection in Go",
        "content": "Go often relies on constructor injection. Passing dependencies explicitly keeps code simple and easy to test."
    },
    {
        "title": "Working with JSON",
        "content": "The encoding/json package provides powerful tools for marshaling and unmarshaling JSON data with minimal code."
    },
    {
        "title": "Context Package Essentials",
        "content": "The context package is used to manage deadlines, cancellation signals, and request-scoped values across API boundaries."
    },
    {
        "title": "Concurrency Done Right",
        "content": "Go's concurrency primitives make writing scalable applications easier. Goroutines and channels help manage workloads efficiently."
    },
    {
        "title": "Slices vs Arrays",
        "content": "Arrays have fixed sizes while slices provide dynamic behavior. In practice, slices are used much more frequently."
    },
    {
        "title": "Maps in Golang",
        "content": "Maps offer efficient key-value storage and are commonly used for caching, indexing, and configuration data."
    },
    {
        "title": "Testing in Go",
        "content": "Go includes built-in testing support. Simply create files ending with _test.go and run tests using 'go test'."
    },
    {
        "title": "Benchmarking Applications",
        "content": "Go provides benchmarking capabilities out of the box. Benchmarks help identify performance bottlenecks early."
    },
    {
        "title": "Building CLI Applications",
        "content": "Go is excellent for command-line tools thanks to its fast execution speed and single binary deployment."
    },
    {
        "title": "Cross Platform Compilation",
        "content": "Go allows developers to compile applications for Linux, Windows, and macOS without changing code."
    },
    {
        "title": "Working with PostgreSQL",
        "content": "Go integrates well with PostgreSQL using libraries like pgx and GORM for database access."
    },
    {
        "title": "Redis with Golang",
        "content": "Redis is commonly used alongside Go applications for caching, queues, and session management."
    },
    {
        "title": "Why Developers Love Go",
        "content": "Go prioritizes readability and maintainability. The language intentionally avoids unnecessary complexity."
    },
    {
        "title": "Go Routines Everywhere",
        "content": "Launching a goroutine requires only the 'go' keyword. This simplicity encourages concurrent application design."
    },
    {
        "title": "WebSockets in Go",
        "content": "Libraries like Gorilla WebSocket make it easy to build chat systems, notifications, and real-time dashboards."
    },
    {
        "title": "Microservices with Golang",
        "content": "Go's performance and low memory footprint make it ideal for microservice architectures."
    },
    {
        "title": "Building APIs with net/http",
        "content": "The standard library includes a robust HTTP package capable of handling production workloads."
    },
    {
        "title": "Middleware Patterns",
        "content": "Middleware is commonly used for authentication, logging, metrics collection, and request validation."
    },
    {
        "title": "Configuration Management",
        "content": "Environment variables are widely used in Go applications to manage secrets and deployment settings."
    },
    {
        "title": "Go and Docker",
        "content": "Go applications compile into static binaries, making them ideal candidates for lightweight Docker images."
    },
    {
        "title": "Containerizing Services",
        "content": "Using multi-stage Docker builds can drastically reduce image sizes and improve deployment speed."
    },
    {
        "title": "Learning Generics",
        "content": "Generics introduced in Go 1.18 provide reusable abstractions while preserving performance and type safety."
    },
    {
        "title": "Understanding Pointers",
        "content": "Pointers allow functions to modify data in place and help avoid unnecessary memory allocations."
    },
    {
        "title": "Package Organization",
        "content": "Keeping packages focused and cohesive improves maintainability and encourages reusable components."
    },
    {
        "title": "Go for Cloud Native Development",
        "content": "Many cloud-native tools including Kubernetes, Docker, and Prometheus are written in Go."
    },
    {
        "title": "Logging Best Practices",
        "content": "Structured logging improves observability and simplifies debugging in distributed systems."
    },
    {
        "title": "Graceful Shutdowns",
        "content": "Handling termination signals correctly ensures active requests complete before services stop."
    },
    {
        "title": "Performance Profiling",
        "content": "Go includes pprof for analyzing CPU usage, memory allocations, and execution bottlenecks."
    },
    {
        "title": "Working with gRPC",
        "content": "gRPC provides high-performance communication between services using Protocol Buffers."
    },
    {
        "title": "Go and Kubernetes",
        "content": "The Kubernetes ecosystem is heavily influenced by Go, making it an excellent language for cloud engineers."
    },
    {
        "title": "Building Scalable Systems",
        "content": "Go excels at handling thousands of concurrent connections, making it perfect for scalable backend systems."
    },
    {
        "title": "Code Formatting with gofmt",
        "content": "The gofmt tool automatically formats source code, ensuring consistent style across projects."
    },
    {
        "title": "Managing Dependencies",
        "content": "Go Modules simplify package management and make reproducible builds much easier."
    },
    {
        "title": "Why Go is Here to Stay",
        "content": "Go continues to grow in popularity due to its excellent tooling, strong ecosystem, and focus on simplicity."
    }
]

# The 44th post - always the oldest (easter egg for pagination tutorial)
POST_44 = {
    "title": "Fun Fact About Golang",
    "content": "Go was created at Google by Robert Griesemer, Rob Pike, and Ken Thompson. It was designed to simplify software engineering at scale while maintaining excellent performance and developer productivity."
}

async def clear_existing_data() -> None:
    # Clear database tables (order respects foreign keys)
    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.PasswordResetToken))
        await db.execute(delete(models.Post))
        await db.execute(delete(models.User))
        await db.commit()
    print("Cleared existing data from database")

async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Post).order_by(models.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        # First post (POST_44) is the oldest - ~90 days ago
        await db.execute(
            update(models.Post)
            .where(models.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        # Remaining posts: each ~1.5 days newer than previous
        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24
            post_date = now - timedelta(days=days_ago, hours=hours_offset)
            await db.execute(
                update(models.Post)
                .where(models.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()
    print("Updated post dates")

async def populate() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport, base_url="http://localhost",
    ) as client:
        # Clear existing data (local images first, then database)
        await clear_existing_data()

        users: list[dict] = []

        print(f"\nCreating {len(USERS)} users...")
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            user = response.json()
            print(f"  Created: {user['username']}")

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            response.raise_for_status()
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name
                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    print(f"    Uploaded: {image_name}")

            users.append(
                {"id": user["id"], "username": user["username"], "token": token},
            )

        print(f"\nCreating {len(POSTS) + 1} posts...")

        # First create POST_44 (will become oldest after date update)
        response = await client.post(
            "/api/posts",
            json={"title": POST_44["title"], "content": POST_44["content"]},
            headers={"Authorization": f"Bearer {users[0]['token']}"},
        )
        response.raise_for_status()
        print(f"  Created: '{POST_44['title']}'")

        # Create remaining posts in reverse (last in list = oldest, first = newest)
        for i, post_data in enumerate(reversed(POSTS)):
            user = users[i % len(users)]
            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            response.raise_for_status()
            title = post_data["title"]
            print(
                f"  Created: '{title[:50]}...'"
                if len(title) > 50
                else f"  Created: '{title}'",
            )

        print("\nUpdating post dates...")
        await update_post_dates()

    await engine.dispose()

    print("\nDone!")
    print(f"  {len(USERS)} users")
    print(f"  {len(POSTS) + 1} posts")
    print("  Profile pictures saved locally")

if __name__ == "__main__":
    asyncio.run(populate())
