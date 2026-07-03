from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user

@pytest.mark.anyio
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422
    assert "email" in response.text
    assert "password" in response.text

@pytest.mark.anyio
async def test_create_user_duplicat_email(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/api/users",
        json={
            "username": "different_usr",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"

@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    response = await client.post(
        "/api/users",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "image_path" in data
    assert "password" not in data
    assert "password" not in data
    assert "password_hash" not in data

@pytest.mark.anyio
async def test_upload_profile_picture(client: AsyncClient, mocker):
    user = await create_test_user(client)
    token = await login_user(client)

    test_image_path = Path(__file__).parent.parent / "test_image.jpg"
    image_bytes = test_image_path.read_bytes()

    mock_oracle_response = MagicMock()
    mock_oracle_response.status_code = 200

    mock_put = mocker.patch("app.utils.image.http_client.put", return_value=mock_oracle_response)

    response = await client.patch(
        f"/api/users/{user['id']}/picture",
        files={"file": ("profile.jpg", BytesIO(image_bytes), 'image/jpeg')},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["image_file"] is not None
    assert data["image_file"].endswith(".jpg")

    assert "oraclecloud.com" in data["image_path"]
    assert data["image_path"].endswith(".jpg")
    mock_put.assert_called_once()

    _, called_kwargs = mock_put.call_args
    assert called_kwargs["content"] is not None
    assert len(called_kwargs["content"]) > 0

@pytest.mark.anyio
async def test_forgot_password_sends_email(client: AsyncClient, mocker):
    await create_test_user(client)

    mock_send = mocker.patch(
        "app.services.users_service.send_password_reset_email",
        new_callable=AsyncMock
    )

    response = await client.post(
        "/api/users/forgot-password",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 202
    mock_send.assert_awaited_once()
    _, call_kwargs = mock_send.call_args
    assert call_kwargs["to_email"] == "test@example.com"
    assert call_kwargs["username"] == "testuser"
    assert "token" in call_kwargs