"""Test the line class."""


import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return PFactoryGrid(project_name=project_name)


@pytest.fixture(scope="module")
def test_line(test_system):
    """Create the test system."""
    test_system.run_load_flow()
    return test_system.lines["Line12"]

def test_line_f_t_bus(test_line):
    """Test if the names of the f and t bus are got correctly."""

    assert "bus1" == test_line.f_bus
    assert "bus2" == test_line.t_bus

