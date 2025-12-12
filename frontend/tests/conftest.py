import pytest
import os

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Tells Playwright to use the saved login state (auth.json)
    for all tests, so you are already logged in.
    """
    # Ensure the path matches where you saved the file in Step 1
    auth_path = os.path.join(os.path.dirname(__file__), "auth.json")
    
    return {
        **browser_context_args,
        "storage_state": auth_path
    }