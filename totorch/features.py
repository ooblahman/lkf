"""Observables & kernels for computing Koopman operators.
"""

import torch
import random
import numpy as np

""" Observables """

class Observable:
	"""Observable function R^d -> R^k

	Args:
		d: input (state) dimension
		k: output (observable) dimension
		m: data length (memory) required for making a single observation (typically 1 except in delay embedding)

	Base class is identity observable.
	"""
	def __init__(self, d: int, k: int, m: int):
		self.d = d 
		self.k = k 
		self.m = m

	def __call__(self, X: torch.Tensor):
		"""Evaluate observable

		Args: 
			X: state snapshot d (state dimension) x N (trajectory length) 
		"""
		return X

	def preimage(self, Z: torch.Tensor):
		"""Obtain preimage

		Args: 
			Z: observation snapshot k (observed dimension) x M (observed trajectory length)
		"""
		return Z

class ComposedObservable(Observable):
	"""Compose multiple observables (e.g. delay + polynomial) into single observable

	Args:
		seq: list of observables to be composed from left (innermost) to right (outermost). Must have matching interleaving dimensions.
	"""
	def __init__(self, seq: list):
		assert len(seq) > 0, 'At least one observable must be provided'
		for i in range(len(seq)-1):
			assert seq[i].k == seq[i+1].d, f'Output dimension of observable {i} does not match input dimension of observable {i+1}'

		self.seq = seq
		d, k, m = seq[0].d, seq[-1].k, np.prod([obs.m for obs in seq])
		super().__init__(d, k, m)

	def __call__(self, X: torch.Tensor):
		Z = X
		for obs in self.seq:
			Z = obs(Z)
		return Z

	def preimage(self, Z: torch.Tensor):
		X = Z
		for obs in reversed(self.seq):
			X = obs.preimage(X)
		return X

class DelayObservable(Observable):
	"""Delay-coordinate embedding 
	
	Args:
		d: state dimension
		tau: delay length
	"""
	def __init__(self, d: int, tau: int):
		assert tau >= 0
		self.tau = tau
		k = (tau + 1) * d
		m = self.tau + 1
		super().__init__(d, k, m)

	def __call__(self, X: torch.Tensor):
		n = X.shape[1]
		assert n >= self.tau + 1
		Z = torch.cat(tuple(X[:, i:n-self.tau+i] for i in range(self.tau+1)), 0)
		return Z

	def preimage(self, Z: torch.Tensor):
		return Z[:self.d]

class PolynomialObservable(Observable):
	"""Observable consisting of randomly chosen polynomials up to degree d

	Args:
		p: maximum degree of observable
		d: state dimension
		k: observable dimension (i.e. no. of polynomials)

	Note: for reproducibility, set the Python, Numpy, and Torch random seeds.
	TODO: if k is too high, init will loop forever.
	"""
	def __init__(self, p: int, d: int, k: int):

		assert p > 0 and k > 0, "Degree and observable dimension must be at least 1"
		assert k >= d, "Basis dimension must be at least as large as full state observable"
		self.p = p 
		self.psi = dict()

		# add full state observable
		for i in range(d):
			key = [0 for _ in range(i)] + [1] + [0 for _ in range(i+1, d)]
			key = tuple(key)
			self.psi[key] = None

		# add higher-order terms
		terms = [None for _ in range(1, p+1)]
		for i in range(1, p+1):
			channels = np.full((i*d,), np.nan)
			for j in range(d):
				channels[j*i:(j+1)*i] = j
			terms[i-1] = channels

		while len(self.psi) < k:
			deg = random.randint(2, p) # polynomial of random degree
			nonzero_terms = random.choices(terms[deg-1], k=deg)
			key = [0 for _ in range(d)] # exponents of terms
			for term in nonzero_terms:
				key[int(term)] += 1
			key = tuple(key)
			if key not in self.psi: # sample without replacement
				self.psi[key] = None

		super().__init__(d, k, 1)

	def __call__(self, X: torch.Tensor):
		if X.requires_grad:
			Z = [torch.ones((X.shape[1],), device=X.device) for _ in range(self.k)]
			for i, key in enumerate(self.psi.keys()):
				for term, power in enumerate(key):
					if power > 0:
						Z[i] = Z[i] * torch.pow(X[term], power)
			return torch.stack(Z)
		else:
			Z = torch.ones((self.k, X.shape[1]), device=X.device)
			for i, key in enumerate(self.psi.keys()):
				for term, power in enumerate(key):
					if power > 0:
						Z[i] *= torch.pow(X[term], power)
			return Z

	def call_numpy(self, X: np.ndarray):
		if len(X.shape) == 1:
			Z = np.ones(self.k)
		else:
			Z = np.ones((self.k, X.shape[1]))
		for i, key in enumerate(self.psi.keys()):
			for term, power in enumerate(key):
				if power > 0:
					Z[i] *= np.power(X[term], power)
		return Z

	def preimage(self, Z: torch.Tensor): 
		return Z[:self.d]

class GaussianObservable(Observable):
	"""TODO"""
	def __init__(self, sigma: float):
		self.sigma = sigma
		raise Exception('Not implemented')

""" Kernels """

class Kernel:
	"""Positive-definite kernel for Kernel-DMD.
	
	Base class is linear kernel.
	"""
	def __init__(self):
		pass

	def gramian(self, X: torch.Tensor, Y: torch.Tensor):
		"""Compute gramian (correlation matrix)"""
		return X.t()@Y

class GaussianKernel(Kernel):
	def __init__(self, sigma: float):
		self.sigma = sigma

	def gramian(self, X: torch.Tensor, Y: torch.Tensor):
		return torch.exp(-torch.pow(torch.cdist(X, Y, p=2), 2)/(2*self.sigma**2))

class LaplacianKernel(Kernel):
	def __init__(self, sigma: float):
		self.sigma = sigma

	def gramian(self, X: torch.Tensor, Y: torch.Tensor):
		return torch.exp(-torch.cdist(X, Y, p=2)/self.sigma)

class PolynomialKernel(Kernel):
	"""Polynomial kernel
	
	Args:
		c: offset
		p: degree
	"""
	def __init__(self, c: float, p: int):
		self.c, self.p = c, p

	def gramian(self, X: torch.Tensor, Y: torch.Tensor):
		return torch.pow(self.c + torch.mm(X.t(), Y), self.p)

""" Tests """

if __name__ == '__main__': 
	print('Poly obs. test')
	p, d, k = 3, 5, 20
	obs = PolynomialObservable(p, d, k)
	print('Polynomial terms:')
	print(obs.psi.keys())
	X = torch.randn((d, 10))
	Y = obs(X)
	Z = obs.preimage(Y)
	assert (X == Z).all().item(), 'poly preimage incorrect'

	print('Delay obs. test')
	d, tau, n = 3, 3, 6
	obs = DelayObservable(d, tau)
	X = torch.Tensor([[i*x for x in range(d)] for i in range(1, n+1)]).t()
	print('X: ', X)
	Y = obs(X)
	print('Y: ', Y)
	Z = obs.preimage(Y)
	print('Z: ', Z)
	assert (X[:, :Z.shape[1]] == Z).all().item(), 'delay preimage incorrect'

	print('Composed obs. test')
	p, d, tau = 3, 5, 2
	obs1 = PolynomialObservable(p, d, 10)
	obs2 = DelayObservable(obs1.k, tau)
	obs = ComposedObservable([obs1, obs2])
	X = torch.Tensor([[i*x for x in range(d)] for i in range(1, 10)]).t()
	print(X)
	Y = obs(X)
	print(Y)
	Z = obs.preimage(Y)
	print(Z)
	assert (X[:, :Z.shape[1]] == Z).all().item(), 'composed preimage incorrect'