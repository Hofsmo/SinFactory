

import numpy as np
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
#print("System path:") 
#print(sys.path)
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid
import matplotlib.pyplot as plt

project_name = "RaPid_compact_bus_sys"
study_case_name = "No_events" # "Case to compare with PSSE (Scenario 3)"
test_obj = PFactoryGrid(project_name=project_name) 
test_obj.activate_study_case(study_case_name=study_case_name)# set variables

parallell_init = np.loadtxt("examples\\parallell_machines.txt",unpack=True)
machine_names = test_obj.get_machines()      
for i, m in enumerate(machine_names): 
    test_obj.set_number_of_parallell(m,int(parallell_init[i]))   
# Check and set all generators in service
for machine_name in machine_names: 
    test_obj.set_in_service(machine_name)

var_names = ("n:fehz:bus1","n:u1:bus1","n:u1:bus1","m:P:bus1","n:Q:bus1",\
    "s:firel", "s:outofstep")  
# map machines in service to variables
output = test_obj.generate_variables(var_names)
print(output["Synchronous Machine(1).ElmSym"][0])
print(var_names[0])
test_obj.power_flow_calc()

plot = "active power"

machine_names = test_obj.get_machines()
for machine_name in machine_names: 
    test_obj.set_in_service(machine_name)
print(test_obj.power_flow_calc() )

test_obj.prepare_dynamic_sim(variables = output, start_time = 0, end_time=10.0)
test_obj.run_dynamic_sim()
print("get branch flow at line 10: ",test_obj.get_branch_flow("Line10"))

#machine_list = test_obj.get_machine_list()
#print(machine_list.size)
#print(machine_list.T)

inertia_list = test_obj.get_machines_inertia_list()
print(inertia_list)
print(inertia_list[0][1])
print(type(inertia_list[0][1]))

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

#plt.show()
tot_gen = 0 
for m in machine_names: 
    tot_gen += test_obj.get_machine_gen(m)* test_obj.get_number_of_parallell(m)
print("Total generation in the system: ", tot_gen)
print("Total consumption in the system: ", sum(test_obj.get_total_load()))

print("Total generation at each bus: ", test_obj.get_total_gen())
print("Generation and load of area 1:")
print("Generation [MW]: ", test_obj.get_area_gen(1))
print("Load [MW]: ", test_obj.get_area_load(1))

# Continue simulation 
test_obj.prepare_dynamic_sim(start_time=3.0, end_time=5.0)

sim_bool = test_obj.run_dynamic_sim()
print("Simulation success (false indicate success):")
print(sim_bool)


result = test_obj.get_results(output,filepath="results.csv") # result is a dataframe with all machines and variables
pole_slip_bool = 0 
for machine in test_obj.get_machines(): 
    if test_obj.pole_slip(machine,result): 
        pole_slip_bool = 1
if pole_slip_bool == 1: 
    print("The system is not stable.")
else: 
    print("The system is stable.")


_, f2 = test_obj.get_dynamic_results("Synchronous Machine(33).ElmSym", "m:P:bus1")
plt.plot(_,f2)
plt.show()
