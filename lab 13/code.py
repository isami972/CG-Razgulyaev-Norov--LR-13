import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct
from math import floor, ceil

class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f})"

class Canvas:
    def __init__(self, width, height, bg_color=(30, 30, 30)):
        self.width = width
        self.height = height
        self.pixels = [bg_color] * (width * height)

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = int(y) * self.width + int(x)
            self.pixels[idx] = color

    def save_ppm(self, filename):
        """Сохранение в формат PPM"""
        with open(filename, 'w') as f:
            f.write(f"P3\n{self.width} {self.height}\n255\n")
            for i in range(self.height):
                for j in range(self.width):
                    idx = i * self.width + j
                    r, g, b = self.pixels[idx]
                    f.write(f"{r} {g} {b} ")
                f.write("\n")
        print(f"Файл {filename} сохранен.")

    def save_bmp(self, filename):
        """Сохранение в формат BMP"""
        w, h = self.width, self.height
        padding = (4 - (w * 3) % 4) % 4
        file_size = 14 + 40 + (3 * w + padding) * h
        bf_type = b'BM'
        bf_off_bits = 54
        
        with open(filename, 'wb') as f:
            f.write(bf_type)
            f.write(struct.pack('<I', file_size))
            f.write(struct.pack('<H', 0)) 
            f.write(struct.pack('<H', 0))
            f.write(struct.pack('<I', bf_off_bits))
            
            f.write(struct.pack('<I', 40))
            f.write(struct.pack('<i', w))
            f.write(struct.pack('<i', -h))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<H', 24))
            f.write(struct.pack('<I', 0))
            f.write(struct.pack('<I', 0))
            f.write(struct.pack('<i', 0))
            f.write(struct.pack('<i', 0))
            f.write(struct.pack('<I', 0))
            f.write(struct.pack('<I', 0))
            
            for y in range(h):
                row_start = y * w
                for x in range(w):
                    r, g, b = self.pixels[row_start + x]
                    f.write(struct.pack('BBB', b, g, r))
                f.write(b'\x00' * padding)
        print(f"Файл {filename} сохранен.")

    def clear(self, bg_color=(30, 30, 30)):
        """Очистка холста"""
        self.pixels = [bg_color] * (self.width * self.height)

def cross_product_z(a, b, c):
    """Векторное произведение (определитель)"""
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

def intersect(p1, p2, cp1, cp2):
    """Нахождение точки пересечения двух отрезков"""
    det = (p1.x - p2.x) * (cp1.y - cp2.y) - (p1.y - p2.y) * (cp1.x - cp2.x)
    
    if det == 0:
        return None 
    
    t = ((p1.x - cp1.x) * (cp1.y - cp2.y) - (p1.y - cp1.y) * (cp1.x - cp2.x)) / det
    
    x = p1.x + t * (p2.x - p1.x)
    y = p1.y + t * (p2.y - p1.y)
    return Point(x, y)

def is_inside(p, cp1, cp2):
    """Проверка, находится ли точка внутри ребра отсекателя"""
    return cross_product_z(cp1, cp2, p) >= 0 

def sutherland_hodgman_clip(subject_polygon, clipper_polygon):
    """Алгоритм Сазерленда-Ходжмана для отсечения многоугольника"""
    output_list = subject_polygon.copy()
    
    for i in range(len(clipper_polygon)):
        input_list = output_list
        output_list = []
        
        if not input_list:
            break

        cp1 = clipper_polygon[i - 1]
        cp2 = clipper_polygon[i]

        for j in range(len(input_list)):
            curr_point = input_list[j]
            prev_point = input_list[j - 1]

            curr_in = is_inside(curr_point, cp1, cp2)
            prev_in = is_inside(prev_point, cp1, cp2)

            if curr_in:
                if not prev_in:
                    inters = intersect(prev_point, curr_point, cp1, cp2)
                    if inters: 
                        output_list.append(inters)
                output_list.append(curr_point)
            elif prev_in:
                inters = intersect(prev_point, curr_point, cp1, cp2)
                if inters: 
                    output_list.append(inters)
                
    return output_list

def bresenham_line(canvas, p1, p2, color):
    """Алгоритм Брезенхема для рисования линии"""
    x1, y1 = int(p1.x), int(p1.y)
    x2, y2 = int(p2.x), int(p2.y)
    
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    while True:
        canvas.set_pixel(x1, y1, color)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

def scanline_fill(canvas, polygon, color):
    """Заливка многоугольника с помощью алгоритма сканирующей строки"""
    if not polygon:
        return

    min_y = int(min(p.y for p in polygon))
    max_y = int(max(p.y for p in polygon))
    min_y = max(0, min_y)
    max_y = min(canvas.height - 1, max_y)

    n = len(polygon)

    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]

            y1_int, y2_int = int(p1.y), int(p2.y)
            if y1_int == y2_int:
                continue
            
            if (y1_int < y <= y2_int) or (y2_int < y <= y1_int):
                if p2.y - p1.y != 0:
                    x = p1.x + (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y)
                    intersections.append(x)
        
        intersections.sort()
        for i in range(0, len(intersections), 2):
            if i + 1 < len(intersections):
                x_start = int(intersections[i])
                x_end = int(intersections[i+1])
                x_start = max(0, x_start)
                x_end = min(canvas.width - 1, x_end)
                
                for x in range(x_start, x_end + 1):
                    canvas.set_pixel(x, y, color)

class PolygonClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Отсечение многоугольников - Сазерленд-Ходжман")
        self.root.geometry("1000x700")
        
        # Инициализация холста
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas_obj = Canvas(self.canvas_width, self.canvas_height)
        
        # Данные многоугольников
        self.subject_polygon = [
            Point(100, 100), Point(400, 50), Point(600, 300), 
            Point(400, 500), Point(100, 400), Point(200, 250)
        ]
        
        self.clipper_polygon = [
            Point(170, 170),
            Point(470, 170),
            Point(470, 470),
            Point(170, 470)
        ]
        
        self.clipped_polygon = []
        
        # Цвета
        self.colors = {
            'background': (30, 30, 30),
            'subject': (255, 50, 50),
            'clipper': (255, 255, 255),
            'clipped_fill': (0, 255, 100),
            'clipped_border': (255, 255, 0)
        }
        
        self.setup_ui()
        self.draw_scene()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Главный фрейм
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель управления
        control_frame = tk.Frame(main_frame, bg='#3c3c3c', width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)
        
        # Заголовок
        title_label = tk.Label(control_frame, text="Отсечение многоугольников", 
                              font=('Arial', 14, 'bold'), bg='#3c3c3c', fg='white')
        title_label.pack(pady=10)
        
        # Информация
        info_frame = tk.LabelFrame(control_frame, text="Информация", 
                                  bg='#3c3c3c', fg='white', font=('Arial', 10))
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.info_label = tk.Label(info_frame, text="", bg='#3c3c3c', fg='white', 
                                  justify=tk.LEFT)
        self.info_label.pack(padx=10, pady=10)
        
        # Управление
        control_buttons = tk.LabelFrame(control_frame, text="Управление", 
                                       bg='#3c3c3c', fg='white', font=('Arial', 10))
        control_buttons.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(control_buttons, text="Выполнить отсечение", command=self.perform_clipping,
                 bg='#4CAF50', fg='white', font=('Arial', 10), padx=10, pady=5).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_buttons, text="Сохранить PPM", command=self.save_ppm,
                 bg='#2196F3', fg='white', font=('Arial', 10), padx=10, pady=5).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_buttons, text="Сохранить BMP", command=self.save_bmp,
                 bg='#FF9800', fg='white', font=('Arial', 10), padx=10, pady=5).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_buttons, text="Очистить", command=self.clear_canvas,
                 bg='#f44336', fg='white', font=('Arial', 10), padx=10, pady=5).pack(fill=tk.X, padx=5, pady=5)
        
        # Настройки цветов
        color_frame = tk.LabelFrame(control_frame, text="Цвета", 
                                   bg='#3c3c3c', fg='white', font=('Arial', 10))
        color_frame.pack(fill=tk.X, padx=10, pady=10)
        
        colors_info = [
            ("Исходный многоугольник", "subject"),
            ("Окно отсечения", "clipper"),
            ("Результат (заливка)", "clipped_fill"),
            ("Результат (граница)", "clipped_border")
        ]
        
        for text, key in colors_info:
            color_box = tk.Frame(color_frame, bg=self.rgb_to_hex(self.colors[key]), 
                                height=20, width=20)
            color_box.pack(side=tk.LEFT, padx=5)
            tk.Label(color_frame, text=text, bg='#3c3c3c', fg='white', 
                    font=('Arial', 8)).pack(side=tk.LEFT, padx=5)
        
        # Правая панель с холстом
        canvas_frame = tk.Frame(main_frame, bg='black')
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Текстовый холст для отображения
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, 
                               height=self.canvas_height, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Статус бар
        self.status_bar = tk.Label(self.root, text="Готов к работе", 
                                  bg='#1a1a1a', fg='white', anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Обновление информации
        self.update_info()

    def rgb_to_hex(self, rgb):
        """Конвертация RGB в HEX цвет"""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def perform_clipping(self):
        """Выполнение отсечения"""
        try:
            self.clipped_polygon = sutherland_hodgman_clip(
                self.subject_polygon, 
                self.clipper_polygon
            )
            
            print(f"Вершин исходного полигона: {len(self.subject_polygon)}")
            print(f"Вершин после отсечения: {len(self.clipped_polygon)}")
            
            for p in self.clipped_polygon:
                print(p)
            
            self.draw_scene()
            self.update_info()
            self.status_bar.config(text="Отсечение выполнено успешно")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            self.status_bar.config(text=f"Ошибка: {str(e)}")

    def draw_scene(self):
        """Отрисовка всей сцены"""
        # Очищаем холст
        self.canvas_obj.clear(self.colors['background'])
        
        # Заливка результата (если есть)
        if self.clipped_polygon:
            scanline_fill(self.canvas_obj, self.clipped_polygon, self.colors['clipped_fill'])
        
        # Рисуем границы исходного многоугольника
        for i in range(len(self.subject_polygon)):
            p1 = self.subject_polygon[i]
            p2 = self.subject_polygon[(i + 1) % len(self.subject_polygon)]
            bresenham_line(self.canvas_obj, p1, p2, self.colors['subject'])
        
        # Рисуем окно отсечения
        for i in range(len(self.clipper_polygon)):
            p1 = self.clipper_polygon[i]
            p2 = self.clipper_polygon[(i + 1) % len(self.clipper_polygon)]
            bresenham_line(self.canvas_obj, p1, p2, self.colors['clipper'])
        
        # Рисуем границы результата
        if self.clipped_polygon:
            for i in range(len(self.clipped_polygon)):
                p1 = self.clipped_polygon[i]
                p2 = self.clipped_polygon[(i + 1) % len(self.clipped_polygon)]
                bresenham_line(self.canvas_obj, p1, p2, self.colors['clipped_border'])
        
        # Отображаем на tkinter canvas
        self.display_on_canvas()

    def display_on_canvas(self):
        """Отображение пикселей на tkinter canvas"""
        self.canvas.delete("all")
        
        # Создаем изображение
        img_data = []
        for y in range(self.canvas_height):
            for x in range(self.canvas_width):
                idx = y * self.canvas_width + x
                r, g, b = self.canvas_obj.pixels[idx]
                img_data.append(f"#{r:02x}{g:02x}{b:02x}")
        
        # Рисуем пиксели (используем прямоугольники для простоты)
        pixel_size = 1  # 1:1 масштаб
        for y in range(self.canvas_height):
            for x in range(self.canvas_width):
                idx = y * self.canvas_width + x
                color = img_data[idx]
                self.canvas.create_rectangle(
                    x * pixel_size, y * pixel_size,
                    (x + 1) * pixel_size, (y + 1) * pixel_size,
                    fill=color, outline=color
                )

    def save_ppm(self):
        """Сохранение в формат PPM"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".ppm",
                filetypes=[("PPM files", "*.ppm"), ("All files", "*.*")]
            )
            if filename:
                self.canvas_obj.save_ppm(filename)
                self.status_bar.config(text=f"Файл сохранен: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def save_bmp(self):
        """Сохранение в формат BMP"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".bmp",
                filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")]
            )
            if filename:
                self.canvas_obj.save_bmp(filename)
                self.status_bar.config(text=f"Файл сохранен: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def clear_canvas(self):
        """Очистка холста"""
        self.clipped_polygon = []
        self.canvas_obj.clear(self.colors['background'])
        self.display_on_canvas()
        self.update_info()
        self.status_bar.config(text="Холст очищен")

    def update_info(self):
        """Обновление информации о полигонах"""
        info_text = f"""
Исходный полигон:
• Вершин: {len(self.subject_polygon)}
• Площадь: {self.calculate_polygon_area(self.subject_polygon):.1f}

Окно отсечения:
• Вершин: {len(self.clipper_polygon)}
• Тип: прямоугольник

Результат:
• Вершин: {len(self.clipped_polygon) if self.clipped_polygon else 0}
        """.strip()
        
        self.info_label.config(text=info_text)

    def calculate_polygon_area(self, polygon):
        """Вычисление площади многоугольника"""
        if len(polygon) < 3:
            return 0
            
        area = 0
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            area += polygon[i].x * polygon[j].y
            area -= polygon[j].x * polygon[i].y
        
        return abs(area) / 2

def main():
    root = tk.Tk()
    app = PolygonClipperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()