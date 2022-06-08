#!/usr/bin/env python
# -*- coding: utf-8 -*-

from modules.pixelate_algorithm import PixelateAlgorithm
import sys

if __name__ == "__main__":
    filename = "parameters.txt"
    params = open(filename).read().splitlines()

    algo = PixelateAlgorithm()

    # Запуск через консоль.
    # Пример ввода: python "main.py" "pictures/Lenna.jpg" 25 100
    if len(params) < 4:
        print('Wrong input!',
              'Input file should be like: ',
              '\t filename.jpg/jpeg',
              '\t colours_number',
              '\t crosses_number',
              '\t producer_colour_map', sep='\n')
        sys.exit(0)
    else:
        algo(params[0], params[1], params[2], params[3])
