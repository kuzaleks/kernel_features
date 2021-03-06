#! usr/bin/python

import numpy as np
import mlpy, pylab, random 
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from scipy.linalg import eig, eigh
from itertools import combinations

def centered_kernel_matrix(Kt, KSub):
    """
    Center samples in the Reproduced Hilbert Space in Kt() on training kernel
    matrix KSub
    Kt = np.random.rand(testTot, trTot)
    KSub = np.random.rand(trTot, trTot)
    """
    assert Kt.shape[1] == KSub.shape[0]
    # Kt.shape = (10, 2), KSub.shape = (2, 4)
    trTotSub = KSub.shape[0]
    trTot = KSub.shape[1]
    KtMan = np.zeros(Kt.shape)
    for i in range(KtMan.shape[0]):
        for j in range(KtMan.shape[1]):
            KtOne = sum(Kt[i, :])
            oneK = sum(KSub.T[:, j])
            sumsumK = sum(sum(KSub))
            KtMan[i, j] = Kt[i, j] - (1.0/trTotSub) * KtOne - (1.0/trTot) * oneK + (1.0 / (trTotSub * trTot)) * sumsumK
    return KtMan
                

def distance_prop(data, prop=np.mean):
    df = pd.DataFrame({'A': np.array([np.linalg.norm(np.array(x) - np.array(y))
                                   for x, y in combinations(data, 2)])})
    return df.mean()
#    return prop([np.linalg.norm(np.array(x) - np.array(y)) for x, y in combinations(data, 2)])


def one_of_c(clabs):
    labsInds = {l: ind for ind, l in enumerate(set(clabs))}
    print labsInds
    Y = np.zeros(shape=(len(clabs), len(set(clabs))))
    for ind in range(len(clabs)):
        Y[ind, len(set(clabs)) - labsInds[clabs[ind]] - 1] = 1.0
    return np.mat(Y)

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

class KernelFunc:
    def __call__(self, x1, x2):
        pass

class KernelRbf(KernelFunc):
    def __init__(self, sigma):
        self.sigma = sigma
    def __call__(self, x1, x2):
        assert isinstance(x1, np.ndarray) and isinstance(x2, np.ndarray)
        return np.exp(-np.dot((x1 - x2), (x1 - x2)) / (2 * self.sigma**2))


class KernelMethod:
    def __init__(self, kernel_func):
        self.kernel_func = kernel_func
    def estim_kbasis(self, trData):
        pass
    def transform(self, data, trDim):
        pass

class kPCA(KernelMethod):
    def estim_kbasis(self, trData):
        self.trData = trData
        Kx = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in self.trData])
        Kx = np.mat(mlpy.kernel_center(Kx, Kx))
        vals, vecs = np.linalg.eig(Kx)

        norm_mat = np.mat(np.diag([1.0/np.sqrt(vals[i]) for i in range(len(vals))]))
        self.vecs = vecs * norm_mat
        print 'mult:', vals[0] * self.vecs[:, 0].T * self.vecs[:, 0]
    def transform(self, data, k=2):
        Kx = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in self.trData])
        Kt = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in data])
        Kt = np.mat(mlpy.kernel_center(Kt, Kx))
        kTransTestData = np.real(Kt * self.vecs[:, :k])
        return np.array(kTransTestData)

class kPLS(KernelMethod):
    def estim_kbasis(self, trData, labels):
        self.trData = trData
        Y = one_of_c(labels)
        Kx = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in self.trData])
        Kx = np.mat(mlpy.kernel_center(Kx, Kx))
        matForEig = np.mat(np.vstack([np.hstack([np.zeros(Kx.shape), Kx * Y]), np.hstack([Y.T * Kx, np.zeros((Y.shape[1], Y.shape[1]))])]))
#        plt.imshow(Kx, cmap = cm.Greys_r)
#        plt.show()
        vals, vecs = np.linalg.eig(matForEig)
        vals = vals[:Kx.shape[0]]
        #print vals[:20]
        vals = np.real(np.array([vals[i] for i in range(1, len(vals), 2)]))
        vecs = vecs[:Kx.shape[0], :Kx.shape[0]]
        self.vecs = vecs[:, 1]
        for i in range(3, vecs.shape[1], 2):
            self.vecs = np.hstack([self.vecs, vecs[:, i]])
        self.vecs = np.mat(self.vecs)
        norm_mat = np.mat(np.diag([np.sqrt(2)/np.sqrt(vals[i]) for i in range(len(vals))]))
        #plobj1 = pylab.plot(vecs[:, 0])
        self.vecs = self.vecs * norm_mat
        print 'mult:', vals[0] * self.vecs[:, 0].T * self.vecs[:, 0]
        #plobj2 = pylab.plot(vecs[:, 0])
        #pylab.show()
        #self.vecs = vecs

    def transform(self, data, k=2):
        Kx = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in self.trData])
        Kt = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in data])
        Kt = np.mat(mlpy.kernel_center(Kt, Kx))
        kTransTestData = np.real(Kt * self.vecs[:, :k])
        return np.array(kTransTestData)

class kOPLS(KernelMethod):
    def estim_kbasis(self, trData, labels, regParam, verbose=True):
        self.trData = trData
        subSetInds = []
        while len(set(subSetInds)) < regParam: subSetInds.append(int(random.uniform(0, len(trData))))
        subSetInds = sorted(list(set(subSetInds)))
        if verbose:
            print "The sub set of indecies for reqularization has been selected"

        self.trDataSubset = np.array([trData[i] for i in subSetInds])
        
        Y = one_of_c(labels)
        Kx = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in self.trDataSubset])
        self.Kx = Kx
        if verbose:
            print "Requralized kernel matrix has been estimated!"
            print "The shape of KxReg is", self.Kx.shape
        Kx = np.mat(mlpy.kernel_center(Kx, Kx))

        Ky = Y * Y.T
        Ky = np.mat(mlpy.kernel_center(Ky, Ky))
        meval = min(np.real(np.linalg.eigvals(Kx * Kx.T)))
        KxKxT = Kx * Kx.T - 1e4 * meval * np.identity(Kx.shape[0])
        if verbose:
            print "Valitidy Check 1: KxKxT is simmetric:", \
                  np.allclose(KxKxT, (KxKxT).T)
        def is_pos_def(x):
            return np.all(np.linalg.eigvals(x) > 0)
        if verbose:
            print "Validity Check 2: KxKxT is positive definite:", \
                  is_pos_def(KxKxT)

#        plt.imshow(Kx, cmap = cm.Greys_r)
#        plt.show()
        vals, vecs = eigh(Kx*Ky*Kx.T, KxKxT)

        vals = np.array([np.real(v) for v in vals])
        print vals        
#        plt.plot(vals)
#        plt.show()
#        vecs = vecs.T
#        lambdas, alphas = zip(*sorted(zip(vals, vecs), reverse=True))
#        lambdas = np.array([l for l in lambdas])
#        alphas = np.mat([col for col in alphas])

#        args = vals.argsort(axis = 0)
#        alphas = np.mat(vecs[list(reversed(args))])
#        alphas = alphas.T
#        lambdas = sorted(vals, reverse=True)
        
        lambdas = vals
        alphas = np.mat(vecs)
        print type(lambdas), type(alphas)
#        plt.plot(lambdas)

#        normTerm = (alpha.T * Kx) * (Kx * alpha)
#        alpha = np.mat(vecs[:, 3]).T
#        print 'mult before norm:', 1.0 / ((alpha.T * Kx) * (Kx * alpha))

        norm_mat = np.mat(np.diag([1.0/np.sqrt(((alphas[:, i].T * Kx) * (Kx.T * alphas[:, i]))[0,0]) for i in range(len(lambdas))]))
        alphas = alphas * norm_mat
        alpha = np.mat(alphas[:, 44])
#        alpha = alpha / np.sqrt(normTerm)
        print 'mult after norm:', (alpha.T * Kx) * (Kx.T * alpha)
        
        self.vecs = alphas
#        self.vecs = self.vecs * norm_mat
#        plt.show()

    def transform(self, data, k=2):
        Kt = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trDataSubset] for xi in data])
        Kt = np.mat(mlpy.kernel_center(Kt, self.Kx.T))
        kTransTestData = np.real(Kt * self.vecs[:, -k:])
        return np.array(kTransTestData)


class kCCAWrapper(KernelMethod):
    def _read_dat(self, fn):
        f = open(fn, 'r')
        data = []
        for line in f:
            if not line.startswith('#') and len(line.split()) > 0:
                data.append([float(numb) for numb in line.split()])
        f.close()
        return data
        
    def load_basis(self, Kxfn, Wxfn, trainfn):
        self.Kx = np.mat(self._read_dat(Kxfn))
        self.vecs = np.mat(self._read_dat(Wxfn))
        self.trData = self._read_dat(trainfn)

    def transform(self, data, k=2):
        Kt = np.mat([[self.kernel_func(np.array(xi), np.array(xj)) for xj in self.trData] for xi in data])
        Kt = np.mat(mlpy.kernel_center(Kt, self.Kx))
        kTransTestData = np.real(Kt * self.vecs[:, :k])
        return np.array(kTransTestData)
