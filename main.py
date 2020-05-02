import tkinter as tk

def key_percent_id(key):
    return f'{key}_perc'

class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Concrete Aggregate Counter")
        self.geometry("300x400")

        self.raw_key_inputs = []

        self.heading = ('Input', 'Component', 'Count', 'Percent')
        self.header_row_offset = 1

        self.keys_config = (
            ('a', 'Paste'),
            ('s', 'Coarse Aggregate'),
            ('d', 'Fine Aggregate'),
            ('f', 'Entrained Air'),
            ('c', 'Entrapped Air'),
            ('x', 'Other'),
        )
        self.setup()

    def setup(self):
        self.bind('<BackSpace>', self.clear_one)
        # button for reset data
        # button for export data
        self.setup_heading()
        self.setup_keys()
        self.setup_totals()
        self.update_total_count_and_percentages()
        self.reset_button = tk.Button(self, text="Reset", command=self.clear_all)
        self.export_button = tk.Button(self, text="Export") # , command=self.clear_all)

        row_offset = self.header_row_offset + len(self.keys_config) + 1
        
        self.reset_button.grid(row=row_offset, column=0)
        self.export_button.grid(row=row_offset, column=1)

    def setup_heading(self):
        for i, text in enumerate(self.heading):
            tk.Label(self, text=text, borderwidth=1).grid(row=0,column=i)

    def setup_keys(self):
        for i, row in enumerate(self.keys_config):
            key, label = row
            row_i = self.header_row_offset + i
            key_count, key_perc = self.setup_key(key)

            tk.Label(self, text=key, borderwidth=1).grid(row=row_i,column=0)
            tk.Label(self, text=label, borderwidth=1).grid(row=row_i,column=1)
            tk.Label(self, textvariable=key_count, borderwidth=1).grid(row=row_i,column=2)
            tk.Label(self, textvariable=key_perc, borderwidth=1).grid(row=row_i,column=3)

    def setup_key(self, key):
        key_perc_id = key_percent_id(key)

        setattr(self, key, tk.IntVar())
        setattr(self, key_perc_id, tk.IntVar())

        key_count = self.reset_key(key)
        key_perc = getattr(self, key_perc_id)

        def on_key_press(evt):
            self.raw_key_inputs.append(key)
            self.update_key_count(key_count)
            self.update_total_count_and_percentages()

        self.bind(key, on_key_press)
        
        return (key_count, key_perc)

    def setup_totals(self):
        self.total_count = tk.IntVar()
        self.total_perc = tk.IntVar()
        row_offset = self.header_row_offset + len(self.keys_config)

        tk.Label(self, text='Total').grid(row=row_offset, column=1)
        tk.Label(self, textvariable=self.total_count).grid(row=row_offset, column=2)
        tk.Label(self, textvariable=self.total_perc).grid(row=row_offset, column=3)

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
            key_perc_id = key_percent_id(key)
            key_count = getattr(self, key).get()
            try:
                key_perc = round(key_count / total * 100, 1)
            except ZeroDivisionError:
                key_perc = 0.0
            getattr(self, key_perc_id).set(key_perc)

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

    def export_csv(self):
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
