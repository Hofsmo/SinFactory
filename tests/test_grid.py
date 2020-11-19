"""Test the function interfacing with the grid."""

import pytest
import numpy as np 
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid

# How to run tests in VSC: 
# 1. Run this script 
# 2. write in terminal: python -m pytest

@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"
    
    return(PFactoryGrid(project_name=project_name))

def test_set_variables(test_system): 
    """ Check if the dictionary is correctly made.""" 
    var_names = ("n:fehz:bus1","m:P:bus1","s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    
    assert output['SM1.ElmSym'][0] == var_names[0]

def test_run_dynamic_simulation(test_system):
    """Check if a dynamic simulation can be run."""
    var_names = ("n:fehz:bus1","m:P:bus1","s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    test_system.prepare_dynamic_sim(variables=output)
    test_system.run_dynamic_sim()
    _, f = test_system.get_dynamic_results("SM1.ElmSym", "n:fehz:bus1")
    
    assert f[20] == pytest.approx(50.0, abs = 0.01)

def test_get_results(test_system): 
    """Check if the result file is on the correct output format. """
    var_names = ("n:fehz:bus1","m:P:bus1","s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    result = test_system.get_results(output)
    
    assert result.columns[0][0] == "SM1"

def test_get_rating(test_system): 
    """Check if get_rating function works. """
    
    assert test_system.get_ratings()[0] == pytest.approx(36.80, abs = 0.01)

def test_get_total_load(test_system): 
    """Check if the total load function is working."""
    
    assert sum(test_system.get_total_load()) == pytest.approx(25.0) 

def test_get_total_gen(test_system): 
    """Check if the total generation function is working."""
    
    assert sum(test_system.get_total_gen()) == pytest.approx(25.0)

def test_get_number_of_parallell(test_system): 
    """ Check if function that gets the number of parallell machines is working."""
    
    assert test_system.get_number_of_parallell("SM1") == 1

def test_set_number_of_parallell(test_system):
    """ Check if setting the number of parallells is working.""" 
    test_system.set_number_of_parallell("SM1",1)

    assert test_system.get_number_of_parallell("SM1") == 1 

def test_set_load_powers(test_system): 
    """Check if a load can be changed"""
    p_load = {"General Load": 10}
    q_load = {"General Load": 2}
    monitor = {"General Load.ElmLod": ["m:P:bus1"]}
    test_system.set_load_powers(p_load, q_load)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, p = test_system.get_dynamic_results("General Load.ElmLod", "m:P:bus1")

    assert p[20] == pytest.approx(10.0, abs=0.01)

def set_generator_powers(test_system): 
    """Check if a generator can be changed"""
    p_gen = {"SM1": 10}
    q_gen = {"SM1": 0}
    monitor = {"SM1.ElmSym": ["m:P:bus1"]}
    test_system.set_generator_powers(p_gen, q_gen)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, p = test_system.get_dynamic_results("SM1.ElmSym", "m:P:bus1")

    assert p[20] == pytest.approx(10.0, abs=0.1)

def test_get_machine_gen(test_system): 
    """Test if get_machine_gen get the true value."""

    assert test_system.get_machine_gen("SM1") == 10

def test_change_bus_load(test_system): 
    """Test if the load can be changed."""
    old_tot_load = sum(test_system.get_total_load())
    test_system.change_bus_load("General Load", 11)
    new_tot_load = sum(test_system.get_total_load())
    test_system.change_bus_load("General Load", 10)

    assert new_tot_load-old_tot_load == 1 

def test_change_machine_gen(test_system): 
    """Test if the production can be changed."""
    old_tot_gen = sum(test_system.get_total_gen())
    test_system.change_machine_gen("SM1", 11)
    new_tot_gen = sum(test_system.get_total_gen())
    test_system.change_machine_gen("SM1", 10)

    assert new_tot_gen-old_tot_gen == 1 

def test_get_machines(test_system): 
    """Test if the names of the machines can be returned."""

    assert test_system.get_machines()[0] == "SM1"

def test_check_if_in_service(test_system): 
    """Check if the function that checks if a machine is in service works."""

    assert test_system.check_if_in_service("SM1") == True

def test_get_area_load_in(test_system): 
    """Check if correct area the load is in."""

    assert test_system.get_area_load_in("General Load(2)") == 1

def test_get_area_gen_in(test_system): 
    """Check if correct area the generator is in."""

    assert test_system.get_area_gen_in("SM1") == 1

def test_get_area_gen(test_system): 
    """Check if the total production in an area is correct."""

    assert test_system.get_area_gen(2) == pytest.approx(9.0)

def test_get_area_load(test_system): 
    """Check if the total consumption in an area is correct."""

    assert test_system.get_area_load(2) == pytest.approx(20.0)

def test_set_out_of_service(test_system): 
    """Test if machines can be set out of service."""
    test_system.set_out_of_service("SM1")

    assert test_system.check_if_in_service("SM1") == False 

def test_set_in_service(test_system): 
    """Test if machines can be set in service."""
    test_system.set_in_service("SM1")

    assert test_system.check_if_in_service("SM1") == True 

def test_change_generator_inertia_constant(test_system): 
    """Check if inertia constant at a generator can be changed."""    
    old_inertia = test_system.get_inertia("SM1") 
    test_system.change_generator_inertia_constant("SM1", 5)
    new_inertia = test_system.get_inertia("SM1")
    test_system.change_generator_inertia_constant("SM1", 4)

    assert new_inertia-old_inertia > 0

def test_change_grid_min_short_circuit_power(test_system): 
    """."""

    raise NotImplementedError

def test_get_list_of_loads(test_system): 
    """Check if a list of all loads is correct."""

    assert test_system.get_list_of_loads()[0] == "General Load"

def test_get_branch_flow(test_system): 
    """Testing if getting the load factor of a branch is correct."""

    assert test_system.get_branch_flow("Line12") == pytest.approx(68.8534, abs=0.001)

def test_get_line_list(test_system): 
    """Test of getting a list of all lines."""

    assert test_system.get_line_list()[3] == "Line34" 

def test_is_ref(test_system): 
    """Testing if a machine is the reference machine."""

    assert test_system.is_ref("SM1") == True

def test_pole_slip(test_system): 
    """Test if registration of pole slip is correct."""
    var_names = ("s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    result = test_system.get_results(output)

    assert test_system.pole_slip("SM1", result) == False

def test_get_initial_rotor_angles(test_system):
    """Test if intial rotor angles are correct.""" 
    var_names = ("s:firel", "s:outofstep")  
    output = test_system.generate_variables(var_names)
    result = test_system.get_results(output)

    assert test_system.get_initial_rotor_angles(result)[0] == pytest.approx(0.0, abs = 0.05)

def test_get_freq(test_system): 
    """Test if the frequency-values are correct."""

    assert test_system.get_freq()[10] == pytest.approx(50.0, abs = 0.01)

def test_get_rotor_angles(test_system): 
    """Test if the rotor angles-values are correct."""
    time, rotor_ang = test_system.get_rotor_angles("SM1")
    rotor_ang = np.transpose(rotor_ang)

    assert rotor_ang[100] == pytest.approx(0.0, abs = 0.01)

def test_get_machines_inertia_list(test_system): 
    """Test if the inertia list is correct."""
    inertia_list = test_system.get_machines_inertia_list()

    assert float(inertia_list[0][1]) == pytest.approx(7.36, abs = 0.01)

def test_get_inertia(test_system): 
    """Test if the correct inertia is given."""

    assert test_system.get_inertia("SM1") == pytest.approx(7.36, abs = 0.01)

def test_create_short_circuit(test_system):
    """Check if a short circuit can be created"""
    monitor = {"bus1.ElmTerm": ["m:u"]}

    test_system.create_short_circuit("Line12.ElmLne", 0.1, "sc")
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, v = test_system.get_dynamic_results("bus1.ElmTerm", "m:u")

    assert v[30] < 1.0


def test_delete_short_circuit(test_system):
    """Check if a short circuit can be deleted."""
    monitor = {"bus1.ElmTerm": ["m:u"]}

    test_system.delete_short_circuit("sc")
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, v = test_system.get_dynamic_results("bus1.ElmTerm", "m:u")

    assert v[30] == pytest.approx(1.0, abs=0.01)


def test_create_switch_evemt(test_system):
    """Check if a switch event can be created."""
    time = 0.1 
    target_name = "Line12"
    switch_1 = test_system.lines[target_name].switches[0]

    test_system.create_switch_event("", time, "trip-"+target_name, switch_1)
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, i = test_system.get_dynamic_results("Line12.ElmLne", "m:I:bus1")

    assert i[30] == pytest.approx(0.0, abs=0.01)


def test_delete_switch_evemt(test_system):
    """Check if a switch event can be created."""
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}
    target_name = "Line12"

    test_system.delete_switch_event("trip-"+target_name)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, i = test_system.get_dynamic_results("Line12.ElmLne", "m:I:bus1")

    assert i[30] > 0.05


def test_create_trip_line_event(test_system): 
    """Check if a line tripping event can be made."""    
    test_system.create_trip_line_event("Line12", 0.1)
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}

    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, i = test_system.get_dynamic_results("Line12.ElmLne", "m:I:bus1")

    assert i[30] == pytest.approx(0.0, abs=0.01)


def test_delete_trip_line_event(test_system): 
    """Check if a line tripping event can be deleted."""
    test_system.delete_trip_line_event("Line12")
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}

    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    _, i = test_system.get_dynamic_results("Line12.ElmLne", "m:I:bus1")

    assert i[30] > 0.05

def test_get_output_window_content(test_system):  
    """Test if the output window data is given."""

    assert test_system.get_output_window_content()  != None

def test_clear_output_window(test_system): 
    """Test if the output window data is removed."""
    test_system.clear_output_window() 

    assert test_system.get_output_window_content()  == [] 

def test_run_load_flow(test_system): 
    """Test if running power flow calculation are correct. """

    assert test_system.run_load_flow(0,0,0) == False 