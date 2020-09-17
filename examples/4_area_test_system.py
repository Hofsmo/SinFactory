import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
#print("System path:") 
#print(sys.path)
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid
import matplotlib.pyplot as plt

project_name = "RaPid"
study_case_name = "No_events" # "Case to compare with PSSE (Scenario 3)"
test_obj = PFactoryGrid(project_name=project_name,study_case_name=study_case_name)
print("Total generation: ",test_obj.get_total_gen()," MW")
print("Total load: ",test_obj.get_total_load()," MW")
plot = "active power"

machine_names = test_obj.get_machines()
for machine_name in machine_names: 
    test_obj.set_in_service(machine_name)

test_obj.prepare_dynamic_sim(start_time=0.0, end_time=3.0)

sim_bool = test_obj.run_dynamic_sim()
print("Simulation success (false indicate success):")
print(sim_bool)
print(test_obj.get_machine_list())

#test_obj.switch_control("Line10",1)

#machine_list = test_obj.get_machine_list()
#print(machine_list.size)
#print(machine_list.T)

#print(test_obj.get_machines_inertia_list())

if plot == "active power": 
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(33).ElmSym", "m:P:bus1")
    plt.plot(_,f1)
elif plot == "frequency":
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(1).ElmSym", "n:fehz:bus1")
    _, f2 = test_obj.get_dynamic_results("Synchronous Machine(18).ElmSym", "n:fehz:bus1")
    plt.plot(_,f1)
    plt.plot(_,f2)
elif plot == "voltage":
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(1).ElmSym", "n:u1:bus1")
    _, f2 = test_obj.get_dynamic_results("Synchronous Machine(18).ElmSym", "m:u1:bus1")
    plt.plot(_,f1)
    plt.plot(_,f2)

if plot == "active power": 
    plt.legend(["Active power bus 30020"])
    plt.xlabel("Time [s]")
    plt.ylabel("Active power [MW]")
elif plot == "frequency":
    plt.legend(["Frequency area 3", "Frequency area 2"])
    plt.xlabel("Time [s]")
    plt.ylabel("Freqency [Hz]")
elif plot == "voltage":
    plt.legend(["Voltage bus 30020", "Voltage bus 20009"])
    plt.xlabel("Time [s]")
    plt.ylabel("Voltage [p.u.]")

plt.show()

print("Generation and load of area 1:")
print("Generation [MW]: ", test_obj.get_area_gen("Area1"))
print("Load [MW]: ", test_obj.get_area_load("Area1"))

test_obj.power_flow_calc() 
test_obj.get_branch_flow(10021, 30023) 
load_buses = test_obj.get_load_busses() 
print(load_buses) 
machine_list = test_obj.get_machine_list()
print(machine_list.size)
print(machine_list.T)

# Continue simulation 
test_obj.prepare_dynamic_sim(start_time=3.0, end_time=5.0)

sim_bool = test_obj.run_dynamic_sim()
print("Simulation success (false indicate success):")
print(sim_bool)
print(test_obj.get_machine_list())

_, f2 = test_obj.get_dynamic_results("Synchronous Machine(33).ElmSym", "m:P:bus1")
plt.plot(_,f2)
plt.show()
