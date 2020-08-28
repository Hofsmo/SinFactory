import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
#print("System path:") 
#print(sys.path)
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid

project_name = "RaPid"
study_case_name = "Case to compare with PSSE (Scenario 3)"
test_obj = PFactoryGrid(project_name=project_name,study_case_name=study_case_name)
print("Total generation: ",test_obj.get_total_gen()," MW")
print("Total load: ",test_obj.get_total_load()," MW")
plot = "frequency"
if plot == "active power": 
    monitor = {"Synchronous Machine(32).ElmSym": ["m:P:bus1"]}
elif plot == "frequency":
    monitor = {"Synchronous Machine(32).ElmSym": ["n:fehz:bus1"], "Synchronous Machine(18).ElmSym": ["n:fehz:bus1"]}
elif plot == "voltage":
    monitor = {"Synchronous Machine(32).ElmSym": ["n:u1:bus1"], "Synchronous Machine(18).ElmSym": ["m:u1:bus1"]}

test_obj.prepare_dynamic_sim(variables=monitor,end_time=20.0)

sim_bool = test_obj.run_dynamic_sim()
print("Simulation success (false indicate success):")
print(sim_bool)

import matplotlib.pyplot as plt
if plot == "active power": 
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(32).ElmSym", "m:P:bus1")
    plt.plot(_,f1)
elif plot == "frequency":
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(32).ElmSym", "n:fehz:bus1")
    _, f2 = test_obj.get_dynamic_results("Synchronous Machine(18).ElmSym", "n:fehz:bus1")
    plt.plot(_,f1)
    plt.plot(_,f2)
elif plot == "voltage":
    _, f1 = test_obj.get_dynamic_results("Synchronous Machine(32).ElmSym", "n:u1:bus1")
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