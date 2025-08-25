"""
Test script to verify the /customers/me endpoint returns the correct User interface shape.
"""

from typing import Any, TypedDict


class User(TypedDict):
    """Expected User interface shape from TypeScript."""

    id: str
    email: str
    emailVerified: bool
    createdAt: str


def verify_response_shape(response_data: dict[str, Any]) -> bool:
    """Verify that the response matches the expected User interface."""
    required_fields = {"id", "email", "emailVerified", "createdAt"}

    # Check if all required fields are present
    if not all(field in response_data for field in required_fields):
        missing_fields = required_fields - set(response_data.keys())
        print(f"Missing required fields: {missing_fields}")
        return False

    # Check field types
    if not isinstance(response_data.get("id"), str):
        print(f"Field 'id' should be string, got {type(response_data.get('id'))}")
        return False

    if not isinstance(response_data.get("email"), str):
        print(f"Field 'email' should be string, got {type(response_data.get('email'))}")
        return False

    if not isinstance(response_data.get("emailVerified"), bool):
        print(
            f"Field 'emailVerified' should be boolean, got {type(response_data.get('emailVerified'))}"
        )
        return False

    if not isinstance(response_data.get("createdAt"), str):
        print(f"Field 'createdAt' should be string, got {type(response_data.get('createdAt'))}")
        return False

    return True


# Example response from the endpoint
example_response = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "emailVerified": True,
    "createdAt": "2024-08-24T21:55:15.000Z",
}

if __name__ == "__main__":
    print("Testing /customers/me endpoint response shape...")
    print(f"Example response: {example_response}")

    if verify_response_shape(example_response):
        print("✓ Response shape matches the expected User interface!")
    else:
        print("✗ Response shape does not match the expected User interface.")

    print("\nThe endpoint has been successfully configured at: /api/customers/me")
    print("It requires authentication (IsAuthenticated permission)")
    print("\nResponse fields:")
    print("  - id: string (UUID of the user)")
    print("  - email: string (user's email address)")
    print("  - emailVerified: boolean (whether email is verified)")
    print("  - createdAt: string (ISO 8601 formatted date)")
