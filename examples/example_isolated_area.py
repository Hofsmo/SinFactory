import pytest
import numpy as np
import pandas as pd 
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid
import sys

print(sys.path)

project_name = "test_grid_sinfactory"

grid = PFactoryGrid(project_name=project_name)

grid.run_load_flow()

print(grid.get_list_of_lines())

grid.set_out_of_service("Line12", "line")
print(grid.get_list_of_lines())
grid.set_in_service("Line12", "line")
print(grid.get_list_of_lines())


# var_names = ("m:u", "b:ipat")
grid.initialize_and_run_dynamic_sim()  # var_buses=var_names)

print(grid.result)
islands = grid.check_islands()
print(islands)

print(grid.get_list_of_loads())
print(grid.get_total_load())
grid.change_connected_loads("bus2", 0)
print(grid.get_total_load())

grid.change_connected_loads("bus2", 5)

volt = grid.get_voltage_magnitude("SM1")
print(volt[10])

islands = grid.check_islands()
buses_in_islands = grid.get_island_elements(islands)

loads = []
machines = []
for island in range(int(islands)):
    loads.append(grid.loads_connected(buses_in_islands[island]))
    machines.append(grid.machines_connected(buses_in_islands[island]))
feature_names = [
    "COI angle",
    "Production",
    "Load",
    "Inertia"
]
feature_values = pd.DataFrame(columns=feature_names, index=np.arange(islands))
for island in range(int(islands)):
    for feature in feature_names: 
        feature_values.loc[island, feature] = grid.get_init_value(feature, loads[island], machines[island])
print(feature_values)