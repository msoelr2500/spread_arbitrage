# -*- coding:utf-8 -*-
import sys
sys.path.append('../')
from myutils import data_window
import unittest


class TestDataWindow(unittest.TestCase):

    def setUp(self):
        self._data_window = data_window(600, 120)

    def test_add_elements(self):
        for i in range(700):
            self._data_window.add(i)

        self.assertEqual(len(self._data_window.datawindow), 600)
        self.assertEqual(self._data_window.datawindow[0], 100)
        self.assertEqual(self._data_window.datawindow[-1], 699)

    def test_is_grow(self):
        def generate(a, b, c):
            self._data_window.clear()
            for i in range(a, b, c):
                self._data_window.add(i)
            is_grow = self._data_window.is_grow()
            return is_grow

        self.assertEqual(generate(0, 10, 1), 0)
        self.assertEqual(generate(0, 600, 1), 1)
        self.assertEqual(generate(0, 800, 1), 1)
        self.assertEqual(generate(800, 0, -1), -1)


if __name__ == '__main__':
    unittest.main()
