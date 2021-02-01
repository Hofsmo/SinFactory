import matplotlib2tikz
import matplotlib.pyplot as plt
import numpy as np

t_cs = [0.2, 0.4, 0.7]
powers = np.arange(0, 1.1, 0.1)
f_0 = 50
dfs = [5, 10, 2, 1]

for df in dfs:
    for t_c in t_cs:
        H = [f_0*power*t_c/(2*df) for power in powers]

        label = 'df= ' + str(df) + ',t_c=' + str(t_c)
        plt.plot(powers, H, label=label)

plt.legend()
plt.grid(True)

matplotlib2tikz.save("../plots/H_constants_new.tikz")
plt.show()
