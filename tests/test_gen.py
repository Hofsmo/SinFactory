"""Test the Generator class."""

import pytest
from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_gen():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return PFactoryGrid(project_name=project_name).gens["SM1"]


def test_set_parallell_machines(test_gen):
    """Check if we can change the number of parallell machines."""
    test_gen.n_machines = 2

    assert test_gen.pf_object.ngnum == 2
    
    # Change the system back
    test_gen.n_machines = 1


def test_change_power(test_gen):
    """Check if we can correctly change the power."""
    old_p = test_gen.p_set

    test_gen.p_set = 150

    assert test_gen.pf_object.pgini == 150

    test_gen.n_machines = 2
    
    assert test_gen.pf_object.pgini == 150/2
    
    test_gen.p_set = 100

    assert test_gen.pf_object.pgini == 100/2

    assert test_gen.p_set == 100
    
    test_gen.n_machines = 1
    test_gen.p_set = old_p
