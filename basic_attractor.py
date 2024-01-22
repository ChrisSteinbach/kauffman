import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Lorenz system parameters
sigma = 10.0
rho = 28.0
beta = 2.667

# Lorenz system differential equations.
def lorenz_system(current_state, t):
    x, y, z = current_state
    dxdt = sigma * (y - x)
    dydt = x * (rho - z) - y
    dzdt = x * y - beta * z
    return [dxdt, dydt, dzdt]

# Initial state (near the origin, but not at it)
initial_state = [0.1, 0.1, 0.1]

# Time vector for the integration (0 to 40 seconds in 0.01 second intervals)
t = np.arange(0, 40, 0.01)

# Integrate the Lorenz equations.
state_trajectories = odeint(lorenz_system, initial_state, t)

# Plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')  # Changed this line
ax.plot(state_trajectories[:,0], state_trajectories[:,1], state_trajectories[:,2])
ax.set_title('Lorenz Attractor')
plt.show()

