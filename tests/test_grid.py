"""Test the function interfacing with the grid."""

import pytest
#import sys
#sys.path.append('c:\\Users\\eirikh\\sinfactory\\sinfactory')
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
#print("System path:") 
#print(sys.path)
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid

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

def test_get_total_load(test_system): 
    assert test_system.get_total_load() == 10

def test_get_total_gen(test_system): 
    assert test_system.get_total_gen() == 0

def test_machine_gen(test_system): 
    assert test_system.get_machine_gen("SM.ElmSym") == 0

def test_change_load(test_system):
    """Check if a load can be changed"""
    p_load = {"Load": 10}
    q_load = {"Load": 0}

    monitor = {"Load.ElmLod": ["m:P:bus1"]}
    test_system.set_load_powers(p_load, q_load)

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, p = test_system.get_dynamic_results("Load.ElmLod", "m:P:bus1")

    assert p[20] == pytest.approx(10.0, abs=0.01)


def test_change_gen(test_system):
    """Check if a load can be changed"""
    p_gen = {"SM": 18}
    q_gen = {"SM": 0}

    monitor = {"SM.ElmSym": ["m:P:bus1"]}
    test_system.set_generator_powers(p_gen, q_gen)

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, p = test_system.get_dynamic_results("SM.ElmSym", "m:P:bus1")

    assert p[20] == pytest.approx(18.0, abs=0.01)


def test_create_short_circuit(test_system):
    """Check if a short circuit can be created"""

    monitor = {"Terminal 2.ElmTerm": ["m:u"]}

    test_system.create_short_circuit("Line.ElmLne", 0.1, "sc")

    p_gen = {"SM": 0}
    q_gen = {"SM": 0}
    test_system.set_generator_powers(p_gen, q_gen)

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, v = test_system.get_dynamic_results("Terminal 2.ElmTerm", "m:u")

    assert v[-1] < 0.1


def test_delete_short_circuit(test_system):
    """Check if a short circuit can be deleted."""

    monitor = {"Terminal 2.ElmTerm": ["m:u"]}

    test_system.delete_short_circuit("sc")

    test_system.prepare_dynamic_sim(variables=monitor)

    test_system.run_dynamic_sim()

    _, v = test_system.get_dynamic_results("Terminal 2.ElmTerm", "m:u")

    assert v[-1] == pytest.approx(1.0, abs=0.01)


def test_create_switch_evemt(test_system):
    """Check if a switch event can be created."""

    test_system.create_switch_event("CB.ElmCoup", 0.1, "sw")
    monitor = {"Line.ElmLne": ["m:I:bus1"]}
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()

    _, i = test_system.get_dynamic_results("Line.ElmLne", "m:I:bus1")

    assert i[-1] == pytest.approx(0.0, abs=0.01)


def test_delete_switch_evemt(test_system):
    """Check if a switch event can be created."""

    monitor = {"Line.ElmLne": ["m:I:bus1"]}
    test_system.delete_switch_event("sw")
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()

    _, i = test_system.get_dynamic_results("Line.ElmLne", "m:I:bus1")

    assert i[-1] > 0.5


def test_change_inertia_constant(test_system):
    """Check if the inertia of a machine can be changed."""
    h_constant = 6
    test_system.change_generator_inertia_constant("28 MVA GT.TypSym",
                                                  h_constant)

    elm = test_system.app.GetCalcRelevantObjects("28 MVA GT.TypSym")

    assert elm[0].h == h_constant
