"""Test the area class."""
import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return PFactoryGrid(project_name=project_name)


def test_inter_area_lines(test_system):
    """Check if we can correctly find the areas beteween two systems."""
    assert sorted(list(test_system.areas["1"].get_inter_area_lines(
        test_system.areas["2"]).keys())) == ["Line14", "Line23"]
