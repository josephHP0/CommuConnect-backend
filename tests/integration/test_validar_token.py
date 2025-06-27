import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestValidarToken:
    """Tests para el endpoint de validación de token"""

    def test_validar_token_sin_token_retorna_401(self, client: TestClient):
        """Test: Sin token debe retornar 401 Unauthorized"""
        response = client.get("/api/auth/validar-token")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.text or "Unauthorized" in response.text

    def test_validar_token_con_token_invalido_retorna_401(self, client: TestClient):
        """Test: Con token inválido debe retornar 401 Unauthorized"""
        headers = {"Authorization": "Bearer token_invalido_123"}
        response = client.get("/api/auth/validar-token", headers=headers)
        
        assert response.status_code == 401

    def test_validar_token_con_token_valido_retorna_200(self, client: TestClient, test_user_token: str):
        """Test: Con token válido debe retornar 200 OK con datos del usuario"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        response = client.get("/api/auth/validar-token", headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
        assert isinstance(data["user_id"], int)

    @pytest.mark.asyncio
    async def test_validar_token_async_con_admin_token(self, async_client: AsyncClient, admin_token: str):
        """Test asíncrono: Con token de admin debe retornar 200 OK"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = await async_client.get("/api/auth/validar-token", headers=headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
        assert isinstance(data["user_id"], int)

    def test_validar_token_formato_header_incorrecto(self, client: TestClient, test_user_token: str):
        """Test: Header de autorización con formato incorrecto debe retornar 401"""
        # Sin "Bearer"
        headers = {"Authorization": test_user_token}
        response = client.get("/api/auth/validar-token", headers=headers)
        
        assert response.status_code == 401 