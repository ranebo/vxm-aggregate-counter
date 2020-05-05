from datetime import datetime
from serial.tools import list_ports
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import serial
import csv
import os

class MotorController:

    def __init__(self, usb_mfr='Prolific'):
        self.usb_mfr = usb_mfr
        self.port = self.find_port()
        self.serial = None

        if self.port:
            self.serial = serial.Serial(self.port.device)

    def find_port(self):
        for p in self.list_ports():
            if p.manufacturer and self.usb_mfr in p.manufacturer:
                return p
        return None
    
    def list_ports(self):
        return list_ports.comports()

    def write(self, value):
        if self.serial:
            self.serial.write(str.encode(value))

    def move_command(self, dist):
        return f'F,C,I1M{dist},L1;'

    def convert_to_steps(self, dist):
        return int(round(dist * (1550 / 0.1))) # steps = inches * (steps/inches))

    def move_forward(self, dist):
        self.write(self.move_command(self.convert_to_steps(dist)))

    def move_backward(self, dist):
        self.write(self.move_command(f'-{self.convert_to_steps(dist)}'))


class App(tk.Tk):

    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        self.concrete_dist = 0.1
        self.mortar_stucco_dist = 0.05
        self.max_step_dist = 5.0
        self.default_step_dist = self.concrete_dist

        self.title("Jon's PetroPro")
        self.geometry("500x350")

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

        self.step_dist = tk.StringVar()
        self.step_dist_entry = tk.Entry(
            self,
            textvariable=self.step_dist,
            validate='all',
            justify='center',
            # other options see here: https://stackoverflow.com/questions/4140437/interactively-validating-entry-widget-content-in-tkinter
            validatecommand=(self.register(self.validate_step_increment), '%P', '%S', '%V'),
            invalidcommand=(self.register(self.invalid_step_increment), '%P', '%s', '%V')
        )

        self.heading_row_offset = 2
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
            tk.Label(self, text=text, pady=5, font='Verdana 14 bold underline').grid(row=1,column=i)

    def setup_keys(self):
        for i, row in enumerate(self.keys_config):
            key, label = row

            row_i = self.heading_row_offset + i
            key_count, key_perc = self.setup_key(key)

            tk.Label(self, text=key).grid(row=row_i,column=0)
            tk.Label(self, text=label).grid(row=row_i,column=1)
            tk.Label(self, textvariable=key_count).grid(row=row_i,column=2)
            tk.Label(self, textvariable=key_perc).grid(row=row_i,column=3)

    def setup_key(self, key):
        key_perc_id = self.get_key_percent_id(key)

        setattr(self, key, tk.IntVar())
        setattr(self, key_perc_id, tk.DoubleVar())

        key_count = self.reset_key(key)
        key_perc = getattr(self, key_perc_id)

        def on_key_press(evt):
            if self.is_bound_key_event(evt):
                self.raw_key_inputs.append(key)
                new_value = key_count.get() + 1
                key_count.set(new_value)
                self.update_total_count_and_percentages()
                self.step_forward(evt)

        self.bind(key, on_key_press)
        
        return (key_count, key_perc)

    def setup_totals(self):
        pady = 10
        tk.Label(self, pady=pady, font='Verdana 12 bold', text=self.total_label).grid(row=self.totals_row_offset, column=1)
        tk.Label(self, pady=pady, font='Verdana 12 bold', textvariable=self.total_count).grid(row=self.totals_row_offset, column=2)
        tk.Label(self, pady=pady, font='Verdana 12 bold', textvariable=self.total_perc).grid(row=self.totals_row_offset, column=3)

    def setup_specials(self):
        self.step_dist.set(self.default_step_dist)

        step_pady = 25
        data_pady = 20
        muted_text = 'grey'

        tk.Label(self, text='Step Dist. (in.):', fg=muted_text).grid(row=0, column=0, pady=step_pady, sticky='E')
        self.step_dist_entry.grid(row=0, column=1, pady=step_pady)
        tk.Button(self, text='Concrete', command=self.set_concrete_dist).grid(row=0, column=2, pady=step_pady, sticky='WE')
        tk.Button(self, text='Mortar/Stucco', command=self.set_mortar_stucco_dist).grid(row=0, column=3, pady=step_pady, sticky='WE')

        tk.Button(self, text='List Ports', command=self.list_ports).grid(row=self.controls_row_offset, column=0, pady=data_pady, sticky='E')
        tk.Label(self, text='Data Options:', fg=muted_text).grid(row=self.controls_row_offset, column=1, pady=data_pady, sticky='E')
        tk.Button(self, text='Reset', command=self.clear_all).grid(row=self.controls_row_offset, column=2, pady=data_pady, sticky='WE')
        tk.Button(self, text='Export', command=self.export_data).grid(row=self.controls_row_offset, column=3, pady=data_pady, sticky='WE')

        self.bind('<BackSpace>', self.clear_last)

        self.bind('<Return>', lambda evt: self.focus_set())
        self.bind('<1>', self.step_dist_entry_focus)

        self.bind('<Right>', self.step_forward)
        self.bind('<Left>', self.step_backward)

    def set_concrete_dist(self):
        self.step_dist.set(self.concrete_dist)
        self.default_step_dist =  self.concrete_dist

    def set_mortar_stucco_dist(self):
        self.step_dist.set(self.mortar_stucco_dist)
        self.default_step_dist =  self.mortar_stucco_dist

    def validate_step_increment(self, P, S, V):
        try:
            if V == 'focusout':
                value = float(P)
                if value > self.max_step_dist or value < 0:
                    raise ValueError(f'Step Dist. must be less than {self.max_step_dist}')
                return True

            if len(S) == 0 or S.isdigit():
                return True

            if len(P):
                float(P)

            return True
        except ValueError:
            return False

    def invalid_step_increment(self, P, s, V):
        if V == 'focusout':
            value = self.default_step_dist

            if len(P):
                xvalue = float(P)
                if xvalue > self.max_step_dist:
                    value = self.max_step_dist
                elif xvalue < 0:
                    value = 0

            self.step_dist_entry.config(validate="none")
            self.step_dist.set(value)
            self.step_dist_entry.config(validate="all")

    def list_ports(self):
        message = ''
        for p in self.controller.list_ports():
            message = message + '\n' + '\n'.join([
                f'Device: {p.device}',
                f'Name: {p.name}',
                f'Description: {p.description}',
                f'Manufacturer: {p.manufacturer}',
                f'Product: {p.product}',
            ]) + '\n'
        tkinter.messagebox.showinfo(title='Ports', message=message)

    def is_bound_key_event(self, evt):
        return evt.widget != self.step_dist_entry

    def step_dist_entry_focus(self, evt):
        if evt.widget != self.step_dist_entry:
            self.focus_set()

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

    def get_key_percent_id(self, key):
        return f'{key}_perc'

    def reset_key(self, key):
        key_count = getattr(self, key)
        key_count.set(0)
        return key_count

    def clear_all(self):
        self.raw_key_inputs.clear()
        for key, label in self.keys_config:
            self.reset_key(key)
        self.update_total_count_and_percentages()

    def clear_last(self, evt):
        if self.is_bound_key_event(evt) and len(self.raw_key_inputs):
            last_key = self.raw_key_inputs.pop()
            key_count = getattr(self, last_key)
            key_count.set(key_count.get() - 1)
            self.update_total_count_and_percentages()
            self.step_backward(evt)

    def step_forward(self, evt):
        if self.is_bound_key_event(evt):
            self.controller.move_forward(float(self.step_dist.get()))

    def step_backward(self, evt):
        if self.is_bound_key_event(evt):
            self.controller.move_backward(float(self.step_dist.get()))

    def export_data(self):
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
            title='Save as...',
            defaultextension='.csv'
        )

        if filepath is None:
            return
        
        # Can check filepath type for writing different file types (maybe break out into own class - file handling)
        self.write_csv(filepath)

    def write_csv(self, filepath):
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


if __name__ == "__main__":
    controller = MotorController()
    app = App(controller)
    app.mainloop()
