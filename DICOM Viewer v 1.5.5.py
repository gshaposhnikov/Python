import os
import sys
import threading
import traceback
from functools import partial
from collections import OrderedDict

import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

LANGUAGES = {
    'en': {
        'open_directory': 'Open Directory',
        'prev': 'Prev',
        'next': 'Next',
        'save_image': 'Save Image',
        'no_files_found': 'No DICOM files found in the selected directory.',
        'error': 'Error',
        'file_error': 'Failed to load file: {}',
        'window_level': 'Window Level',
        'window_width': 'Window Width',
        'select_language': 'Select Language',
        'metadata': 'Metadata',
        'loading': 'Loading...',
        'zoom_in': 'Zoom In',
        'zoom_out': 'Zoom Out',
        'reset_zoom': 'Reset Zoom',
        'pan_instructions': 'Use mouse wheel to zoom, drag to pan.',
    },
    'ru': {
        'open_directory': 'Открыть папку',
        'prev': 'Назад',
        'next': 'Вперед',
        'save_image': 'Сохранить изображение',
        'no_files_found': 'DICOM-файлы в выбранной папке не найдены.',
        'error': 'Ошибка',
        'file_error': 'Не удалось загрузить файл: {}',
        'window_level': 'Уровень окна',
        'window_width': 'Ширина окна',
        'select_language': 'Выберите язык',
        'metadata': 'Метаданные',
        'loading': 'Загрузка...',
        'zoom_in': 'Увеличить',
        'zoom_out': 'Уменьшить',
        'reset_zoom': 'Сбросить масштаб',
        'pan_instructions': 'Колесо мыши — масштаб, перетаскивание — панорамирование.',
    }
}

class DICOMViewer(tk.Tk):
    THUMBNAIL_SIZE = (64, 64)
    MAIN_IMAGE_SIZE = (512, 512)
    ZOOM_STEP = 1.2
    MAX_ZOOM = 10
    MIN_ZOOM = 0.2

    def __init__(self):
        super().__init__()
        self.title("DICOM Viewer v1.5.5")
        self.geometry("1200x700")
        self.minsize(900, 600)

        self.lang_code = 'ru'
        self.lang = LANGUAGES[self.lang_code]

        self.dicom_files = []
        self.dicom_datasets = []
        self.thumbnails = []
        self.current_index = 0

        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._drag_data = {"x": 0, "y": 0}

        self.create_widgets()
        self.setup_layout()
        self.bind_events()

    def create_widgets(self):
        self.top_frame = ttk.Frame(self)
        self.btn_open = ttk.Button(self.top_frame, text=self.lang['open_directory'], command=self.open_directory)
        self.btn_prev = ttk.Button(self.top_frame, text=self.lang['prev'], command=self.prev_image, state=tk.DISABLED)
        self.btn_next = ttk.Button(self.top_frame, text=self.lang['next'], command=self.next_image, state=tk.DISABLED)
        self.btn_save = ttk.Button(self.top_frame, text=self.lang['save_image'], command=self.save_image, state=tk.DISABLED)

        self.btn_zoom_in = ttk.Button(self.top_frame, text=self.lang['zoom_in'], command=self.zoom_in, state=tk.DISABLED)
        self.btn_zoom_out = ttk.Button(self.top_frame, text=self.lang['zoom_out'], command=self.zoom_out, state=tk.DISABLED)
        self.btn_reset_zoom = ttk.Button(self.top_frame, text=self.lang['reset_zoom'], command=self.reset_zoom, state=tk.DISABLED)

        self.lang_var = tk.StringVar(value=self.lang_code)
        self.lang_menu = ttk.OptionMenu(self.top_frame, self.lang_var, self.lang_code, *LANGUAGES.keys(), command=self.change_language)

        self.main_frame = ttk.Frame(self)

        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas = tk.Canvas(self.canvas_frame, width=self.MAIN_IMAGE_SIZE[0], height=self.MAIN_IMAGE_SIZE[1], bg='black')
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.metadata_frame = ttk.LabelFrame(self.main_frame, text=self.lang['metadata'])
        self.text_metadata = tk.Text(self.metadata_frame, width=40, height=30, wrap=tk.NONE)
        self.scroll_metadata_y = ttk.Scrollbar(self.metadata_frame, orient=tk.VERTICAL, command=self.text_metadata.yview)
        self.scroll_metadata_x = ttk.Scrollbar(self.metadata_frame, orient=tk.HORIZONTAL, command=self.text_metadata.xview)
        self.text_metadata.configure(yscrollcommand=self.scroll_metadata_y.set, xscrollcommand=self.scroll_metadata_x.set, state=tk.DISABLED)

        self.thumb_frame = ttk.LabelFrame(self, text="Thumbnails")
        self.thumb_canvas = tk.Canvas(self.thumb_frame, width=self.THUMBNAIL_SIZE[0] + 20)
        self.thumb_scrollbar = ttk.Scrollbar(self.thumb_frame, orient=tk.VERTICAL, command=self.thumb_canvas.yview)
        self.thumb_canvas.configure(yscrollcommand=self.thumb_scrollbar.set)
        self.thumb_inner_frame = ttk.Frame(self.thumb_canvas)

        self.thumb_canvas.create_window((0, 0), window=self.thumb_inner_frame, anchor='nw')

        self.status_bar = ttk.Label(self, text=self.lang['pan_instructions'], relief=tk.SUNKEN, anchor=tk.W)

    def setup_layout(self):
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.btn_open.pack(side=tk.LEFT, padx=3)
        self.btn_prev.pack(side=tk.LEFT, padx=3)
        self.btn_next.pack(side=tk.LEFT, padx=3)
        self.btn_save.pack(side=tk.LEFT, padx=3)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=3)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=3)
        self.btn_reset_zoom.pack(side=tk.LEFT, padx=3)
        ttk.Label(self.top_frame, text=self.lang['select_language'] + ":").pack(side=tk.LEFT, padx=10)
        self.lang_menu.pack(side=tk.LEFT)

        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.hbar.grid(row=1, column=0, sticky='ew')
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        self.metadata_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.text_metadata.grid(row=0, column=0, sticky='nsew')
        self.scroll_metadata_y.grid(row=0, column=1, sticky='ns')
        self.scroll_metadata_x.grid(row=1, column=0, sticky='ew')
        self.metadata_frame.rowconfigure(0, weight=1)
        self.metadata_frame.columnconfigure(0, weight=1)

        self.thumb_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.thumb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.thumb_inner_frame.bind("<Configure>", self.on_thumb_frame_configure)

    def bind_events(self):
        self.thumb_canvas.bind_all("<MouseWheel>", self.on_mousewheel_thumb)
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_button_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_button_release)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel_canvas)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def on_thumb_frame_configure(self, event):
        self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))

    def on_mousewheel_thumb(self, event):
        if event.widget == self.thumb_canvas or event.widget.master == self.thumb_inner_frame:
            self.thumb_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def on_mousewheel_canvas(self, event):
        if self.dicom_files:
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def on_canvas_button_press(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_canvas_move_press(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_canvas_button_release(self, event):
        pass

    def on_canvas_configure(self, event):
        if self.dicom_files:
            self.display_image(self.current_index)

    def change_language(self, lang_code):
        if lang_code not in LANGUAGES:
            return
        self.lang_code = lang_code
        self.lang = LANGUAGES[lang_code]
        self.update_ui_texts()

    def update_ui_texts(self):
        self.btn_open.config(text=self.lang['open_directory'])
        self.btn_prev.config(text=self.lang['prev'])
        self.btn_next.config(text=self.lang['next'])
        self.btn_save.config(text=self.lang['save_image'])
        self.btn_zoom_in.config(text=self.lang['zoom_in'])
        self.btn_zoom_out.config(text=self.lang['zoom_out'])
        self.btn_reset_zoom.config(text=self.lang['reset_zoom'])
        self.metadata_frame.config(text=self.lang['metadata'])
        self.status_bar.config(text=self.lang['pan_instructions'])
        self.lang_menu['menu'].delete(0, 'end')
        for code in LANGUAGES.keys():
            self.lang_menu['menu'].add_command(label=code, command=lambda c=code: self.lang_var.set(c) or self.change_language(c))

    def open_directory(self):
        directory = filedialog.askdirectory()
        if not directory:
            return
        self.reset_viewer()
        self.status_bar.config(text=self.lang['loading'])
        self.update()
        threading.Thread(target=self.load_dicom_files, args=(directory,), daemon=True).start()

    def reset_viewer(self):
        self.dicom_files.clear()
        self.dicom_datasets.clear()
        self.thumbnails.clear()
        self.current_index = 0
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self.clear_thumbnails()
        self.text_metadata.config(state=tk.NORMAL)
        self.text_metadata.delete("1.0", tk.END)
        self.text_metadata.config(state=tk.DISABLED)
        self.canvas.delete("all")
        self.btn_prev.config(state=tk.DISABLED)
        self.btn_next.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.btn_zoom_in.config(state=tk.DISABLED)
        self.btn_zoom_out.config(state=tk.DISABLED)
        self.btn_reset_zoom.config(state=tk.DISABLED)

    def load_dicom_files(self, directory):
        try:
            files = self.find_dicom_files(directory)
            if not files:
                self.after(0, lambda: messagebox.showinfo(self.lang['error'], self.lang['no_files_found']))
                self.after(0, lambda: self.status_bar.config(text=''))
                return
            self.dicom_files = sorted(files)
            self.dicom_datasets = [None] * len(self.dicom_files)
            self.after(0, self.create_thumbnails)
        except Exception as e:
            traceback.print_exc()
            self.after(0, lambda: messagebox.showerror(self.lang['error'], str(e)))
            self.after(0, lambda: self.status_bar.config(text=''))

    def find_dicom_files(self, directory):
        dicom_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if self.is_valid_dicom(filepath):
                    dicom_files.append(filepath)
        return dicom_files

    def is_valid_dicom(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                preamble = f.read(132)
                return preamble[128:132] == b'DICM'
        except Exception:
            return False

    def create_thumbnails(self):
        self.clear_thumbnails()
        for idx, filepath in enumerate(self.dicom_files):
            ds = self.load_dataset(idx)
            if ds is None:
                thumb_img = Image.new('L', self.THUMBNAIL_SIZE, color=128)
            else:
                thumb_img = self.get_pil_image(ds, thumbnail=True)
            thumb_photo = ImageTk.PhotoImage(thumb_img)
            btn = ttk.Button(self.thumb_inner_frame, image=thumb_photo)
            btn.image = thumb_photo
            btn.grid(row=idx, column=0, pady=2, padx=2)
            btn.config(command=partial(self.select_image, idx))
            self.thumbnails.append({'button': btn, 'image': thumb_photo})

        self.select_image(0)
        self.status_bar.config(text='')

    def clear_thumbnails(self):
        for thumb in self.thumbnails:
            thumb['button'].destroy()
        self.thumbnails.clear()

    def load_dataset(self, index):
        if self.dicom_datasets[index] is not None:
            return self.dicom_datasets[index]
        try:
            ds = pydicom.dcmread(self.dicom_files[index])
            self.dicom_datasets[index] = ds
            return ds
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(self.lang['error'], self.lang['file_error'].format(self.dicom_files[index])))
            return None

    def select_image(self, index):
        if index < 0 or index >= len(self.dicom_files):
            return
        self.current_index = index
        ds = self.load_dataset(index)
        if ds is None:
            return

        self.highlight_thumbnail(index)
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_image(index)
        self.display_metadata(ds)
        self.update_navigation_buttons()
        self.update_zoom_buttons()
        self.btn_save.config(state=tk.NORMAL)

    def highlight_thumbnail(self, index):
        for i, thumb in enumerate(self.thumbnails):
            if i == index:
                thumb['button'].state(['pressed'])
            else:
                thumb['button'].state(['!pressed'])

    def display_image(self, index):
        ds = self.load_dataset(index)
        if ds is None:
            return
        pil_img = self.get_pil_image(ds, thumbnail=False)
        w, h = pil_img.size
        new_w = int(w * self.zoom_factor)
        new_h = int(h * self.zoom_factor)
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

        self.current_pil_image = pil_img

        self.photo_image = ImageTk.PhotoImage(pil_img)
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo_image)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = max((canvas_width - new_w) // 2, 0)
        y = max((canvas_height - new_h) // 2, 0)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.canvas.move("all", x, y)

    def display_metadata(self, ds):
        self.text_metadata.config(state=tk.NORMAL)
        self.text_metadata.delete("1.0", tk.END)

        def format_value(val):
            if isinstance(val, bytes):
                try:
                    return val.decode('utf-8', errors='ignore')
                except Exception:
                    return str(val)
            return str(val)

        info = OrderedDict()
        info['Patient Name'] = getattr(ds, 'PatientName', 'N/A')
        info['Patient ID'] = getattr(ds, 'PatientID', 'N/A')
        info['Patient Birth Date'] = getattr(ds, 'PatientBirthDate', 'N/A')
        info['Study Date'] = getattr(ds, 'StudyDate', 'N/A')
        info['Study Description'] = getattr(ds, 'StudyDescription', 'N/A')
        info['Series Description'] = getattr(ds, 'SeriesDescription', 'N/A')
        info['Modality'] = getattr(ds, 'Modality', 'N/A')
        info['Manufacturer'] = getattr(ds, 'Manufacturer', 'N/A')
        info['Institution Name'] = getattr(ds, 'InstitutionName', 'N/A')
        info['Body Part Examined'] = getattr(ds, 'BodyPartExamined', 'N/A')
        info['Window Center(s)'] = getattr(ds, 'WindowCenter', 'N/A')
        info['Window Width(s)'] = getattr(ds, 'WindowWidth', 'N/A')

        for key, val in info.items():
            self.text_metadata.insert(tk.END, f"{key}: {format_value(val)}\n")

        self.text_metadata.config(state=tk.DISABLED)

    def update_navigation_buttons(self):
        self.btn_prev.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_index < len(self.dicom_files) - 1 else tk.DISABLED)

    def update_zoom_buttons(self):
        self.btn_zoom_in.config(state=tk.NORMAL if self.zoom_factor < self.MAX_ZOOM else tk.DISABLED)
        self.btn_zoom_out.config(state=tk.NORMAL if self.zoom_factor > self.MIN_ZOOM else tk.DISABLED)
        self.btn_reset_zoom.config(state=tk.NORMAL if self.zoom_factor != 1.0 else tk.DISABLED)

    def prev_image(self):
        if self.current_index > 0:
            self.select_image(self.current_index - 1)

    def next_image(self):
        if self.current_index < len(self.dicom_files) - 1:
            self.select_image(self.current_index + 1)

    def save_image(self):
        if not hasattr(self, 'current_pil_image'):
            return
        filetypes = [('PNG Image', '*.png'), ('JPEG Image', '*.jpg'), ('BMP Image', '*.bmp')]
        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)
        if filename:
            try:
                self.current_pil_image.save(filename)
                messagebox.showinfo("Info", f"Image saved to {filename}")
            except Exception as e:
                messagebox.showerror(self.lang['error'], str(e))

    def zoom_in(self):
        if self.zoom_factor * self.ZOOM_STEP <= self.MAX_ZOOM:
            self.zoom_factor *= self.ZOOM_STEP
            self.display_image(self.current_index)
            self.update_zoom_buttons()

    def zoom_out(self):
        if self.zoom_factor / self.ZOOM_STEP >= self.MIN_ZOOM:
            self.zoom_factor /= self.ZOOM_STEP
            self.display_image(self.current_index)
            self.update_zoom_buttons()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.display_image(self.current_index)
        self.update_zoom_buttons()

    def get_pil_image(self, ds, thumbnail=False):
        try:
            arr = apply_voi_lut(ds.pixel_array, ds, force=True)
        except Exception:
            arr = ds.pixel_array

        arr = self.normalize_to_uint8(arr)

        img = Image.fromarray(arr).convert('L')

        if thumbnail:
            img.thumbnail(self.THUMBNAIL_SIZE, Image.LANCZOS)

        return img

    def normalize_to_uint8(self, arr):
        arr = arr.astype(np.float32)
        min_val = np.min(arr)
        max_val = np.max(arr)
        if max_val > min_val:
            arr = (arr - min_val) / (max_val - min_val) * 255.0
        else:
            arr = np.zeros(arr.shape, dtype=np.float32)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return arr

if __name__ == "__main__":
    app = DICOMViewer()
    app.mainloop()
