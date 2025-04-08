# coding: utf-8

import os
import pydicom
import numpy as np
from PIL import Image, ImageTk, ImageOps
import tkinter as tk
from tkinter import filedialog, messagebox


class DICOMViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("DICOM Viewer v 1.4.1")

        self.current_index = 0
        self.dicom_files = []
        self.images = []
        self.thumbnails = []
        self.metadata_list = []

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        self.btn_open_dir = tk.Button(self.root, text="Открыть директорию", command=self.open_directory)

        self.image_frame = tk.Frame(self.root)
        self.canvas = tk.Canvas(self.image_frame, width=512, height=512)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW)

        self.metadata_frame = tk.Frame(self.image_frame, width=150, height=512)
        self.metadata_text = tk.Text(self.metadata_frame, wrap=tk.WORD, state=tk.DISABLED, width=20)
        self.metadata_scroll = tk.Scrollbar(self.metadata_frame)

        self.btn_prev = tk.Button(self.root, text="Назад", command=self.prev_image)
        self.btn_next = tk.Button(self.root, text="Вперед", command=self.next_image)

        self.thumbnail_frame = tk.Frame(self.root)
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, width=200, height=512)
        self.scrollbar = tk.Scrollbar(self.thumbnail_frame, orient="vertical", command=self.thumbnail_canvas.yview)
        self.scrollable_frame = tk.Frame(self.thumbnail_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.thumbnail_canvas.configure(
                scrollregion=self.thumbnail_canvas.bbox("all")
            )
        )

        self.thumbnail_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.thumbnail_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Добавляем обработчик колесика мыши
        self.thumbnail_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Обработчик прокрутки колесиком мыши"""
        self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def setup_layout(self):
        self.btn_open_dir.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.image_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.metadata_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        self.metadata_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.metadata_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.metadata_text.config(yscrollcommand=self.metadata_scroll.set)
        self.metadata_scroll.config(command=self.metadata_text.yview)

        self.btn_prev.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.btn_next.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.thumbnail_frame.grid(row=0, column=2, rowspan=3, padx=5, pady=5, sticky="ns")
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def open_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dicom_files = []
            self.images = []
            self.thumbnails = []
            self.metadata_list = []

            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            self.find_dicom_files(dir_path)

            if not self.dicom_files:
                messagebox.showwarning("Ошибка", "Не найдено DICOM файлов в директории")
                return

            self.create_thumbnails()
            self.show_image(0)

    def find_dicom_files(self, start_dir):
        checked_files = {}

        for root_dir, _, files in os.walk(start_dir):
            for file in files:
                file_path = os.path.join(root_dir, file)
                file_key = (os.path.getsize(file_path), file)

                if file_key not in checked_files:
                    checked_files[file_key] = self.is_valid_dicom(file_path)

                if checked_files[file_key]:
                    self.dicom_files.append(file_path)

    def is_valid_dicom(self, file_path):
        try:
            pydicom.dcmread(file_path, stop_before_pixels=True)
            return True
        except:
            return False

    def create_thumbnails(self):
        for i, file_path in enumerate(self.dicom_files):
            try:
                dicom_data = pydicom.dcmread(file_path)
                pixel_array = dicom_data.pixel_array

                processed_array = self.preprocess_image(pixel_array, dicom_data)
                img = Image.fromarray(processed_array).convert('RGB')
                img = ImageOps.autocontrast(img, cutoff=2)

                thumbnail = img.resize((64, 64), Image.LANCZOS)
                tk_thumbnail = ImageTk.PhotoImage(thumbnail)

                self.create_thumbnail_button(i, tk_thumbnail)

                self.thumbnails.append(tk_thumbnail)
                self.images.append(img)
                self.metadata_list.append(self.extract_metadata(dicom_data))

            except Exception as e:
                print(f"Ошибка обработки файла {file_path}: {str(e)}")
                continue

    def preprocess_image(self, pixel_array, dicom_data):
        if hasattr(dicom_data, 'WindowWidth') and hasattr(dicom_data, 'WindowCenter'):
            window_width = float(dicom_data.WindowWidth)
            window_center = float(dicom_data.WindowCenter)
            return self.apply_window_level(pixel_array, window_width, window_center)
        else:
            return self.auto_contrast(pixel_array)

    def create_thumbnail_button(self, index, thumbnail):
        btn = tk.Button(self.scrollable_frame, image=thumbnail,
                        command=lambda idx=index: self.show_image(idx))
        btn.image = thumbnail
        btn.pack(padx=2, pady=2)

    def extract_metadata(self, dicom_data):
        return {
            'PatientName': str(getattr(dicom_data, 'PatientName', 'Не указано')),
            'StudyDescription': str(getattr(dicom_data, 'StudyDescription', 'Не указано')),
            'SeriesDescription': str(getattr(dicom_data, 'SeriesDescription', 'Не указано')),
            'StudyDate': str(getattr(dicom_data, 'StudyDate', 'Не указано')),
            'Modality': str(getattr(dicom_data, 'Modality', 'Не указано'))
        }

    def get_enhanced_dicom_image(self, dicom_data):
        pixel_array = dicom_data.pixel_array
        processed_array = self.preprocess_image(pixel_array, dicom_data)
        return Image.fromarray(processed_array).convert('RGB')

    def apply_window_level(self, pixel_array, window_width, window_center):
        min_val = window_center - window_width / 2
        max_val = window_center + window_width / 2

        pixel_array = np.clip(pixel_array, min_val, max_val)
        return ((pixel_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)

    def auto_contrast(self, pixel_array):
        vmin, vmax = np.percentile(pixel_array, (2, 98))
        pixel_array = np.clip(pixel_array, vmin, vmax)
        return ((pixel_array - vmin) / (vmax - vmin) * 255).astype(np.uint8)

    def display_image(self, img):
        tk_img = ImageTk.PhotoImage(img)
        self.canvas.itemconfig(self.image_on_canvas, image=tk_img)
        self.canvas.image = tk_img

        self.update_metadata(self.current_index)
        self.update_navigation_buttons()

    def update_metadata(self, index):
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)

        if 0 <= index < len(self.metadata_list):
            meta = self.metadata_list[index]
            text = (f"Имя пациента: {meta['PatientName']}\n\n"
                    f"Описание исследования: {meta['StudyDescription']}\n\n"
                    f"Описание серии: {meta['SeriesDescription']}\n\n"
                    f"Дата исследования: {meta['StudyDate']}\n\n"
                    f"Модальность: {meta['Modality']}")

            self.metadata_text.insert(tk.END, text)

        self.metadata_text.config(state=tk.DISABLED)

    def show_image(self, index):
        if 0 <= index < len(self.images):
            self.current_index = index
            self.display_image(self.images[index])

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image(self.current_index)

    def next_image(self):
        if self.current_index < len(self.dicom_files) - 1:
            self.current_index += 1
            self.show_image(self.current_index)

    def update_navigation_buttons(self):
        self.btn_prev.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_index < len(self.dicom_files) - 1 else tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = DICOMViewer(root)
    root.mainloop()
