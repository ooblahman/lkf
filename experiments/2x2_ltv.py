""" Partially known LTV example """ 

from systems.linear import *
from utils import set_seed
from lib.lkf import LKF
from lib.kf import KF

from typing import Callable
import numpy as np
import pandas as pd
import pdb
import scipy.stats as stats

import matplotlib.pyplot as plt

set_seed(9001)

dt = 1e-3
T = 60.
x0 = np.array([-1., -1.])

z = TimeVarying(x0, dt, 0.0, 1.0, f=1/5)
F_hat = lambda t: z.F(0)
eta = lambda t: F_hat(t) - z.F(t)

print(F_hat(0))
f1 = KF(x0, F_hat, z.H, z.Q, z.R, dt)
f2 = LKF(x0, F_hat, z.H, z.Q, z.R, dt, tau=0.25, eps=3e-2, gamma=0.9)

# pdb.set_trace()

max_err = 2.
max_eta_err = 100

hist_t = []
hist_z = []
hist_f1_x = []
hist_f2_x = []
hist_f1_err = []
hist_f2_err = []
hist_eta = []
while z.t <= T:
	z_t = z()
	x1_t, err1_t = f1(z_t)
	x2_t, err2_t = f2(z_t)
	hist_z.append(z_t)
	hist_t.append(z.t)
	hist_f1_x.append(x1_t) 
	hist_f2_x.append(x2_t) 
	hist_f1_err.append(err1_t)
	hist_f2_err.append(err2_t)
	hist_eta.append(f2.eta_t.copy())

	# Error condition 1
	if np.linalg.norm(err2_t) > max_err:
		print('Error overflowed!')
		break

	# Error condition 2
	if np.linalg.norm(f2.eta_t - eta(z.t)) > max_eta_err:
		print('Variation error overflowed!')
		break

# start, end = None, 20000 # for case analysis
start, end = None, None # for case analysis
every = 1

hist_t = np.array(hist_t)[start:end:every]
hist_z = np.array(hist_z)[start:end:every]
hist_f1_x = np.array(hist_f1_x)[start:end:every]
hist_f2_x = np.array(hist_f2_x)[start:end:every]
hist_f1_err = np.array(hist_f1_err)[start:end:every]
hist_f2_err = np.array(hist_f2_err)[start:end:every]
hist_eta = np.array(hist_eta)[start:end:every]

# pdb.set_trace()

fig, axs = plt.subplots(2, 5, figsize=(20, 20))
	
# axs[0,0].plot(hist_z[:,0], hist_z[:,1], color='blue', label='obs')
# axs[0,0].plot(hist_f1_x[:,0], hist_f1_x[:,1], color='orange', label='est')
# axs[0,0].legend()
# axs[0,0].set_title('System')

# axs[1,0].plot(hist_z[:,0], hist_z[:,1], color='blue', label='obs')
# axs[1,0].plot(hist_f2_x[:,0], hist_f2_x[:,1], color='orange', label='est')
# axs[1,0].legend()

axs[0,0].plot(hist_t, hist_z[:,0], color='blue', label='obs')
axs[0,0].plot(hist_t, hist_f1_x[:,0], color='orange', label='est')
axs[0,0].set_title('Axis 1')

axs[1,0].plot(hist_t, hist_z[:,0], color='blue', label='obs')
axs[1,0].plot(hist_t, hist_f2_x[:,0], color='orange', label='est')

axs[0,1].plot(hist_t, hist_z[:,1], color='blue', label='obs')
axs[0,1].plot(hist_t, hist_f1_x[:,1], color='orange', label='est')
axs[0,1].set_title('Axis 2')

axs[1,1].plot(hist_t, hist_z[:,1], color='blue', label='obs')
axs[1,1].plot(hist_t, hist_f2_x[:,1], color='orange', label='est')

axs[0,2].plot(hist_t, hist_f1_err[:,0])
axs[0,2].set_title('Axis 1 error')
axs[0,2].set_ylim((-1., 1.))

axs[1,2].plot(hist_t, hist_f2_err[:,0])
axs[1,2].set_ylim((-1., 1.))

axs[0,3].plot(hist_t, hist_f1_err[:,1])
axs[0,3].set_title('Axis 2 error')
axs[0,3].set_ylim((-1., 1.))

axs[1,3].plot(hist_t, hist_f2_err[:,1])
axs[1,3].set_ylim((-1., 1.))

var_err_bs = -np.array(list(map(eta, hist_t)))
var_err_rast_bs = var_err_bs.reshape((var_err_bs.shape[0], 4))
axs[0,4].plot(hist_t, var_err_rast_bs[:,0])
axs[0,4].plot(hist_t, var_err_rast_bs[:,1])
axs[0,4].plot(hist_t, var_err_rast_bs[:,2])
axs[0,4].plot(hist_t, var_err_rast_bs[:,3])
axs[0,4].set_title('Variation error (rasterized)')
axs[0,4].set_ylim((-.5, .5))

var_err = hist_eta - np.array(list(map(eta, hist_t)))
var_err_rast = var_err.reshape((var_err.shape[0], 4))
axs[1,4].plot(hist_t, var_err_rast[:,0])
axs[1,4].plot(hist_t, var_err_rast[:,1])
axs[1,4].plot(hist_t, var_err_rast[:,2])
axs[1,4].plot(hist_t, var_err_rast[:,3])
axs[1,4].set_ylim((-.5, .5))

plt.setp(axs[0, 0], ylabel='KF')
plt.setp(axs[1, 0], ylabel='LKF')

plt.show()
