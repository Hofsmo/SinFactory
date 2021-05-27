"""Test the bus class."""

import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_bus():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    test_system = PFactoryGrid(project_name=project_name)
    test_system.run_load_flow()
    return test_system.buses["bus3"]

def test_bus_voltage(test_bus):
    """Check if we can correctly return the bus voltage."""
    assert 0.99 == pytest.approx(test_bus.u, 0.01)

