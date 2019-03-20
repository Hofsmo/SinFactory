"""Test the function interfacing with the grid."""

import pytest

from sinfactory.pfactorygrid import PFactoryGrid


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "sinfactory"
    study_case_name = "Tests"
    return(PFactoryGrid(project_name=project_name,
                        study_case_name=study_case_name))


def test_run_dynamic_simulation(test_system):
    """Check if a dynamic simulation can be run."""

    monitor = {"SM.ElmSym": ["n:fe:bus1"]}

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, f = test_system.get_dynamic_results("SM.ElmSym", "n:fe:bus1")

    assert f[20] == pytest.approx(1.0)


def test_change_load(test_system):
    """Check if a load can be changed"""
    p_load = {"Load": 1}
    q_load = {"Load": 0}

    monitor = {"Load.ElmLod": ["m:P:bus1"]}
    test_system.set_all_loads(p_load, q_load)

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, p = test_system.get_dynamic_results("Load.ElmLod", "m:P:bus1")

    assert p[20] == pytest.approx(1.0, abs=0.01)
