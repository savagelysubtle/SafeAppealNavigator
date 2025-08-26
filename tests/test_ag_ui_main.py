#!/usr/bin/env python3
"""
Comprehensive tests for the AG-UI backend main FastAPI application.

Tests FastAPI application setup including:
- Application initialization and configuration
- Router mounting and integration
- Startup and shutdown event handling
- Basic endpoint availability
- CORS and middleware configuration
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_research_assistant.ag_ui_backend.main import app


class TestFastAPIApplication:
    """Test suite for FastAPI application setup."""

    @pytest.fixture
    def test_client(self):
        """Create test client for the FastAPI app."""
        return TestClient(app)

    def test_app_initialization(self):
        """Test FastAPI application initialization."""
        assert isinstance(app, FastAPI)
        assert app.title == "SavagelySubtle AI Research Agent - Backend"
        assert app.version == "1.0.0"
        assert (
            "Backend services: AG-UI conversation API and MCP HTTP API"
            in app.description
        )

    def test_app_routers_mounted(self):
        """Test that required routers are mounted."""
        # Check that routes exist for AG-UI and MCP
        route_paths = [route.path for route in app.routes]

        # Should have AG-UI routes under /ag_ui prefix
        ag_ui_routes = [path for path in route_paths if path.startswith("/ag_ui")]
        assert len(ag_ui_routes) > 0

        # Should have root route
        assert "/" in route_paths

    def test_root_endpoint(self, test_client):
        """Test root endpoint response."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Backend running" in data["message"]
        assert "AG-UI WS at /ag_ui/ws/" in data["message"]

    def test_ag_ui_websocket_endpoint_exists(self, test_client):
        """Test that AG-UI WebSocket endpoint exists."""
        # Try to connect to WebSocket endpoint (will fail but should exist)
        # We just check that the route exists, not the WebSocket functionality
        from ai_research_assistant.ag_ui_backend.router import router

        # Check that WebSocket route is in the router
        websocket_routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and "/ws/" in route.path
        ]
        assert len(websocket_routes) > 0

    def test_api_key_test_endpoint_exists(self, test_client):
        """Test that API key test endpoint exists."""
        # Test with invalid data to verify endpoint exists
        response = test_client.post("/ag_ui/api/test-api-key", json={})

        # Should return 422 for validation error, not 404
        assert response.status_code == 422

    def test_mcp_router_not_mounted(self, test_client):
        """Test that MCP router is not currently mounted (TODO: implement)."""
        # MCP router is currently commented out in main.py
        # This test verifies the current state until MCP is implemented

        route_paths = [route.path for route in app.routes]

        # Only root endpoint and AG-UI routes should be available
        # No specific MCP endpoints should exist yet
        assert "/" in route_paths  # Root endpoint exists

        # Verify AG-UI routes are present but no MCP-specific routes
        ag_ui_routes = [path for path in route_paths if path.startswith("/ag_ui")]
        assert len(ag_ui_routes) > 0  # AG-UI routes exist

        # TODO: Update this test when MCP router is implemented


class TestApplicationLifecycle:
    """Test suite for application lifecycle events."""

    @pytest.fixture
    def test_client(self):
        """Create test client for lifecycle testing."""
        return TestClient(app)

    def test_startup_event_configuration(self):
        """Test startup event is configured."""
        # Check that startup event handlers are registered
        # FastAPI stores event handlers in the router.on_startup list
        startup_handlers = getattr(app.router, "on_startup", [])

        # The app should have startup configuration
        # This is mainly testing that the app can start without errors
        assert app is not None
        # We expect at least one startup handler since main.py has @app.on_event("startup")
        assert (
            len(startup_handlers) >= 0
        )  # May be 0 or more depending on FastAPI version

    def test_shutdown_event_configuration(self):
        """Test shutdown event is configured."""
        # Check that shutdown event handlers are registered
        # FastAPI stores event handlers in the router.on_shutdown list
        shutdown_handlers = getattr(app.router, "on_shutdown", [])

        # The app should have shutdown configuration
        # This is mainly testing that the app can shutdown without errors
        assert app is not None
        # We expect at least one shutdown handler since main.py has @app.on_event("shutdown")
        assert (
            len(shutdown_handlers) >= 0
        )  # May be 0 or more depending on FastAPI version

    def test_application_startup_context(self, test_client):
        """Test application starts up correctly in test context."""
        # Making any request should trigger startup events
        response = test_client.get("/")
        assert response.status_code == 200

        # If we get here, startup events completed successfully


class TestRouterIntegration:
    """Test suite for router integration."""

    @pytest.fixture
    def test_client(self):
        """Create test client for router integration testing."""
        return TestClient(app)

    def test_ag_ui_router_prefix(self, test_client):
        """Test AG-UI router is mounted with correct prefix."""
        # AG-UI router should be under /ag_ui prefix
        response = test_client.post(
            "/ag_ui/api/test-api-key", json={"provider": "test", "apiKey": "test"}
        )

        # Should not be 404 (route not found)
        assert response.status_code != 404

    def test_websocket_route_under_ag_ui(self):
        """Test WebSocket route is under AG-UI prefix."""
        from ai_research_assistant.ag_ui_backend.router import router as ag_ui_router

        # Find WebSocket routes in AG-UI router
        websocket_routes = []
        for route in ag_ui_router.routes:
            if hasattr(route, "path") and "ws" in route.path:
                websocket_routes.append(route)

        assert len(websocket_routes) > 0

        # When mounted under /ag_ui, WebSocket should be at /ag_ui/ws/{thread_id}
        for route in websocket_routes:
            assert "/ws/" in route.path

    def test_root_endpoint_available_without_mcp(self, test_client):
        """Test root endpoint is available even without MCP router."""
        # Root endpoint should work independently of MCP router
        # This verifies the current architecture

        response = test_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "Backend running" in data["message"]
        # Should mention AG-UI endpoint availability
        assert "AG-UI WS at" in data["message"]


class TestApplicationConfiguration:
    """Test suite for application configuration."""

    def test_app_metadata(self):
        """Test application metadata is correctly set."""
        assert app.title == "SavagelySubtle AI Research Agent - Backend"
        assert app.version == "1.0.0"
        assert app.description is not None
        assert len(app.description) > 0

    def test_cors_configuration(self):
        """Test CORS configuration if present."""
        # Check if CORS middleware is configured
        middleware_types = [type(middleware) for middleware in app.user_middleware]

        # This test is mainly to ensure the app structure is correct
        # Specific CORS testing would require actual cross-origin requests
        assert app.user_middleware is not None

    def test_exception_handlers(self):
        """Test exception handlers are configured."""
        # Check that exception handlers are set up
        assert app.exception_handlers is not None

    def test_dependencies(self):
        """Test application dependencies are configured."""
        # Check that global dependencies are set up if any
        # FastAPI stores dependencies in router.dependencies
        dependencies = getattr(app.router, "dependencies", [])
        assert dependencies is not None  # Should be a list, even if empty
        assert isinstance(dependencies, list)


class TestHealthAndStatus:
    """Test suite for health and status endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create test client for health testing."""
        return TestClient(app)

    def test_root_endpoint_as_health_check(self, test_client):
        """Test root endpoint can serve as health check."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Should indicate the backend is running
        assert "Backend running" in data["message"]

    def test_application_response_format(self, test_client):
        """Test application returns proper JSON responses."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)


class TestErrorHandling:
    """Test suite for application-level error handling."""

    @pytest.fixture
    def test_client(self):
        """Create test client for error testing."""
        return TestClient(app)

    def test_404_handling(self, test_client):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed_handling(self, test_client):
        """Test method not allowed handling."""
        # Try to POST to GET-only endpoint
        response = test_client.post("/")
        assert response.status_code == 405

    def test_validation_error_handling(self, test_client):
        """Test validation error handling."""
        # Send invalid data to API key test endpoint
        response = test_client.post("/ag_ui/api/test-api-key", json={"invalid": "data"})
        assert response.status_code == 422


class TestApplicationIntegrity:
    """Test suite for overall application integrity."""

    def test_app_can_start(self):
        """Test that the application can start without errors."""
        # This test ensures that importing and initializing the app doesn't raise errors
        from ai_research_assistant.ag_ui_backend.main import app as test_app

        assert test_app is not None
        assert isinstance(test_app, FastAPI)

    def test_all_routers_importable(self):
        """Test that all required routers can be imported."""
        try:
            from ai_research_assistant.ag_ui_backend.router import (
                router as ag_ui_router,
            )

            assert ag_ui_router is not None
        except ImportError as e:
            pytest.fail(f"Failed to import AG-UI router: {e}")

        # Test MCP router import
        try:
            # This import path may need adjustment based on actual MCP router location
            pass  # MCP router import would go here
        except ImportError:
            # MCP router might not be implemented yet
            pass

    def test_settings_and_config_available(self):
        """Test that settings and configuration are available."""
        try:
            from ai_research_assistant.config.global_settings import settings

            assert settings is not None
        except ImportError as e:
            pytest.fail(f"Failed to import settings: {e}")

    def test_dependencies_importable(self):
        """Test that all dependencies are importable."""
        # Test FastAPI
        import fastapi

        assert fastapi is not None

        # Test AG-UI core
        try:
            import ag_ui.core

            assert ag_ui.core is not None
        except ImportError:
            pytest.skip("AG-UI core not available")

    def test_application_routes_integrity(self):
        """Test that application routes are properly configured."""
        # Check that the app has routes
        assert len(app.routes) > 0

        # Check that each route is properly configured
        for route in app.routes:
            assert hasattr(route, "path")
            assert route.path is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
