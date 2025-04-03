import pydicom
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import os

class DicomViewer:
    def __init__(self, master):
        self.master = master
        master.title("DICOM Viewer v1.2")

        # Увеличиваем размер и размещаем кнопки вверху
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=10)  # Добавляем отступ снизу

        self.open_button = tk.Button(self.button_frame, text="Открыть файл", width=20, command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5) # Добавляем отступ между кнопками

        self.open_directory_button = tk.Button(self.button_frame, text="Открыть директорию", width=20, command=self.open_directory)
        self.open_directory_button.pack(side=tk.LEFT, padx=5) # Добавляем отступ между кнопками

        self.navigation_frame = tk.Frame(master)
        self.navigation_frame.pack(pady=5)

        self.prev_button = tk.Button(self.navigation_frame, text="Назад", width=10, command=self.show_previous)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.prev_button["state"] = "disabled"  # Initially disabled

        self.next_button = tk.Button(self.navigation_frame, text="Вперед", width=10, command=self.show_next)
        self.next_button.pack(side=tk.LEFT, padx=5)
        self.next_button["state"] = "disabled" # Initially disabled

        self.image_label = tk.Label(master)
        self.image_label.pack(expand=True, fill=tk.BOTH)  # Растягиваем по всему окну

        self.dicom_dataset = None
        self.image = None
        self.photo = None
        self.files_in_directory = []  # Список всех файлов в выбранной директории
        self.current_index = -1  # Индекс текущего отображаемого файла



    def open_file(self):
        filepath = filedialog.askopenfilename(
            initialdir=".",
            title="Выбрать файл",
            filetypes=(("Все файлы", "*.*"),)  # Открываем все типы файлов
        )

        if filepath:
            self.load_and_display(filepath)

    def open_directory(self):
        directory = filedialog.askdirectory(
            initialdir=".",
            title="Выбрать директорию с файлами"
        )

        if directory:
            self.files_in_directory = []
            for root, _, files in os.walk(directory): # os.walk проходит по всем поддиректориям
                for file in files:
                    full_path = os.path.join(root, file)
                    self.files_in_directory.append(full_path)


            if self.files_in_directory:
                self.current_index = 0
                self.load_and_display(self.files_in_directory[0])
                self.update_navigation_buttons()  # Enable/disable buttons
            else:
                messagebox.showinfo("Информация", "В выбранной директории нет файлов.")
                self.reset_navigation() # Reset state

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_and_display(self.files_in_directory[self.current_index])
            self.update_navigation_buttons()

    def show_next(self):
        if self.current_index < len(self.files_in_directory) - 1:
            self.current_index += 1
            self.load_and_display(self.files_in_directory[self.current_index])
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Enables or disables the navigation buttons based on current index."""
        self.prev_button["state"] = "normal" if self.current_index > 0 else "disabled"
        self.next_button["state"] = "normal" if self.current_index < len(self.files_in_directory) - 1 else "disabled"

    def reset_navigation(self):
        """Resets the navigation state."""
        self.current_index = -1
        self.files_in_directory = []
        self.prev_button["state"] = "disabled"
        self.next_button["state"] = "disabled"

    def load_and_display(self, filepath):
        try:
            try:
                # Пытаемся прочитать как DICOM
                self.dicom_dataset = pydicom.dcmread(filepath)
                self.display_dicom_image() # Отображаем как DICOM
            except pydicom.errors.InvalidDicomError:
                # Если не DICOM, пытаемся открыть как изображение
                try:
                    self.image = Image.open(filepath)
                    self.display_image() # Отображаем как обычное изображение
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть файл как DICOM или изображение: {e}")
                    self.image_label.config(text=f"Не удалось открыть файл: {e}")
                    self.reset_navigation() # Reset Navigation
        except Exception as e:
             messagebox.showerror("Ошибка", f"Общая ошибка при загрузке файла: {e}")
             self.image_label.config(text=f"Ошибка при загрузке файла: {e}")
             self.reset_navigation() # Reset navigation.

    def display_dicom_image(self):
        if self.dicom_dataset is None:
            return

        try:
            # Получить массив пикселей из DICOM набора данных
            pixel_array = self.dicom_dataset.pixel_array

            # Обработка различных типов данных и масштабирование
            if 'RescaleIntercept' in self.dicom_dataset and 'RescaleSlope' in self.dicom_dataset:
                intercept = self.dicom_dataset.RescaleIntercept
                slope = self.dicom_dataset.RescaleSlope
                pixel_array = pixel_array * slope + intercept

            # Нормализация данных пикселей к диапазону 0-255 для отображения
            if pixel_array.dtype != np.uint8:
                pixel_array = self.normalize_pixel_array(pixel_array)

            # Преобразование numpy массива в PIL Image
            self.image = Image.fromarray(pixel_array)
            self.display_image() # Используем общую функцию для отображения
            # Отображение некоторых метаданных DICOM (необязательно)
            metadata_string = f"Имя пациента: {self.dicom_dataset.PatientName}\n"
            metadata_string += f"Описание исследования: {self.dicom_dataset.StudyDescription}\n"
            metadata_string += f"Описание серии: {self.dicom_dataset.SeriesDescription}"
            self.image_label.config(text=metadata_string, compound=tk.TOP)

        except Exception as e:
            print(f"Ошибка при отображении DICOM изображения: {e}")
            self.image_label.config(text=f"Ошибка при отображении DICOM изображения: {e}")
            self.reset_navigation()

    def display_image(self):
        """Отображает PIL Image в image_label."""
        if self.image is None:
            return

        try:
            # Изменение размера изображения, если необходимо
            max_width = 800  # Максимальная ширина области отображения
            max_height = 800 # Максимальная высота области отображения
            width, height = self.image.size
            if width > max_width or height > max_height:
                self.image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Преобразование PIL Image в Tkinter PhotoImage
            self.photo = ImageTk.PhotoImage(self.image)

            # Отображение изображения в метке
            self.image_label.config(image=self.photo)
            self.image_label.image = self.photo  # Сохранение ссылки
            self.image_label.config(text="") # Убираем текст, если он есть
        except Exception as e:
            print(f"Ошибка при отображении изображения: {e}")
            self.image_label.config(text=f"Ошибка при отображении изображения: {e}")
            self.reset_navigation() # Reset if image load fails

    def normalize_pixel_array(self, pixel_array):
        """Нормализует данные пикселей к диапазону 0-255."""
        max_value = np.max(pixel_array)
        min_value = np.min(pixel_array)

        if max_value == min_value:
            return np.zeros_like(pixel_array, dtype=np.uint8)  # Обработка случаев, когда все пиксели имеют одинаковое значение

        normalized_array = ((pixel_array - min_value) / (max_value - min_value)) * 255
        return normalized_array.astype(np.uint8)


root = tk.Tk()
# Увеличиваем размер окна
root.geometry("800x800")  # Или любой другой размер
viewer = DicomViewer(root)
root.mainloop()