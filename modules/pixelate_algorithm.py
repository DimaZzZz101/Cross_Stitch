#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
from PIL import Image
from modules.DMC import DMC
from modules.TO_SVG import TO_SVG

BLOCK_SIZE = 10
FILTRATION_PARAM = 9


class PixelateAlgorithm:
    def __init__(self):
        self.WIDTH = None
        self.filename = ""  # Название файла (путь к файлу).
        self.colours_count = 0  # Количество цветов.
        self.crosses_count = 0  # Количество крестов в ширину.

        self.original_picture = None  # Первоначальная картинка.
        self.dmc = None  # Словарь с цветами DMC.

        self.svg_pattern = None
        self.svg_palette = None

        self.coloured_no_icons = TO_SVG(True, True, False)
        self.coloured_with_icons = TO_SVG(True, True, True)
        self.black_white = TO_SVG(False, True, True)
        self.key_map = TO_SVG(True, True, True)

    def __call__(self, input_filename, input_colours, input_crosses, producer):
        self.WIDTH = int(input_crosses) * 5
        self.dmc = DMC(producer)
        self.filename = input_filename
        self.colours_count = int(input_colours)
        self.crosses_count = int(input_crosses)

        # Проверка открытия исходного изображения.
        try:
            self.original_picture = cv2.imread(self.filename)
        except FileNotFoundError:
            print(f"File {self.filename} not found.")

        PixelateAlgorithm.do_filter(self)

        # Вычисление размера нового пикселя.
        pixel_size = int(self.WIDTH / int(self.crosses_count))

        # Изменения размера картинки с сохранением пропорций.
        PixelateAlgorithm.resize(self)

        # Квантование картинки с заданным размером нового пикселя
        # (с вычислением цвета из палитры DMC для каждого пикселя).
        dmc_image, x_count, y_count = PixelateAlgorithm.do_quantization(self, pixel_size)

        # Получение цветовой палитры картинки после квантования.
        palette = dmc_image.getpalette()

        # Сохраним картинку после квантования в переменную svg_pattern.
        self.svg_pattern = [[dmc_image.getpixel((x, y)) for x in range(x_count)] for y in range(y_count)]

        # Создание svg-палитры с заданным количеством цветов:
        # берем по три составляющие цвета из палитры паттерна (r, g, b соответственно).
        self.svg_palette = [self.dmc.get_dmc_code((palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2])) for i in
                            range(self.colours_count)]

        # Выполнение проверки на наличие изолированных пикселей.
        PixelateAlgorithm.check_pattern(self, x_count, y_count)

        width = x_count * BLOCK_SIZE  # Ширина итогового паттерна.
        height = y_count * BLOCK_SIZE  # Высота итогового паттерна.

        # Создание паттернов в трех вариациях:
        #   1) Цветной без обозначений;
        #   2) Цветной с обозначений;
        #   3) Черно-белый (с обозначениями по умолчанию);
        PixelateAlgorithm.create_patterns(self, width, height)

        # Окрашивание паттернов в соответствии с вариацией.
        PixelateAlgorithm.colour_pattern(self, x=BLOCK_SIZE, y=BLOCK_SIZE, block_size=BLOCK_SIZE)

        # Создание сетки для паттернов (чтобы ориентироваться).
        PixelateAlgorithm.add_grid_on_pattern(self, width, height, block_size=BLOCK_SIZE)

        # Создание ключа для вышивки.
        PixelateAlgorithm.create_key_map(self, size=40, x=0, y=0)

        # Сохранение паттернов и ключа.
        PixelateAlgorithm.save_patterns(self)
        PixelateAlgorithm.save_key(self)

    def do_filter(self):
        """
        Данный метод проводит предварительную фильтрацию изображения.
        Сначала, так как цветовая схема BGR, изображение приводится к классическому RGB.
        Затем изображение проходит фильтрацию (используется билатеральный фильтр), на нем устраняются шумы и другие
        дефекты, в частности т. н. "salt and pepper".
        """
        self.original_picture = cv2.cvtColor(self.original_picture, cv2.COLOR_BGR2RGB)
        filtered_median = Image.fromarray(cv2.bilateralFilter(self.original_picture, FILTRATION_PARAM, 75, 75))
        self.original_picture = filtered_median

    def resize(self):
        """
        Данный метод задает новые размеры изображения, необходимые для последующей обработки, с сохранением пропорций.
        """

        new_height = int(self.WIDTH * self.original_picture.size[1] / self.original_picture.size[0])
        self.original_picture = self.original_picture.resize((self.WIDTH, new_height), Image.ANTIALIAS)

    def do_quantization(self, pixel_size):
        """
        Данный метод выполняет квантование цвета изображения.
        Сначала получаем матрицу цветов: цвет каждого пикселя раскладывается на три составляющие RGB.
        Затем создается новое изображение с размерами предыдущего.
        После этого изображение окрашивается таким образом, что на выходе получится заданное количество цветов с
        сохранением исходной палитры.

        :param pixel_size: Размер нового пикселя.
        :return: dmc_image: Изображение после квантования.
                 x_count: Ширина нового изображения.
                 y_count: Высота нового изображения.
        """

        dmc_colour_matrix = [
            [self.dmc.get_dmc_rgb(self.original_picture.getpixel((x, y)))
             for x in range(0, self.original_picture.size[0], pixel_size)]
            for y in range(0, self.original_picture.size[1], pixel_size)]
        dmc_image = Image.new('RGB', (len(dmc_colour_matrix[0]), len(dmc_colour_matrix)))
        dmc_image.putdata([value for row in dmc_colour_matrix for value in row])
        dmc_image = dmc_image.convert('P', palette=Image.ADAPTIVE, colors=self.colours_count)

        x_count = dmc_image.size[0]
        y_count = dmc_image.size[1]

        return dmc_image, x_count, y_count

    def colour_pattern(self, x, y, block_size):
        """
        Данный метод создает паттерны для вышивки.

        :param x: Ширина паттерна.
        :param y: Высота паттерна.
        :param block_size: размер "пикселя паттерна".
        """

        for row in self.svg_pattern:
            for index in row:
                self.coloured_no_icons.add_pixel(self.svg_palette, index, x, y, block_size)
                self.coloured_with_icons.add_pixel(self.svg_palette, index, x, y, block_size)
                self.black_white.add_pixel(self.svg_palette, index, x, y, block_size)
                x += block_size
            y += block_size
            x = block_size

    def check_pattern(self, x_count, y_count):
        """
        Проверка полученного паттерна на необработанные пиксели (методом поиска соседей в матрице).

        :param x_count: Ширина паттерна.
        :param y_count: Высота паттерна.
        """

        if True:
            for x in range(0, x_count):
                for y in range(0, y_count):
                    gen = PixelateAlgorithm.get_matrix_neighbours((y, x), self.svg_pattern)
                    neighbours = []
                    for n in gen:
                        neighbours.append(n)
                    if self.svg_pattern[y][x] not in neighbours:
                        mode = max(neighbours, key=neighbours.count)
                        self.svg_pattern[y][x] = mode

    def create_patterns(self, width, height):
        """
        Данный метод определяет общие параметры паттерна.
        Если быть точнее, то задаются общие заголовки для svg-файлов (изображений).
        Также наносятся центрирующие стрелки (для позиционирования при вышивке).

        :param width: Ширина паттерна.
        :param height: Высота паттерна.
        """

        self.coloured_no_icons.start_svg(width, height)
        self.coloured_no_icons.add_center_arrows(BLOCK_SIZE, width, height)

        self.coloured_with_icons.start_svg(width, height)
        self.coloured_with_icons.add_center_arrows(BLOCK_SIZE, width, height)

        self.black_white.start_svg(width, height)
        self.black_white.add_center_arrows(BLOCK_SIZE, width, height)

    def create_key_map(self, size, x, y):
        """
        Данный метод нужен для генерации ключа для вышивки.
        Каждому цвету соответствует свой символ, название и код цвета.

        :param size: Размер ячейки таблицы.
        :param x: Координата x для позиционирования отрисовки.
        :param y: Координата y для позиционирования отрисовки.
        """

        self.key_map.start_svg(size * 13, size * len(self.svg_palette))

        for i in range(len(self.svg_palette)):
            self.key_map.create_key(x, y, size, i, self.svg_palette[i])
            y += size

    def add_grid_on_pattern(self, width, height, block_size):
        """
        Данный метод требуется для нанесения сетки на паттерн, которая нужна для ориентира при вышивке.

        :param width: Ширина паттерна.
        :param height: Высота паттерна.
        :param block_size: Размер "пикселя" паттерна.
        """
        self.coloured_no_icons.add_grid(width, height, block_size)
        self.coloured_with_icons.add_grid(width, height, block_size)
        self.black_white.add_grid(width, height, block_size)

    def save_patterns(self):
        """
        Данный метод сохраняет полученные паттерны в директории с названием исходного изображения.
        """

        name = PixelateAlgorithm.cut_extension(self)

        self.coloured_no_icons.save(f'patterns/{name}/{name}_no_icons.svg')
        self.coloured_with_icons.save(f'patterns/{name}/{name}_with_icons.svg')
        self.black_white.save(f'patterns/{name}/{name}_black_and_white.svg')

    def save_key(self):
        """
        Данный метод сохраняет ключ в директории с названием исходного изображения.
        Метод сделан отдельным, поскольку ключ не является паттерном.
        """

        name = PixelateAlgorithm.cut_extension(self)
        self.key_map.save(f'patterns/{name}/key_for_pattern.svg')

    def cut_extension(self):
        """
        Данный метод используется для выделения имени файла без расширения.
        """

        name = str(os.path.basename(self.filename))

        if '.jpeg' in name:
            name = name.rstrip('.jpeg')
        elif '.JPEG' in name:
            name = name.rstrip('.JPEG')
        elif '.jpg' in name:
            name = name.rstrip('.jpg')
        elif '.JPG' in name:
            name = name.rstrip('.JPG')

        return name

    @staticmethod
    def get_matrix_neighbours(pos, matrix):
        """
        Данная функция используется для поиска соседей в матрице, это, в свою очередь, нужно для выявления
        изолированных пикселей.

        :param pos: Позиция пикселя, его координаты (x; y).
        :param matrix: Паттерн.
        """

        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        step_size = 1
        for i in range(max(0, pos[0] - step_size), min(rows, pos[0] + step_size + 1)):
            for j in range(max(0, pos[1] - step_size), min(cols, pos[1] + step_size + 1)):
                if not (i == pos[0] and j == pos[1]):
                    yield matrix[i][j]
