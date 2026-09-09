import os
import pytest
from backend.config import settings

@pytest.fixture(autouse=True, scope='session')
def enforce_test_mock_llm():
    orig = os.environ.get('LLM_PROVIDER')
    os.environ['LLM_PROVIDER'] = 'mock'
    settings.LLM_PROVIDER = 'mock'
    yield
    if orig is not None:
        os.environ['LLM_PROVIDER'] = orig
        settings.LLM_PROVIDER = orig
    else:
        os.environ.pop('LLM_PROVIDER', None)
        settings.LLM_PROVIDER = 'ollama'