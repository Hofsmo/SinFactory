import matplotlib.pyplot as plt
import numpy as np

# Impedance to the fault
Z_7 = 2.365
Z_1234 = 4.135

S_sc = np.arange(30, 200, 10)/100

V_pcc = [Z_7/(1/power+Z_1234+Z_7) for power in S_sc]

plt.plot(S_sc*100, V_pcc)
plt.grid(True)
plt.show()
