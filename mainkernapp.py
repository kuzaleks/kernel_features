#! /usr/bin/python

import sys

import numpy as np
import numpy
import matplotlib.pyplot as plt
import mlpy
from functools import partial
import yaml

def line(stDot, finDot, res=100):
    assert len(stDot) == len(finDot)
    return np.array([alpha*stDot + (1 - alpha)*finDot for alpha in np.linspace(0, 1, res)])

def rbf_closure(sigma):
    def rbf(x1, x2):
        assert isinstance(x1, np.ndarray) and isinstance(x2, np.ndarray)
        return np.exp(-np.dot((x1 - x2), (x1 - x2)) / (2 * sigma**2))
    return rbf

def polynomial_closure(ext):
    def polynomial(x1, x2):
        assert isinstance(x1, np.ndarray) and isinstance(x2, np.ndarray)
        return np.dot(x1, x2) ** ext
    return polynomial


def draw_data(data, clabs, kernel_func):
    fig = plt.figure(1) # plot

    print data.shape
    ax1 = plt.subplot(121)
    plot1 = plt.scatter(data[:, 0], data[:, 1], c=clabs)

    Kx = np.mat([[kernel_func(xi, xj) for xj in data] for xi in data])
    Kx = np.mat(mlpy.kernel_center(Kx, Kx))
    vals, vecs = np.linalg.eig(Kx)

    gK = mlpy.kernel_gaussian(data, data, sigma=2)
    print "gK is eqaul to Kx", np.allclose(gK, Kx)
    gaussian_pca = mlpy.KPCA()
    gaussian_pca.learn(gK)

    stream = open('vecs', 'w')
    yaml.dump(np.real(vecs), stream, default_flow_style=False)
    stream.close()

    stream = open('vals.yaml', 'w')
    yaml.dump(np.real(vals), stream, default_flow_style=False)
    stream.close()

    
    print "mult before normalization", vals[0]*vecs[:, 0].T*vecs[:, 0]

    norm_mat = np.mat(np.diag([1.0/np.sqrt(vals[i]) for i in range(len(vals))]))
    vecs = vecs * norm_mat
    print 'mult:', vals[0] * vecs[:, 0].T * vecs[:, 0]

    stream = open('norm_vecs.yaml', 'w')
    yaml.dump(np.real(vecs), stream, default_flow_style=False)
    stream.close()

    mlpy_vecs = np.mat(gaussian_pca.coeff())
    print 'mlpy_mult:', gaussian_pca.evals()[0] * mlpy_vecs[:, 0].T * mlpy_vecs[:, 0]
    data_k_trans = np.real(Kx.T * vecs[:, :2])
    data_k_trans = np.array(data_k_trans)
    ax2 = plt.subplot(122)
    plot2 = plt.scatter(data_k_trans[:, 0], data_k_trans[:, 1], c=clabs)

    plt.show()


def draw_mlpy_example(data, clabs):
    gK = mlpy.kernel_gaussian(data, data, sigma=2) # gaussian kernel matrix
    gaussian_pca = mlpy.KPCA()
    gaussian_pca.learn(gK)
    gz = gaussian_pca.transform(gK, k=2)

    stream = open('mlpy_vecs.yaml', 'w')
    yaml.dump(np.mat(gaussian_pca.coeff()), stream, default_flow_style=False)
    stream.close()

    stream = open('mlpy_vals.yaml', 'w')
    yaml.dump(np.real(gaussian_pca.evals()), stream, default_flow_style=False)
    stream.close()

    fig = plt.figure(1)
    ax1 = plt.subplot(121)
    plot1 = plt.scatter(data[:, 0], data[:, 1], c=clabs)
    title1 = ax1.set_title('Original data')
    ax2 = plt.subplot(122)
    plot2 = plt.scatter(gz[:, 0], gz[:, 1], c=clabs)
    title2 = ax2.set_title('Gaussian kernel')
    plt.show()

def main():
    args = sys.argv[1:]
    if not args:
        print "--drawdata"    
        sys.exit(0)

    if args[0] == "--drawdata":
        np.random.seed(0)
        np.random.seed(0)
        x = np.zeros((150, 2))
        y = np.empty(150, dtype=np.int)
        theta = np.random.normal(0, np.pi, 50)
        r = np.random.normal(0, 0.1, 50)
        x[0:50, 0] = r * np.cos(theta)
        x[0:50, 1] = r * np.sin(theta)
        y[0:50] = 0
        theta = np.random.normal(0, np.pi, 50)
        r = np.random.normal(2, 0.1, 50)
        x[50:100, 0] = r * np.cos(theta)
        x[50:100, 1] = r * np.sin(theta)
        y[50:100] = 1
        theta = np.random.normal(0, np.pi, 50)
        r = np.random.normal(5, 0.1, 50)
        x[100:150, 0] = r * np.cos(theta)
        x[100:150, 1] = r * np.sin(theta)
        y[100:150] = 2

#        kernel_func = partial(mlpy.kernel_gaussian, sigma=2.0)
        kernel_func = rbf_closure(2.0)
        draw_data(x, y, kernel_func)
        draw_mlpy_example(x, y)


if __name__ == "__main__":
    print "Hello!"
    main()
