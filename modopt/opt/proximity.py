# -*- coding: utf-8 -*-

"""PROXIMITY OPERATORS

This module contains classes of proximity operators for optimisation

:Author: Samuel Farrens <samuel.farrens@cea.fr>

"""

import numpy as np
try:
    from sklearn.isotonic import isotonic_regression
except ImportError:
    import_sklearn = False
else:
    import_sklearn = True

from modopt.base.types import check_callable
from modopt.signal.noise import thresh
from modopt.signal.svd import svd_thresh, svd_thresh_coef
from modopt.signal.positivity import positive
from modopt.math.matrix import nuclear_norm
from modopt.base.transform import cube2matrix, matrix2cube
from modopt.interface.errors import warn


class ProximityParent(object):

    def __init__(self, op, cost):

        self.op = op
        self.cost = cost

    @property
    def op(self):
        """Linear Operator

        This method defines the linear operator

        """

        return self._op

    @op.setter
    def op(self, operator):

        self._op = check_callable(operator)

    @property
    def cost(self):
        """Cost Contribution

        This method defines the proximity operator's contribution to the total
        cost

        """

        return self._cost

    @cost.setter
    def cost(self, method):

        self._cost = check_callable(method)


class IdentityProx(ProximityParent):
    """Identity Proxmity Operator

    This is a dummy class that can be used as a proximity operator

    Notes
    -----
    The identity proximity operator contributes 0.0 to the total cost

    """

    def __init__(self):

        self.op = lambda x: x
        self.cost = lambda x: 0.0


class Positivity(ProximityParent):
    """Positivity Proximity Operator

    This class defines the positivity proximity operator

    """

    def __init__(self):

        self.op = lambda x: positive(x)
        self.cost = self._cost_method

    def _cost_method(self, *args, **kwargs):
        """Calculate positivity component of the cost

        This method returns 0 as the posivituty does not contribute to the
        cost.

        Returns
        -------
        float zero

        """

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - Min (X):', np.min(args[0]))

        return 0.0


class SparseThreshold(ProximityParent):
    """Threshold proximity operator

    This class defines the threshold proximity operator

    Parameters
    ----------
    linear : class
        Linear operator class
    weights : np.ndarray
        Input array of weights
    thresh_type : str {'hard', 'soft'}, optional
        Threshold type (default is 'soft')

    """

    def __init__(self, linear, weights, thresh_type='soft'):

        self._linear = linear
        self.weights = weights
        self._thresh_type = thresh_type
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        """Operator Method

        This method returns the input data thresholded by the weights

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray thresholded data

        """

        threshold = self.weights * extra_factor

        return thresh(data, threshold, self._thresh_type)

    def _cost_method(self, *args, **kwargs):
        """Calculate sparsity component of the cost

        This method returns the l1 norm error of the weighted wavelet
        coefficients

        Returns
        -------
        float sparsity cost component

        """

        cost_val = np.sum(np.abs(self.weights * self._linear.op(args[0])))

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - L1 NORM (X):', cost_val)

        return cost_val


class LowRankMatrix(ProximityParent):
    r"""Low-rank proximity operator

    This class defines the low-rank proximity operator

    Parameters
    ----------
    thresh : float
        Threshold value
    treshold_type : str {'hard', 'soft'}
        Threshold type (options are 'hard' or 'soft')
    lowr_type : str {'standard', 'ngole'}
        Low-rank implementation (options are 'standard' or 'ngole')
    operator : class
        Operator class ('ngole' only)

    Examples
    --------
    >>> from modopt.opt.proximity import LowRankMatrix
    >>> a = np.arange(9).reshape(3, 3).astype(float)
    >>> inst = LowRankMatrix(10.0, thresh_type='hard')
    >>> inst.op(a)
    array([[[  2.73843189,   3.14594066,   3.55344943],
            [  3.9609582 ,   4.36846698,   4.77597575],
            [  5.18348452,   5.59099329,   5.99850206]],

           [[  8.07085295,   9.2718846 ,  10.47291625],
            [ 11.67394789,  12.87497954,  14.07601119],
            [ 15.27704284,  16.47807449,  17.67910614]]])
    >>> inst.cost(a, verbose=True)
     - NUCLEAR NORM (X): 469.391329425
    469.39132942464983

    """

    def __init__(self, thresh, thresh_type='soft',
                 lowr_type='standard', operator=None):

        self.thresh = thresh
        self.thresh_type = thresh_type
        self.lowr_type = lowr_type
        self.operator = operator
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        """Operator

        This method returns the input data after the singular values have been
        thresholded

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray SVD thresholded data

        """

        # Update threshold with extra factor.
        threshold = self.thresh * extra_factor

        if self.lowr_type == 'standard':
            data_matrix = svd_thresh(cube2matrix(data), threshold,
                                     thresh_type=self.thresh_type)

        elif self.lowr_type == 'ngole':
            data_matrix = svd_thresh_coef(cube2matrix(data), self.operator,
                                          threshold,
                                          thresh_type=self.thresh_type)

        new_data = matrix2cube(data_matrix, data.shape[1:])

        # Return updated data.
        return new_data

    def _cost_method(self, *args, **kwargs):
        """Calculate low-rank component of the cost

        This method returns the nuclear norm error of the deconvolved data in
        matrix form

        Returns
        -------
        float low-rank cost component

        """

        cost_val = self.thresh * nuclear_norm(cube2matrix(args[0]))

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - NUCLEAR NORM (X):', cost_val)

        return cost_val


class LinearCompositionProx(ProximityParent):
    """Proximity operator of a linear composition

    This class defines the proximity operator of a function given by
    a composition between an initial function whose proximity operator is known
    and an orthogonal linear function.

    Parameters
    ----------
    linear_op : class instance
        Linear operator class
    prox_op : class instance
        Proximity operator class
    """
    def __init__(self, linear_op, prox_op):
        self.linear_op = linear_op
        self.prox_op = prox_op
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        r"""Operator method

        This method returns the scaled version of the proximity operator as
        given by Lemma 2.8 of [CW2005].

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray result of the scaled proximity operator
        """
        return self.linear_op.adj_op(
            self.prox_op.op(self.linear_op.op(data), extra_factor=extra_factor)
        )

    def _cost_method(self, *args, **kwargs):
        """Calculate the cost function associated to the composed function

        Returns
        -------
        float the cost of the associated composed function
        """
        return self.prox_op.cost(self.linear_op.op(args[0]), **kwargs)


class ProximityCombo(ProximityParent):
    r"""Proximity Combo

    This class defines a combined proximity operator

    Parameters
    ----------
    operators : list
        List of proximity operator class instances

    Examples
    --------
    >>> from modopt.opt.proximity import ProximityCombo, ProximityParent
    >>> a = ProximityParent(lambda x: x ** 2, lambda x: x ** 3)
    >>> b = ProximityParent(lambda x: x ** 4, lambda x: x ** 5)
    >>> c = ProximityCombo([a, b])
    >>> c.op([2, 2])
    array([4, 16], dtype=object)
    >>> c.cost([2, 2])
    40

    """

    def __init__(self, operators):

        operators = self._check_operators(operators)
        self.operators = operators
        self.op = self._op_method
        self.cost = self._cost_method

    def _check_operators(self, operators):
        """ Check Inputs

        This method cheks that the input operators and weights are correctly
        formatted

        Parameters
        ----------
        operators : list, tuple or np.ndarray
            List of linear operator class instances

        Returns
        -------
        np.array operators

        Raises
        ------
        TypeError
            For invalid input type

        """

        if not isinstance(operators, (list, tuple, np.ndarray)):
            raise TypeError('Invalid input type, operators must be a list, '
                            'tuple or numpy array.')

        operators = np.array(operators)

        if not operators.size:
            raise ValueError('Operator list is empty.')

        for operator in operators:
            if not hasattr(operator, 'op'):
                raise ValueError('Operators must contain "op" method.')
            if not hasattr(operator, 'cost'):
                raise ValueError('Operators must contain "cost" method.')
            operator.op = check_callable(operator.op)
            operator.cost = check_callable(operator.cost)

        return operators

    def _op_method(self, data, extra_factor=1.0):
        """Operator

        This method returns the result of applying all of the proximity
        operators to the data

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray result

        """

        res = np.empty(len(self.operators), dtype=np.ndarray)

        for i in range(len(self.operators)):
            res[i] = self.operators[i].op(data[i], extra_factor=extra_factor)

        return res

    def _cost_method(self, *args, **kwargs):
        """Calculate combined proximity operator components of the cost

        This method returns the sum of the cost components from each of the
        proximity operators

        Returns
        -------
        float combinded cost components

        """

        return np.sum([operator.cost(data) for operator, data in
                       zip(self.operators, args[0])])


class OrderedWeightedL1Norm(ProximityParent):
    r"""Ordered Weighted L1 norm proximity operator

    This class defines the OWL proximity operator described in [F2014]

    Parameters
    ----------
    weights : np.ndarray
        Weights values they should be sorted in a non-increasing order

    Examples
    --------
    >>> import numpy as np
    >>> from modopt.opt.proximity import OrderedWeightedL1Norm
    >>> A = np.arange(5)*5
    array([ 0,  5, 10, 15, 20])
    >>> prox_op = OrderedWeightedL1Norm(np.arange(5))
    >>> prox_op.weights
    array([4, 3, 2, 1, 0])
    >>> prox_op.op(A)
    array([ 0.,  4.,  8., 12., 16.])
    >>> prox_op.cost(A, verbose=True)
     - OWL NORM (X): 150
    150
    """

    def __init__(self, weights):
        if not import_sklearn:  # pragma: no cover
            raise ImportError('Required version of Scikit-Learn package not'
                              ' found see documentation for details: '
                              'https://cea-cosmic.github.io/ModOpt/'
                              '#optional-packages')

        self.weights = np.sort(weights.flatten())[::-1]
        if (self.weights < 0).any():
            raise ValueError("All the entries of the weights should be"
                             " positive")
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        """Operator

        This method returns the input data after the a clustering and a
        thresholding. Implements (Eq 24) in F2014

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray thresholded data

        """

        # Update threshold with extra factor.
        threshold = self.weights * extra_factor

        # Squeezing the data
        data_squeezed = np.squeeze(data)

        # Sorting (non increasing order) input vector's absolute values
        data_abs = np.abs(data_squeezed)
        data_abs_sort_idx = np.argsort(data_abs)[::-1]
        data_abs = data_abs[data_abs_sort_idx]

        # Projection onto the monotone non-negative cone using
        # isotonic_regression

        data_abs = isotonic_regression(data_abs - threshold, y_min=0,
                                       increasing=False)
        # Unsorting the data
        data_abs_unsorted = data_abs[data_abs_sort_idx]

        # Putting the sign back
        with np.errstate(invalid='ignore'):
            sign_data = data_squeezed / np.abs(data_squeezed)

        # Removing NAN caused by the sign
        sign_data[np.isnan(sign_data)] = 0

        return np.reshape(sign_data * data_abs_unsorted, data.shape)

    def _cost_method(self, *args, **kwargs):
        """Calculate OWL component of the cost

        This method returns the ordered weighted l1 norm of the data.

        Returns
        -------
        float OWL cost component

        """

        cost_val = np.sum(self.weights * np.sort(np.squeeze(
            np.abs(args[0]))[::-1]))

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - OWL NORM (X):', cost_val)

        return cost_val


class Ridge(ProximityParent):
    r"""L2-norm proximity operator (i.e. shrinkage)

    This class defines the L2-norm proximity operator

    Parameters
    ----------
    linear : class
        Linear operator class
    weights : np.ndarray
        Input array of weights

    Notes
    -----
    Implements the following equation:
    ..math::
    prox(y) = \underset{x \in \mathbb{C}^N}{argmin} 0.5 \|x-y\||_2^2 + \alpha
     \|x\|_2^2
    """

    def __init__(self, linear, weights, thresh_type='soft'):

        self._linear = linear
        self.weights = weights
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        """Operator Method

        This method returns the input data shrinked by the weights

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray thresholded data

        """

        threshold = self.weights * extra_factor * 2

        return self._linear.op(data) / (1 + threshold)

    def _cost_method(self, *args, **kwargs):
        """Calculate Ridge component of the cost

        This method returns the l2 norm error of the weighted wavelet
        coefficients

        Returns
        -------
        float sparsity cost component

        """

        cost_val = np.sum(np.abs(self.weights * self._linear.op(args[0])**2))

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - L2 NORM (X):', cost_val)

        return cost_val


class ElasticNet(ProximityParent):
    r"""Linear combination between L2 and L1 norm proximity operator,
    described in [Z2005]

    This class defines the Elastic net proximity operator

    Parameters
    ----------
    alpha : np.ndarray
        Weights for the L2 norm

    beta : np.ndarray
        Weights for the L1 norm

    Notes
    -----
    ..math::
    prox(y) = \underset{x \in \mathbb{C}^N}{argmin} 0.5 \|x-y\||_2^2 + \alpha
     \|x\|_2^2 + beta*||x||_1
    """

    def __init__(self, linear, alpha, beta, naive=False):

        self._linear = linear
        self.alpha = alpha
        self.beta = beta
        self.op = self._op_method
        self.cost = self._cost_method

    def _op_method(self, data, extra_factor=1.0):
        """Operator Method

        This method returns the input data shrinked by the weights

        Parameters
        ----------
        data : np.ndarray
            Input data array
        extra_factor : float
            Additional multiplication factor

        Returns
        -------
        np.ndarray thresholded data

        """

        soft_threshold = self.beta * extra_factor
        normalization = (self.alpha * 2 * extra_factor + 1)
        return thresh(data, soft_threshold, 'soft') / normalization

    def _cost_method(self, *args, **kwargs):
        """Calculate Ridge component of the cost

        This method returns the l2 norm error of the weighted wavelet
        coefficients

        Returns
        -------
        float sparsity cost component

        """

        cost_val = np.sum(np.abs(self.alpha * self._linear.op(args[0])**2) +
                          np.abs(self.beta * self._linear.op(args[0])))

        if 'verbose' in kwargs and kwargs['verbose']:
            print(' - ELASTIC NET (X):', cost_val)

        return cost_val
