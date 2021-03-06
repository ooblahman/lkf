import numpy as np
import torch
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def system(z, t, alpha, beta, gamma, delta, u):
	"""System definition for scipy.integrate.odeint format"""
	x, y = z
	xdot = y
	ydot = -delta*y - alpha*x - beta*(x**3) + gamma*u(t)
	return xdot, ydot

def dataset(tmax: int, n: int, alpha=-1.0, beta=1.0, gamma=0.5, delta=0.3, omega=1.2, x0=1.0, y0=0.0, u=None):
	"""Duffing oscillator 
	
	Args:
		tmax: # seconds 
		n: # data points (dt = tmax / n)
		x0: initial condition
		y0: initial condition
		u: control signal (Callable : time -> float)
	"""
	t = np.linspace(0, tmax, n)
	if u is None:
		u = lambda t: np.cos(omega*t)
	X = odeint(system, (x0, y0), t, args=(alpha, beta, gamma, delta, u))
	return torch.from_numpy(X.T).float()

if __name__ == '__main__': 
	t, n = 80, 4000
	taxis = np.linspace(0, t, n)

	# X, Y = dataset(t, n, gamma=0.0, x0=-1.0, y0=2.0)
	# plt.figure(figsize=(8,8))
	# plt.title('Unforced')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.2)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with period-1 oscillation')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.28)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with period-2 oscillation')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.29)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with period-4 oscillation')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.37)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with period-5 oscillation')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.50)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with chaos')
	# plt.plot(X[0], X[1])

	# X, Y = dataset(t, n, gamma=0.65)
	# plt.figure(figsize=(8,8))
	# plt.title('Forced with period-2 oscillation (2)')
	# plt.plot(X[0], X[1])

	u = lambda t: np.sign(np.cos(np.pi*t/0.3))
	X, Y = dataset(t, n, gamma=0.5, u=u)
	fig, axs = plt.subplots(2, 1, figsize=(12,8))
	fig.suptitle('Forced with square wave')
	axs[0].plot(X[0], X[1])
	axs[1].plot(taxis, [u(t) for t in taxis])

	plt.show()
