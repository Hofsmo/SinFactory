"""Module for testing eigenvalue calculations."""
import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return PFactoryGrid(project_name=project_name)


def test_eigenvalue_calculation(test_system):
    """Check if we can calculate eigenvalues."""

    assert test_system.calculate_eigenvalues().min_damping < 100
