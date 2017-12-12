# -*- coding: utf-8 -*-

"""UNIT TESTS FOR BASE

This module contains unit tests for the modopt.base module.

:Author: Samuel Farrens <samuel.farrens@gmail.com>

"""

import pytest
import numpy as np
import numpy.testing as npt
from unittest import main, TestCase
from modopt.base import *


class NPAdjustTestCase(TestCase):

    def setUp(self):

        self.data1 = np.arange(9).reshape((3, 3))
        self.data2 = np.arange(18).reshape((2, 3, 3))

    def tearDown(self):

        self.data1 = None
        self.data2 = None

    def test_rotate(self):

        npt.assert_array_equal(np_adjust.rotate(self.data1),
                               np.array([[8, 7, 6], [5, 4, 3], [2, 1, 0]]),
                               err_msg='Incorrect rotation')

    def test_rotate_stack(self):

        npt.assert_array_equal(np_adjust.rotate_stack(self.data2),
                               np.array([[[8, 7, 6], [5, 4, 3], [2, 1, 0]],
                                         [[17, 16, 15], [14, 13, 12],
                                         [11, 10,  9]]]),
                               err_msg='Incorrect stack rotation')

    def test_pad2d(self):

        npt.assert_array_equal(np_adjust.pad2d(self.data1, (1, 1)),
                               np.array([[0, 0, 0, 0, 0],
                                         [0, 0, 1, 2, 0],
                                         [0, 3, 4, 5, 0],
                                         [0, 6, 7, 8, 0],
                                         [0, 0, 0, 0, 0]]),
                               err_msg='Incorrect padding')

    def test_fancy_transpose(self):

        npt.assert_array_equal(np_adjust.fancy_transpose(self.data2),
                               np.array([[[0, 3, 6], [9, 12, 15]],
                                         [[1, 4, 7], [10, 13, 16]],
                                         [[2, 5, 8], [11, 14, 17]]]),
                               err_msg='Incorrect fancy transpose')

    def test_ftr(self):

        npt.assert_array_equal(np_adjust.ftr(self.data2),
                               np.array([[[0, 3, 6], [9, 12, 15]],
                                         [[1, 4, 7], [10, 13, 16]],
                                         [[2, 5, 8], [11, 14, 17]]]),
                               err_msg='Incorrect fancy transpose: ftr')

    def test_ftl(self):

        npt.assert_array_equal(np_adjust.ftl(self.data2),
                               np.array([[[0, 9], [1, 10], [2, 11]],
                                         [[3, 12], [4, 13], [5, 14]],
                                         [[6, 15], [7, 16], [8, 17]]]),
                               err_msg='Incorrect fancy transpose: ftl')


class TransformTestCase(TestCase):

    def setUp(self):

        self.cube = np.arange(16).reshape((4, 2, 2))
        self.map = np.array([[0, 1, 4, 5], [2, 3, 6, 7], [8, 9, 12, 13],
                             [10, 11, 14, 15]])
        self.matrix = np.array([[0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14],
                                [3, 7, 11, 15]])
        self.layout = (2, 2)

    def tearDown(self):

        self.cube = None
        self.map = None
        self.layout = None

    def test_cube2map(self):

        npt.assert_array_equal(transform.cube2map(self.cube, self.layout),
                               self.map,
                               err_msg='Incorrect transformation: cube2map')

    def test_map2cube(self):

        npt.assert_array_equal(transform.map2cube(self.map, self.layout),
                               self.cube,
                               err_msg='Incorrect transformation: map2cube')

    def test_map2matrix(self):

        npt.assert_array_equal(transform.map2matrix(self.map, self.layout),
                               self.matrix,
                               err_msg='Incorrect transformation: map2matrix')

    def test_matrix2map(self):

        npt.assert_array_equal(transform.matrix2map(self.matrix,
                               self.map.shape), self.map,
                               err_msg='Incorrect transformation: matrix2map')

    def test_cube2matrix(self):

        npt.assert_array_equal(transform.cube2matrix(self.cube),
                               self.matrix,
                               err_msg='Incorrect transformation: cube2matrix')

    def test_matrix2cube(self):

        npt.assert_array_equal(transform.matrix2cube(self.matrix,
                               self.cube[0].shape), self.cube,
                               err_msg='Incorrect transformation: matrix2cube')


if __name__ == '__main__':
    main(verbosity=2)
