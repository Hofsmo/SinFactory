"""Test the bus class."""

import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return PFactoryGrid(project_name=project_name)


@pytest.fixture(scope="module")
def test_bus(test_system):
    """Create the test system."""
    test_system.run_load_flow()
    return test_system.buses["bus3"]


def test_bus_voltage(test_bus):
    """Check if we can correctly return the bus voltage."""
    assert 0.99 == pytest.approx(test_bus.u, 0.01)


def test_island_id(test_system):
    """Check if we can correctly detect islands."""
    test_system.lines["Line12"].in_service = False
    test_system.lines["Line34"].in_service = False

    test_system.run_load_flow()
    assert len(set(bus.island_id for bus in test_system.buses.values())) == 2

    test_system.lines["Line12"].in_service = True
    test_system.lines["Line34"].in_service = True
