import numpy as np
import matplotlib.pyplot as plt
from random_states import random_prob_vector

# define bad functions for generating probability vectors

def random_prob_vector_gaussian(dim):
    x = np.abs(np.random.randn(dim))
    x = x / np.sum(x)
    return x

def random_prob_vector_uniform(dim):
    x = np.random.rand(dim)
    x = x / np.sum(x)
    return x

# generate a bunch of pvs using that function

N = 10000

pvs = np.array([
    [random_prob_vector_gaussian(3) for _ in range(N)],
    [random_prob_vector_uniform(3) for _ in range(N)],
    [random_prob_vector(3) for _ in range(N)],
])
names = ['Gaussian', 'Uniform', 'Fair']

for n, data in zip(names, pvs):
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(projection='3d')
    ax.scatter(data[:,0], data[:,1], data[:,2], s=0.8, alpha=0.5)
    ax.set_xlabel(r'$p_0$')
    ax.set_ylabel(r'$p_1$')
    ax.set_zlabel(r'$p_2$')
    fig.canvas.manager.set_window_title(f'prob_vecs_{n}')
    plt.show()
