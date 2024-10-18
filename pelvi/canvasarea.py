import tkinter as tk
from pelvi.background import load_image_to_canvas

class CanvasArea:
    def __init__(self, parent, pelvi, axis1, axis2, width, height, background_image):
        self.canvas = tk.Canvas(parent, width=width, height=height)
        load_image_to_canvas(self.canvas, background_image, width, height)
        self.canvas.bind("<Button-1>", self.on_click_canvas)
        self.canvas.bind("<Configure>", self.on_resize)
        self.pelvi = pelvi
        self.point = None
        self.axis1 = axis1
        self.axis2 = axis2

    @classmethod
    def create_canvas_area(cls, parent, pelvi, axis1, axis2, width, height, background_image, row, column):
        canvas_area = cls(parent, pelvi, axis1, axis2, width, height, background_image)
        canvas_area.create_axes_lines(0, 0)
        canvas_area.canvas.grid(row=row, column=column, padx=4, pady=5)
        return canvas_area

    def on_click_canvas(self, event):
        x = event.x
        y = event.y

        if x < 0 or x > self.canvas.winfo_width() or y < 0 or y > self.canvas.winfo_height():
            print("Click outside the canvas")
            return
        self.move_to(x, y)

    def on_resize(self, event):
        self.update_point()

    def update_point(self):
        if self.axis1 == self.axis2:
            x_pixel = self.canvas.winfo_width() // 2
            y_pixel = self.pelvi.get_axis_value(self.axis1)
        else:
            x_pixel = self.pelvi.get_axis_value(self.axis1)
            y_pixel = self.pelvi.get_axis_value(self.axis2)

        if self.point:
            self.canvas.delete(self.point)
        self.point = self.canvas.create_oval(x_pixel - 5, y_pixel - 5, x_pixel + 5, y_pixel + 5, fill='blue')

    def create_axes_lines(self, axis1_pos, axis2_pos):
        self.canvas.create_line(axis1_pos, 0, axis1_pos, self.canvas.winfo_height(), fill="black")
        self.canvas.create_line(0, axis2_pos, self.canvas.winfo_width(), axis2_pos, fill="black")

    def delete_point(self):
        if self.point:
            self.canvas.delete(self.point)
            self.point = None

    def update_red_rectangle(self):
        # Get current rectangle coordinates from pelvi
        rectangle_left, rectangle_right = self.pelvi.get_blocked_area("X")
        rectangle_top, rectangle_bottom = self.pelvi.get_blocked_area("Y")

        self.canvas.delete('red_rectangle')

        self.canvas.create_rectangle(
            rectangle_left,
            rectangle_top,
            rectangle_right,
            rectangle_bottom,
            fill='red',
            outline='',
            tags='red_rectangle'
        )

    def move_by(self, axis, value):
        self.pelvi.move_axis_by(axis, value)
        if axis == self.axis1 or axis == self.axis2:
            if self.move_to(self.pelvi.get_axis_value(self.axis1), self.pelvi.get_axis_value(self.axis2)) is False:
                self.pelvi.move_axis_by(axis, -value)
        else:
            self.move_to(self.pelvi.get_axis_value(self.axis1), self.pelvi.get_axis_value(self.axis2))

    def move_to(self, x, y):
        if self.axis1 == "X" and self.axis2 == "Y" and self.is_point_inside_rectangle(x, y):
            print("Bewegung in den roten Bereich ist nicht erlaubt.")
            return False
        self.pelvi.move_axis_to(self.axis1, x)
        self.pelvi.move_axis_to(self.axis2, y)
        self.update_point()
        return True

    def is_point_inside_rectangle(self, x_mm, y_mm):
        return ((self.pelvi.get_blocked_area("X")[0] <= x_mm <= self.pelvi.get_blocked_area("X")[1])
                and (self.pelvi.get_blocked_area("Y")[0] <= y_mm <= self.pelvi.get_blocked_area("Y")[1]))

    def is_inside_rectangle(self, left, top, right, bottom):
        points = [(self.pelvi.get_axis_value("X"), self.pelvi.get_axis_value("Y"))]
        for x, y in points:
            if left <= x <= right and top <= y <= bottom:
                return True
        return False

    def adjust_blocked_position(self, dx=0, dy=0):
        rectangle_left, rectangle_right = self.pelvi.get_blocked_area("X")
        rectangle_top, rectangle_bottom = self.pelvi.get_blocked_area("Y")

        new_left = rectangle_left + dx
        new_top = rectangle_top + dy
        new_right = rectangle_right + dx
        new_bottom = rectangle_bottom + dy

        if new_left < 0:
            new_left = 0
            new_right = rectangle_right - rectangle_left
        if new_top < 0:
            new_top = 0
            new_bottom = rectangle_bottom - rectangle_top
        if new_right > self.pelvi.get_axis_range("X"):
            new_right = self.pelvi.get_axis_range("X")
            new_left = self.pelvi.get_axis_range("X") - (rectangle_right - rectangle_left)
        if new_bottom > self.pelvi.get_axis_range("Y"):
            new_bottom = self.pelvi.get_axis_range("Y")
            new_top = self.pelvi.get_axis_range("Y") - (rectangle_bottom - rectangle_top)

        if self.is_inside_rectangle(new_left, new_top, new_right, new_bottom):
            print("Blockierte Position kann nicht auf den aktuellen Punkt verschoben werden.")
            return

        self.pelvi.update_blocked_area("X", new_left, new_right)
        self.pelvi.update_blocked_area("Y", new_top, new_bottom)

        self.update_red_rectangle()