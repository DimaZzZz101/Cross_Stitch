#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import numpy as np
import collections


class DMC:
    dmc_palette = {}  # Палитра DMC.

    def __init__(self, producer):
        """
        Инициализация словаря цветами из палитры DMC.

        Формат: код цвета(ключ): RED, BLUE, GREEN, название цвета, код цвета.
        """
        with open(producer, mode='r') as table:
            self.dmc_palette = collections.OrderedDict(
                {row[0]: [int(row[1]), int(row[2]), int(row[3]), row[4], row[0]] for row in csv.reader(table)})

    def get_dmc_rgb(self, colour):
        """
        Получение RGB кодов из таблицы цветов DMC.

        На входе: colour - исходный цвет.
        На выходе: tuple из трех составляющих цвета (rgb) из палитры DMC, которые наиболее близки к исходному.
        """
        dmc_colour = self.get_dmc_code(colour)
        return dmc_colour[0], dmc_colour[1], dmc_colour[2]

    def get_dmc_code(self, colour):
        """
        Получение записи из словаря с цветом из палитры DMC, максимально приближенным к текущему цвету пикселя.

        На входе: colour - исходный цвет.
        На выходе: запись из словаря с найденным цветом из палитры DMC.
        """
        min_distance = 100000000
        colour_code = ''
        for key in self.dmc_palette:
            distance = self.get_distance(self.dmc_palette[key], colour)
            if distance < min_distance:
                colour_code = key
                min_distance = distance
        return self.dmc_palette[colour_code]

    @staticmethod
    def get_distance(colour1, colour2):
        """
        Расчет расстояния между двумя цветами (евклидова метрика).

        На входе:
            colour1: Запись из словаря палитры DMC с предполагаемым цветом.
            colour2: Три составляющие цвета для которого ищем цвет в палитре.

        На выходе:
            Евклидово расстояние между цветами.
        """
        (r_1, g_1, b_1, colour_name, colour_code) = colour1
        (r_2, g_2, b_2) = colour2
        return np.sqrt(((r_1 - r_2) ** 2) + ((g_1 - g_2) ** 2) + ((b_1 - b_2) ** 2))
