
import pytest
from sinfactory.pfactorygrid import PFactoryGrid
from sinfactory.pfresults import PFResults


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"

    return PFactoryGrid(project_name=project_name)


def test_gen_results(test_system):
    """Test if we can get the generator results."""
    old_p = test_system.gens["SM1"].p_set

    test_system.gens["SM1"].p_set = 33

    test_system.run_load_flow()

    res = PFResults(test_system)

    assert res.gen.loc["SM1", "p_set"] == 33

    test_system.gens["SM1"].p_set = old_p


def test_load_results(test_system):
    """Test if we can get the load results."""
    name = "General Load"
    old_p = test_system.loads[name].p_set

    test_system.loads[name].p_set = 33

    test_system.run_load_flow()

    res = PFResults(test_system)

    assert res.load.loc[name, "p_set"] == 33

    test_system.loads[name].p_set = old_p


def test_area_results(test_system):
    """Check if we can get the results for an area"""
    test_system.run_load_flow()
    res = PFResults(test_system)
    
    assert res.area.loc["1", "gens"] > 0
    assert res.area.loc["1", "2"] > 0
