import pytest
from backend.app import create_app
from backend.services.model_service import ModelService

class MockModelService(ModelService):
    def load_model_configs(self):
        self.models = {
            "mock-model": {
                "id": "mock-model",
                "name": "Mock Model",
                "type": "mock",
                "description": "A mock model for testing.",
                "is_default": True
            }
        }
        self.default_model = "mock-model"
        print("Loaded mock model configs")

    def preload_models_in_background(self):
        print("Skipping model preloading in test environment.")
        pass

@pytest.fixture
def app(monkeypatch):
    """Create and configure a new app instance for each test."""

    # It's important to mock before the app is created
    # because ModelService is instantiated at the module level in routes.
    monkeypatch.setattr('backend.api.routes.model_service', MockModelService())

    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
