"""Test the function interfacing with the grid."""

import pytest
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid

@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    return(PFactoryGrid(project_name=project_name))

def test_set_variables(test_system): 
    """ Check if the dictionary is correctly made.""" 
    var_names = ("n:fehz:bus1","m:P:bus1","s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    assert output['SM1'] == var_names

def test_run_dynamic_simulation(test_system):
    """Check if a dynamic simulation can be run."""
    monitor = {"SM1.ElmSym": ["n:fe:bus1"]}
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, f = test_system.get_dynamic_results("SM.ElmSym", "n:fe:bus1")
    assert f[20] == pytest.approx(1.0)

def test_get_total_load(test_system): 
    """Check if the total load function is working."""
    assert sum(test_system.get_total_load()) == 25 

def test_get_total_gen(test_system): 
    """Check if the total generation function is working."""
    assert sum(test_system.get_total_gen()) == 25.12

def test_get_number_of_parallell(test_system): 
    """ Check if function that gets the number of parallell machines is working."""
    assert test_system.get_number_of_parallell("SM1") == 1

def test_set_number_of_parallell(test_system):
    """ Check if setting the number of parallells is working.""" 
    num = test_system.get_number_of_parallell("SM1")
    test_system.set_number_of_parallell("SM1",num+1)
    assert test_system.get_number_of_parallell("SM1") == num +1 

def test_set_load_powers(test_system): 
    """Check if a load can be changed"""
    p_load = {"General Load": 10}
    q_load = {"General Load": 2}
    monitor = {"General Load.ElmLod": ["m:P:bus1"]}
    test_system.set_load_powers(p_load, q_load)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, p = test_system.get_dynamic_results("General Load.ElmLod", "m:P:bus1")
    assert p[20] == pytest.approx(20.0, abs=0.01)

def set_generator_powers(test_system): 
    """Check if a generator can be changed"""
    p_gen = {"SM1": 10}
    q_gen = {"SM1": 0}
    monitor = {"SM1.ElmSym": ["m:P:bus1"]}
    test_system.set_generator_powers(p_gen, q_gen)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, p = test_system.get_dynamic_results("SM1.ElmSym", "m:P:bus1")
    assert p[-1] == pytest.approx(10.0, abs=0.1)

def test_get_machine_gen(test_system): 
    """Test if get_machine_gen get the true value."""
    assert test_system.get_machine_gen("SM1.ElmSym") == 10

def test_change_bus_load(test_system): 
    raise NotImplementedError
    
def test_change_gen_load(test_system): 
    raise NotImplementedError

def test_change_machine_gen(test_system): 
    raise NotImplementedError

def test_get_machines(test_system): 
    raise NotImplementedError

def test_check_if_in_service(test_system): 
    raise NotImplementedError

def test_get_area_load_in(test_system): 
    raise NotImplementedError

def test_get_area_gen_in(test_system): 
    raise NotImplementedError

def test_get_area_gen(test_system): 
    raise NotImplementedError

def test_get_area_load(test_system): 
    raise NotImplementedError

def test_set_out_of_service(test_system): 
    raise NotImplementedError

def test_set_in_service(test_system): 
    raise NotImplementedError

def test_change_generator_inertia_constant(test_system): 
    raise NotImplementedError

def test_change_grid_min_short_circuit_power(test_system): 
    raise NotImplementedError

def test_get_list_of_loads(test_system): 
    raise NotImplementedError

def test_power_flow_calc(test_system): 
    raise NotImplementedError

def test_power_power_calc_converged(test_system): 
    raise NotImplementedError

def test_power_get_branch_flow(test_system): 
    raise NotImplementedError

def test_get_line_list(test_system): 
    raise NotImplementedError

def test_run_sim(test_system): 
    raise NotImplementedError

def test_is_ref(test_system): 
    raise NotImplementedError

def test_pole_slip(test_system): 
    raise NotImplementedError

def test_get_initial_rotor_angles(test_system): 
    raise NotImplementedError

def test_get_freq(test_system): 
    raise NotImplementedError

def test_get_rotor_angles(test_system): 
    raise NotImplementedError

def test_get_machines_inertia_list(test_system): 
    raise NotImplementedError

def test_get_inertia(test_system): 
    raise NotImplementedError

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

    assert i[-1] > 0.05


def test_create_trip_line_event(test_system): 
    raise NotImplementedError

def test_delete_trip_line_event(test_system): 
    raise NotImplementedError

def test_get_output_window_content(test_system): 
    raise NotImplementedError

def test_clear_output_window(test_system): 
    raise NotImplementedError

def test_run_load_flow(test_system): 
    raise NotImplementedError