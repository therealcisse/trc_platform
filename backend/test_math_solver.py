"""
Test script for the math solver functionality.
This tests both mock and production modes of the OpenAI client.
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings  # noqa: E402

from core.services.openai_client import (  # noqa: E402
    MockOpenAIClient,
    ProductionOpenAIClient,
    openai_client,
)


def test_mock_mode():
    """Test the mock implementation."""
    print("\n=== Testing Mock Mode ===")
    print(f"USE_MOCK_OPENAI: {settings.USE_MOCK_OPENAI}")

    # Create a mock client directly
    mock_client = MockOpenAIClient()

    # Test with a small image (should return error)
    small_image = b"small"
    try:
        result = mock_client.solve_image(small_image)
        print("\nSmall image test:")
        print(f"  Result: {result.result}")
        print(f"  Model: {result.model}")
        print(f"  Request ID: {result.request_id}")
        print(f"  Processing time: {result.processing_time_ms}ms")
    except Exception as e:
        print(f"\nSmall image test failed with error: {e}")

    # Test with a normal image
    normal_image = b"x" * 5000  # 5KB image
    result = mock_client.solve_image(normal_image)
    print("\nNormal image test:")
    print(f"  Result: {result.result}")
    print(f"  Model: {result.model}")
    print(f"  Usage: {result.usage}")
    print(f"  Request ID: {result.request_id}")
    print(f"  Processing time: {result.processing_time_ms}ms")
    
    # Test numeric parsing
    numeric_result = result.get_numeric_result()
    print(f"  Numeric result: {numeric_result}")
    
    # Test dictionary conversion (for backwards compatibility)
    result_dict = result.to_dict()
    print(f"  As dict: {result_dict}")

    # Test ping
    print(f"\nPing test: {mock_client.ping()}")


def test_singleton_client():
    """Test the singleton client that respects USE_MOCK_OPENAI setting."""
    print("\n=== Testing Singleton Client ===")
    print(f"Implementation type: {type(openai_client._impl).__name__}")

    # Test with a normal image - using new type-safe API
    test_image = b"x" * 5000  # 5KB image
    result = openai_client.solve_image(test_image)
    print("\nImage solve test (type-safe):")
    print(f"  Result: {result.result}")
    print(f"  Model: {result.model}")
    print(f"  Is error: {result.is_error_response()}")
    
    # Test backwards compatibility with return_dict=True
    result_dict = openai_client.solve_image(test_image, return_dict=True)
    print("\nImage solve test (dict mode):")
    print(f"  Result: {result_dict['result']}")
    print(f"  Model: {result_dict['model']}")

    # Test ping
    print(f"\nPing test: {openai_client.ping()}")


def test_production_mode_validation():
    """Test that production mode properly validates API key requirement."""
    print("\n=== Testing Production Mode Validation ===")

    # Temporarily clear the API key
    original_api_key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = ""

    try:
        ProductionOpenAIClient()
        print("ERROR: Should have raised ValueError for missing API key")
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")
    finally:
        # Restore original API key
        settings.OPENAI_API_KEY = original_api_key


if __name__ == "__main__":
    print("Math Solver Client Test")
    print("=" * 50)

    test_mock_mode()
    test_singleton_client()
    test_production_mode_validation()

    print("\n" + "=" * 50)
    print("All tests completed!")
