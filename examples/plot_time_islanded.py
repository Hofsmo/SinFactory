#import matplotlib2tikz
import tikzplotlib
import matplotlib.pyplot as plt
import numpy as np 

powers = np.arange(0, 1.1, 0.1)
H_constants = np.arange(0.3, 1.4, 0.3)
f_0 = 50
dfs = [5, 10, 2, 1]

powers = np.linspace(0.01, 1)
data = []
for df in dfs:
    for H in H_constants:
        t = [2*H*df/(f_0*power) for power in powers]

        t = np.array(t).reshape(-1, 1)
        powers = np.array(powers).reshape(-1, 1)

        if not np.any(data):
            data = np.concatenate((powers*100, t), 1)
        else:
            data = np.column_stack((data, t))

        label = 'df= ' + str(df) + ',H=' + str(H)
        plt.plot(powers*100, t, label=label)

plt.legend()
plt.grid(True)

# matplotlib2tikz.save("../plots/time_islanded_template.tikz")
np.savetxt("time_islanded.csv",
           data, delimiter=',')
plt.show()
