from datetime import datetime
from serial.tools import list_ports
import tkinter as tk
import tkinter.filedialog
import serial
import csv
import os

class MotorController:

    def __init__(self, usb_mfr_regex='Velmex'):
        self.usb_mfr_regex = usb_mfr_regex
        self.port = None
        self.serial = None

        self.find_port()
        if self.port:
            self.serial = serial.Serial(self.port.device)

    def find_port(self):
        ports = list_ports.comports()
        for p in ports:
            if p.manufacturer and self.usb_mfr_regex in p.manufacturer:
                self.port = p

    def print_ports(self):
        ports = list_ports.comports()
        for p in ports:
            print(p.__dict__)

    def write(self, value):
        if self.serial:
            self.serial.write(str.encode(value))

    def move_command(self, dist):
        return f'F,C,I1M{dist},L1;'

    def convert_to_steps(self, dist):
        return dist * (1550 / 0.1) # steps = inches * (steps/inches))

    def move_forward(self, dist):
        self.write(self.move_command(self.convert_to_steps(dist)))

    def move_backward(self, dist):
        self.write(self.move_command(f'-{self.convert_to_steps(dist)}'))


class App(tk.Tk):

    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.default_step_distance = 0.1

        self.title("Concrete Aggregate Counter")
        self.geometry("500x400")

        self.raw_key_inputs = []

        self.heading = ('Input', 'Component', 'Count', 'Percent')

        self.keys_config = (
            ('a', 'Paste'),
            ('s', 'Coarse Aggregate'),
            ('d', 'Fine Aggregate'),
            ('f', 'Entrained Air'),
            ('c', 'Entrapped Air'),
            ('x', 'Other'),
        )

        self.total_label = 'Total'
        self.total_count = tk.IntVar()
        self.total_perc = tk.DoubleVar()

        self.step_distance = tk.DoubleVar()
        
        self.heading_row_offset = 1
        self.totals_row_offset = self.heading_row_offset + len(self.keys_config)
        self.controls_row_offset = self.totals_row_offset + 1

        self.setup()

    def setup(self):
        self.setup_heading()
        self.setup_keys()
        self.setup_totals()
        self.setup_specials()
        self.update_total_count_and_percentages()

    def setup_heading(self):
        for i, text in enumerate(self.heading):
            tk.Label(self, text=text, borderwidth=1).grid(row=0,column=i)

    def setup_keys(self):
        for i, row in enumerate(self.keys_config):
            key, label = row

            row_i = self.heading_row_offset + i
            key_count, key_perc = self.setup_key(key)

            tk.Label(self, text=key, borderwidth=1).grid(row=row_i,column=0)
            tk.Label(self, text=label, borderwidth=1).grid(row=row_i,column=1)
            tk.Label(self, textvariable=key_count, borderwidth=1).grid(row=row_i,column=2)
            tk.Label(self, textvariable=key_perc, borderwidth=1).grid(row=row_i,column=3)

    def setup_key(self, key):
        key_perc_id = self.get_key_percent_id(key)

        setattr(self, key, tk.IntVar())
        setattr(self, key_perc_id, tk.DoubleVar())

        key_count = self.reset_key(key)
        key_perc = getattr(self, key_perc_id)

        def on_key_press(evt):
            self.raw_key_inputs.append(key)
            self.update_key_count(key_count)
            self.update_total_count_and_percentages()
            self.move_forward(evt)

        self.bind(key, on_key_press)
        
        return (key_count, key_perc)

    def setup_totals(self):
        tk.Label(self, text=self.total_label).grid(row=self.totals_row_offset, column=1)
        tk.Label(self, textvariable=self.total_count).grid(row=self.totals_row_offset, column=2)
        tk.Label(self, textvariable=self.total_perc).grid(row=self.totals_row_offset, column=3)

    def setup_specials(self):
        self.step_distance.set(self.default_step_distance)
        # validatecommand

        tk.Button(self, text='Reset', command=self.clear_all).grid(row=self.controls_row_offset, column=0, sticky='E')
        tk.Button(self, text='Export', command=self.export_csv).grid(row=self.controls_row_offset, column=1, sticky='w')
        tk.Label(self, text='Step Dist. (in.)').grid(row=self.controls_row_offset, column=2)
        tk.Entry(self, textvariable=self.step_distance).grid(row=self.controls_row_offset, column=3)
        
        self.bind('<BackSpace>', self.clear_one)

        self.bind('<Right>', self.move_forward)
        self.bind('<Left>', self.move_backward)

    def get_key_percent_id(self, key):
        return f'{key}_perc'

    def update_total_count_and_percentages(self):
        total = 0

        for key, label in self.keys_config:
            total = total + getattr(self, key).get()

        self.total_count.set(total)

         # Sticking to 100.0 or 0.0 instead of nuanced rounding errors
        if total == 0:
            self.total_perc.set(0.0)
        else:
            self.total_perc.set(100.0)

        for key, label in self.keys_config:
            key_count = getattr(self, key).get()
            try:
                key_perc = round(key_count / total * 100, 1)
            except ZeroDivisionError:
                key_perc = 0.0
            getattr(self, self.get_key_percent_id(key)).set(key_perc)

    def update_key_count(self, key_count):
        new_value = key_count.get() + 1
        key_count.set(new_value)
        
    def reset_key(self, key):
        key_count = getattr(self, key)
        key_count.set(0)
        return key_count

    def clear_all(self):
        self.raw_key_inputs.clear()
        for key, label in self.keys_config:
            self.reset_key(key)
        self.update_total_count_and_percentages()

    def clear_one(self, evt):
        if len(self.raw_key_inputs):
            last_key = self.raw_key_inputs.pop()
            key_count = getattr(self, last_key)
            key_count.set(key_count.get() - 1)
            self.update_total_count_and_percentages()
            self.move_backward(evt)

    def export_csv(self):
        curr_dir = os.getcwd()
        initial_filename = f'aggregate-count-{datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")}'

        my_formats = [
            ('CSV', '*.csv'),
        ]

        filepath = tkinter.filedialog.asksaveasfile(
            parent=self,
            filetypes=my_formats,
            initialdir=curr_dir,
            initialfile=initial_filename,
            title="Save as...",
            defaultextension='.csv'
        )

        if filepath is None:
            return

        with open(filepath.name, 'w') as f:
            w = csv.writer(f)
            w.writerow(self.heading[1:])
            for key, label in self.keys_config:
                row = [
                    label,
                    getattr(self, key).get(),
                    getattr(self, self.get_key_percent_id(key)).get()
                ]
                w.writerow(row)
            w.writerow([
                self.total_label,
                self.total_count.get(),
                self.total_perc.get()
            ])

    def move_forward(self, evt):
        self.controller.move_forward(self.step_distance.get())

    def move_backward(self, evt):
        self.controller.move_backward(self.step_distance.get())


if __name__ == "__main__":
    controller = MotorController()
    app = App(controller)
    app.mainloop()
