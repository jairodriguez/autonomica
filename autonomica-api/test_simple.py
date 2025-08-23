"""
Simple test file to validate basic functionality without complex dependencies
"""
import pytest
from typing import Dict, List, Any


def add_numbers(a: int, b: int) -> int:
    """Simple function to test"""
    return a + b


def create_user_data(name: str, email: str) -> Dict[str, str]:
    """Create user data dictionary"""
    return {
        "name": name,
        "email": email,
        "active": True
    }


def calculate_average(numbers: List[float]) -> float:
    """Calculate average of numbers"""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


class TestBasicMath:
    """Test basic mathematical operations"""

    def test_add_positive_numbers(self):
        assert add_numbers(2, 3) == 5

    def test_add_negative_numbers(self):
        assert add_numbers(-2, -3) == -5

    def test_add_mixed_numbers(self):
        assert add_numbers(5, -3) == 2


class TestUserData:
    """Test user data creation"""

    def test_create_user_data(self):
        user = create_user_data("John Doe", "john@example.com")
        assert user["name"] == "John Doe"
        assert user["email"] == "john@example.com"
        assert user["active"] is True

    def test_create_user_data_empty_name(self):
        user = create_user_data("", "test@example.com")
        assert user["name"] == ""
        assert user["email"] == "test@example.com"


class TestStatistics:
    """Test statistical calculations"""

    def test_calculate_average_normal(self):
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert calculate_average(numbers) == 3.0

    def test_calculate_average_single_number(self):
        numbers = [42.0]
        assert calculate_average(numbers) == 42.0

    def test_calculate_average_empty_list(self):
        numbers = []
        assert calculate_average(numbers) == 0.0

    def test_calculate_average_floats(self):
        numbers = [1.5, 2.5, 3.5]
        assert calculate_average(numbers) == 2.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
