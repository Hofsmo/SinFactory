"""Test the function interfacing with the grid."""

import pytest
import numpy as np
import pandas as pd
from sinfactory.pfactorygrid import PFactoryGrid
from sinfactory.pfresults import PFResults


@pytest.fixture(scope="module")
def test_system():
    """Create the test system."""
    project_name = "test_grid_sinfactory"

    return PFactoryGrid(project_name=project_name)


def test_set_variables(test_system):
    """ Check if the dictionary is correctly made."""
    var_names = ("n:fehz:bus1", "m:P:bus1", "s:firel", "s:outofstep", "n:u1:bus1")
    output = test_system.generate_variables(var_machines=var_names)

    assert output["SM1.ElmSym"][0] == var_names[0]


def test_run_dynamic_simulation(test_system):
    """Check if a dynamic simulation can be run."""
    variables = {"SM1.ElmSym": ["n:fehz:bus1"]}
    test_system.prepare_dynamic_sim(variables=variables)
    test_system.run_dynamic_sim()
    res = test_system.get_results(variables)

    assert res.iloc[20, :].to_numpy()[0] == pytest.approx(50.0, abs=0.01)


def test_check_islands(test_system):
    """ Check if the isalnds can be detected correctly. """
    test_system.create_trip_line_event("Line12", 1.0)
    test_system.create_trip_line_event("Line34", 1.0)
    test_system.initialize_and_run_dynamic_sim()
    test_system.delete_switch_event("Line12")
    test_system.delete_switch_event("Line34")

    assert test_system.check_islands() == 2


def test_get_island_elements(test_system):
    """ Check if the buses are correctly allocated to the islands. """
    test_system.initialize_and_run_dynamic_sim()
    islands = test_system.check_islands()
    island_list = test_system.get_island_elements(islands)

    assert island_list[0][0] == "bus1" or "bus4"


def test_find_connected_element(test_system):
    """ Test if connected elements can be found. """
    load = test_system.find_connected_element("bus2", ".ElmLod")
    assert load == "General Load(2)"


def test_pole_slip(test_system):
    """Test if registration of pole slip is correct."""
    var_names = ("s:firel", "s:outofstep")
    test_system.initialize_and_run_dynamic_sim(var_machines=var_names)

    assert test_system.pole_slip("SM1") is False


def test_delete_short_circuit(test_system):
    """Check if a short circuit can be deleted."""
    monitor = {"bus1.ElmTerm": ["m:u"]}

    test_system.delete_short_circuit("sc")
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    
    res = test_system.get_results(monitor)

    assert res.iloc[30, :].to_numpy()[0] == pytest.approx(1.0, abs=0.01)


def test_create_switch_evemt(test_system):
    """Check if a switch event can be created."""
    time = 0.1
    target_name = "Line12"
    switch_1 = test_system.lines[target_name].switches[0]

    test_system.create_switch_event("", time, "trip-" + target_name, switch_1)
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    res = test_system.get_results(monitor)

    assert res.iloc[30, :].to_numpy()[0] == pytest.approx(0.0, abs=0.01)


def test_delete_switch_evemt(test_system):
    """Check if a switch event can be created."""
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}
    target_name = "Line12"

    test_system.delete_switch_event("trip-" + target_name)
    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    res = test_system.get_results(monitor)

    assert res.iloc[30, :].to_numpy()[0] > 0.05


def test_create_trip_line_event(test_system):
    """Check if a line tripping event can be made."""
    test_system.create_trip_line_event("Line12", 0.1)
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}

    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    res = test_system.get_results(monitor)

    assert res.iloc[30, :].to_numpy()[0] == pytest.approx(0.0, abs=0.01)


def test_delete_trip_line_event(test_system):
    """Check if a line tripping event can be deleted."""
    test_system.delete_trip_line_event("Line12")
    monitor = {"Line12.ElmLne": ["m:I:bus1"]}

    test_system.prepare_dynamic_sim(variables=monitor)
    test_system.run_dynamic_sim()
    
    res = test_system.get_results(monitor)

    assert res.iloc[30, :].to_numpy()[0] > 0.05


def test_get_output_window_content(test_system):
    """Test if the output window data is given."""

    assert test_system.get_output_window_content() is not None


def test_clear_output_window(test_system):
    """Test if the output window data is removed."""
    test_system.clear_output_window()

    assert test_system.get_output_window_content() == []


def test_run_load_flow(test_system):
    """Test if running power flow calculation are correct. """

    assert test_system.run_load_flow(0, 0, 0) == 0


def test_calculate_isf(test_system):
    """Test if the ISFs are calculated correctly."""
    # First we will calculate the ISFs analytically.
    # We enumerate the lines as follows
    # 1: Line12, 2: Line14, 3: Line23, 4: Line34
    # We enumerate the generatos as follows:
    # 1: gen1, 2: gen2, 3: gen3
    # The adjacency matrix of the system is then.
    A = np.array([[1, -1, 0, 0],
                  [1, 0, 0, -1],
                  [0, 1, -1, 0],
                  [0, 0, 1, -1]])
    # All the lines have the same reactance, which gives the following
    # susceptance
    b = 1/0.0850115
    # The diagonal matrix of the system is
    D = np.diag(4*[b])
    X = np.zeros((4, 4))
    X[1:, 1:] = np.linalg.inv((A.T@D@A)[1:, 1:])
    ISF = D@A@X

    rows = np.array(
        [list(test_system.lines).index(name) for name in ["Line12",
                                                          "Line14",
                                                          "Line23",
                                                          "Line34"]])
    
    cols = np.array([list(test_system.gens).index(name) for name in ["SM1",
                                                                     "SM2",
                                                                     "SM3"]])
    
    isf = test_system.calculate_isf(balanced=2)
    np.testing.assert_allclose(ISF[:, [0, 1, 3]],
                               isf[rows[:, None], cols], rtol=0.1)

    def test_init_from_res(test_system):
        """Check if we can initialise the system from a PFResults object."""
        old_p = test_system.gens["SM1"].p_set
        val = 13.3
        
        test_system.gens["SM1"].p_set = val
        res = PFResults(test_system)
        test_system.gens["SM1"].p_set = old_p
        
        test_system.init_system_from_res(res)

        assert val == test_system.gens["SM1"].p_set
        test_system.gens["SM1"].p_set = old_p


def test_get_total_load(test_system):
    """Check if we can get teh total load correctly."""
    assert test_system.get_total_load() == 25


def test_get_total_gen(test_system):
    """Check if we can get the total production correctly."""
    assert test_system.get_total_gen() == 25

def test_change_os(test_system):
    """Check if we can correctly initialise a grid from a pandas Series."""
    index_l = pd.MultiIndex.from_product([["loads"], ["General Load"],
                                          ["p_set"]])
    index_g = pd.MultiIndex.from_product([["gens"], ["SM1", "SM2"],
                                          ["p_set"]])
    test_system.change_os(
        pd.Series([100.0, 50.0, 50.0], index= index_l.append(index_g)))

    assert test_system.loads["General Load"].p_set == 100
    assert test_system.gens["SM1"].p_set == 50
