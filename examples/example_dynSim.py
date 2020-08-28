import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'sinfactory')))
#print("System path:") 
#print(sys.path)
from sinfactory.pfactorygrid import PFactoryGrid as PFactoryGrid

project_name = "sinfactory"
study_case_name = "Tests"
#project_name = 'IEEE 9bus modified'
#study_case_name = 'Five-Cycles Fault Mag-A-Stat'
test_obj = PFactoryGrid(project_name=project_name,study_case_name=study_case_name)

monitor = {"SM.ElmSym": ["n:fe:bus1"]}
#monitor = {'G2.ElmSym': ['m:P:bus1']}

test_obj.prepare_dynamic_sim(variables=monitor)

sim_bool = test_obj.run_dynamic_sim()
print("Simulation success:")
print(sim_bool)
_, f = test_obj.get_dynamic_results("SM.ElmSym", "n:fe:bus1")
#_, f = test_obj.get_dynamic_results('G2.ElmSym', 'm:P:bus1')

import matplotlib.pyplot as plt
plt.plot(_,f)
plt.show()