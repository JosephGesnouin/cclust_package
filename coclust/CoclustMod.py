# -*- coding: utf-8 -*-
import numpy as np
import scipy.sparse as sp

# from __future__ import absolute_import


from .utils.initialization import random_init
print(__name__)


class CoclustMod(object):
    """Co-clustering by direct maximization of graph modularity.

    Parameters
    ----------

    n_clusters : int, optional, default: 2
        Number of co-clusters to form

    init : numpy array or scipy sparse matrix, shape (n_features, n_clusters), \
        optional, default: None
        Initial column labels

    max_iter : int, optional, default: 20
        Maximum number of iterations

    Attributes
    ----------
    row_labels_ : array-like, shape (n_rows,)
        Bicluster label of each row

    column_labels_ : array-like, shape (n_cols,)
        Bicluster label of each column

    modularity : float
        Final value of the modularity

    modularities : list
        Record of all computed modularity values for all iterations

    References
    ----------
    * Ailem M., Role F., Nadif M., Co-clustering Document-term Matrices by \
    Direct Maximization of Graph Modularity. CIKM 2015: 1807-1810
    """

    def __init__(self, n_clusters=2, init=None, max_iter=20):
        self.n_clusters = n_clusters
        self.init = init
        self.max_iter = max_iter
        self.row_labels_ = None
        self.column_labels_ = None
        self.modularity = float("NaN")
        self.modularities = []

    def fit(self, X, y=None):
        """Perform co-clustering by direct maximization of graph modularity.

        Parameters
        ----------
        X : numpy array or scipy sparse matrix, shape=(n_samples, n_features)
            Matrix to be analyzed
        """

        if not sp.issparse(X):
            X = np.matrix(X)

        if self.init is None:
            W = random_init(self.n_clusters, X.shape[1])
        else:
            W = np.matrix(self.init, dtype=float)

        Z = np.zeros((X.shape[0], self.n_clusters))

        # Compute the modularity matrix
        row_sums = np.matrix(X.sum(axis=1))
        col_sums = np.matrix(X.sum(axis=0))
        N = float(X.sum())
        indep = (row_sums.dot(col_sums)) / N

        # B is a numpy matrix
        B = X - indep

        # Loop
        m_begin = float("-inf")
        change = True
        iteration = 1
        while change:
            change = False

            # Reassign rows
            BW = B.dot(W)
            for idx, k in enumerate(np.argmax(BW, axis=1)):
                Z[idx, :] = 0
                Z[idx, k] = 1

            # Reassign columns
            BtZ = (B.T).dot(Z)
            for idx, k in enumerate(np.argmax(BtZ, axis=1)):
                W[idx, :] = 0
                W[idx, k] = 1

            k_times_k = (Z.T).dot(BW)
            m_end = np.trace(k_times_k)

            if np.abs(m_end - m_begin) > 1e-9 and iteration < self.max_iter:
                self.modularities.append(m_end/N)
                m_begin = m_end
                change = True

        self.row_labels_ = np.argmax(Z, axis=1).tolist()
        self.column_labels_ = np.argmax(W, axis=1).tolist()
        self.modularity = m_end/N

        print ("Final modularity", m_end / N)

    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Parameters
        ----------
        deep: boolean, optional
            If True, will return the parameters for this estimator and
            contained subobjects that are estimators

        Returns
        -------
        dict
            Mapping of string to any parameter names mapped to their values
        """
        return {"init": self.init,
                "n_clusters": self.n_clusters,
                "max_iter": self.max_iter
                }

    def set_params(self, **parameters):
        """Set the parameters of this estimator.

        The method works on simple estimators as well as on nested objects
        (such as pipelines). The former have parameters of the form
        ``<component>__<parameter>`` so that it's possible to update each
        component of a nested object.

        Returns
        -------
        CoclustMod
            self
        """
        for parameter, value in parameters.items():
            setattr(self, parameter, value)
        return self

    def get_indices(self, i):
        """Give the row and column indices of the i’th co-cluster.

        Parameters
        ----------
        i : integer
            Index of the co-cluster

        Returns
        -------
        (list, list)
            (row indices, column indices)
        """
        row_indices = [index for index, label in enumerate(self.row_labels_)
                       if label == i]
        column_indices = [index for index, label
                          in enumerate(self.column_labels_) if label == i]
        return (row_indices, column_indices)

    def get_shape(self, i):
        """Give the shape of the i’th co-cluster.

        Parameters
        ----------
        i : integer
            Index of the co-cluster

        Returns
        -------
        (int, int)
            (number of rows, number of columns)
        """
        row_indices, column_indices = self.get_indices(i)
        return (len(row_indices), len(column_indices))

    def get_submatrix(self, i, data):
        """Returns the submatrix corresponding to bicluster `i`.

        Works with sparse matrices. Only works if ``rows_`` and
        ``columns_`` attributes exist.
        """
        row_ind, col_ind = self.get_indices(i)
        return data[row_ind[:, np.newaxis], col_ind]
