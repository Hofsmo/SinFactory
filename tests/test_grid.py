"""Test the function interfacing with the grid."""

import pytest

from sinfactory.pfactorygrid import PFactoryGrid


def test_run_dynamic_simulation():
    """Check if a dynamic simulation can be run."""

    project_name = "sinfactory"
    study_case_name = "Tests"

    monitor = {"SM.ElmSym": "fe:bus1"}

    sim = PFactoryGrid(project_name=project_name,
                       study_case_name=study_case_name)

    sim.prepare_dynamic_sim(variables=monitor)

    sim.run_dynamic_sim()

    _, f = sim.get_dynamic_results("SM.ElmSym", "fe:bus1")

    assert f[100] == pytest.approx(1.0)
