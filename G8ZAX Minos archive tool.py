# G8ZAX Minos Archive tool. Allows multiple .cls, .edi and .minos
#       files for be combined into an archive file

# Copyright (C) 2025  Rob Rees G8ZAX  rob.rees@zaxsoft.co.uk

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import re

class CSLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minos Archive Maker R Rees G8ZAX")
        self.data = defaultdict(list)
        self.selections = {}
        self.output_path = None

        tk.Button(root, text="Create Blank Output File", command=self.create_output_file).pack(pady=5)
        file_buttons_frame = tk.Frame(root)
        file_buttons_frame.pack(pady=5)

        tk.Button(file_buttons_frame, text="Import .csl Files", command=self.import_csl_files).pack(side=tk.LEFT, padx=2)
        tk.Button(file_buttons_frame, text="Import .edi Files", command=self.import_edi_files).pack(side=tk.LEFT, padx=2)
        tk.Button(file_buttons_frame, text="Import .minos Files", command=self.import_minos_files).pack(side=tk.LEFT, padx=2)

        self.keep_all_var = tk.BooleanVar()
        #feature removed
        #tk.Checkbutton(root, text="Keep all duplicates", variable=self.keep_all_var).pack()

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=300)
        self.progress.pack(pady=5)
        self.log = tk.Text(root, height=8, width=80)
        self.log.pack(pady=5)
        self.frame = tk.Frame(root)
        self.canvas = tk.Canvas(self.frame, width=600, height=300)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.frame.pack(pady=10)
        self.canvas.pack(side="left")
        self.scrollbar.pack(side="right", fill="y")
        self.save_button = tk.Button(root, text="Save to Output File", command=self.save_output, state=tk.DISABLED)
        self.save_button.pack(pady=10)

    def log_message(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)

    def log_error(self, message):
        with open("errors.txt", "a") as error_file:
            error_file.write(message + "\n")

    def create_output_file(self):
        self.output_path = filedialog.asksaveasfilename(defaultextension=".csl", filetypes=[("CSL files", "*.csl")])
        if self.output_path:
            open(self.output_path, 'w').close()
            self.log_message(f"Blank output file created: {os.path.basename(self.output_path)}")
            self.save_button.config(state=tk.DISABLED)

    def import_csl_files(self):
        self.import_files(".csl")

    def import_edi_files(self):
        self.import_files(".edi")

    def import_minos_files(self):
        self.import_files(".minos")

    def import_files(self, extension):
        if not self.output_path:
            messagebox.showwarning("No Output File", "Please create a blank output file first.")
            return

        file_paths = filedialog.askopenfilenames(filetypes=[(f"{extension.upper()} Files", f"*{extension}")])
        if not file_paths:
            return

        self.progress["maximum"] = len(file_paths)
        self.progress["value"] = 0

        for i, path in enumerate(file_paths):
            self.log_message(f"Reading file: {os.path.basename(path)}")
            try:
                if path.endswith('.csl'):
                    self.load_csl_file(path)
                elif path.endswith('.edi'):
                    self.load_edi_file(path)
                elif path.endswith('.minos'):
                    self.load_minos_file(path)
            except Exception as e:
                self.log_error(f"Error reading {os.path.basename(path)}: {e}")

            self.progress["value"] = i + 1
            self.root.update_idletasks()

        self.resolve_duplicates()
        self.save_button.config(state=tk.NORMAL)
        self.log_message("File import complete.")

    def normalize_name(self, name):
        return name.strip().capitalize() if name else ''

    def load_csl_file(self, path):
        with open(path, newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 3:
                    first = row[0].strip()
                    second = row[1].strip()
                    name = self.normalize_name(row[2])
                    key = (first, second)
                    RRfirst = first not in {k[0] for k in self.data.keys()}
                    self.data[key].append(name)
                    self.log_message(f"Added: {first}, {second}, {name}" + (" [NEW]" if RRfirst else ""))

    def load_edi_file(self, path):
        with open(path, 'r') as file:
            start = False
            for line in file:
                if line.strip().startswith('[QSORecords'):
                    start = True
                    continue
                if not start:
                    continue
                fields = line.strip().split(';')
                if len(fields) >= 10:
                    first = fields[2].strip()
                    second = fields[9].strip()
                    key = (first, second)
                    existing_names = self.data.get(key, [])
                    if any(name.strip() for name in existing_names):
                        self.log_message(f"Skipped: {first}, {second} (non-blank name already exists)")
                        continue
                    RRfirst = first not in {k[0] for k in self.data.keys()}
                    self.data[key].append('')
                    self.log_message(f"Added: {first}, {second}, (from .edi)" + (" [NEW]" if RRfirst else ""))

    def load_minos_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            # Find all complete <iq>...</iq> blocks
            iq_blocks = re.findall(r"<iq.*?>.*?</iq>", content, re.DOTALL)

            blocks = defaultdict(dict)

            for block in iq_blocks:
                try:
                    root = ET.fromstring(block)
                    struct = root.find(".//{*}struct")
                    if struct is None:
                        continue

                    entry = {}
                    lseq = None
                    for member in struct.findall("{*}member"):
                        name_el = member.find("{*}name")
                        value_el = member.find("{*}value")
                        if name_el is None or value_el is None:
                            continue

                        tag = name_el.text
                        text = None
                        for subtag in ["string", "i4"]:
                            sub_el = value_el.find("{*}" + subtag)
                            if sub_el is not None:
                                text = sub_el.text
                                break
                        if text:
                            entry[tag] = text.strip()
                            if tag == "lseq":
                                lseq = text.strip()

                    if lseq:
                        blocks[lseq].update(entry)

                except ET.ParseError as e:
                    self.log_error(f"XML block parse error in {os.path.basename(path)}: {e}")

            for lseq, entry in blocks.items():
                call = entry.get("callRx")
                loc = entry.get("locRx")
                name = self.normalize_name(entry.get("commentsTx") or entry.get("commentsRx"))
                if call and loc:
                    key = (call, loc)
                    RRfirst = call not in {k[0] for k in self.data.keys()}
                    self.data[key].append(name if name else '')
                    self.log_message(f"Added: {call}, {loc}, {name if name else ''}" + (" [NEW]" if RRfirst else ""))

        except Exception as e:
            self.log_error(f"Unexpected error in {os.path.basename(path)}: {e}")

    def resolve_duplicates(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for (first, second), names in self.data.items():
            unique_names = list(set(names))
            if len(unique_names) == 1 and not self.keep_all_var.get():
                self.selections[(first, second)] = unique_names[0]
                continue

            unique_names = list(filter(None, unique_names))
            bg_color = 'skyblue' if len(unique_names) > 1 else None
            if len(unique_names) > 1:
                entry_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
                tk.Label(entry_frame, text=f"{first}, {second}", font=("Arial", 10, "bold"), bg=bg_color).pack(anchor="w")
                #self.log_message(f"uniquename: {type(unique_names)}")
                default = max(unique_names, key=len)
                var = tk.StringVar(value=default)
                #self.log_message(f"default: {default}")
                for name in sorted(unique_names):
                    #we only want the strings from this list that are not null
                    if name:
                        tk.Radiobutton(entry_frame, text=name, variable=var, value=name, bg=bg_color).pack(anchor="w")
                    entry_frame.pack(fill='x', padx=2, pady=2)
                    self.selections[(first, second)] = var

    def save_output(self):
        if not self.output_path:
            messagebox.showwarning("No Output File", "Please create a blank output file first.")
            return

        with open(self.output_path, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            if self.keep_all_var.get():
                for (first, second), name_list in self.data.items():
                    for name in sorted(name_list):
                        if name.strip():
                            writer.writerow([first, second, name])
            else:
                for (first, second), name_sel in sorted(self.selections.items()):
                    name = name_sel.get() if isinstance(name_sel, tk.StringVar) else name_sel
                    writer.writerow([first, second, name])

        messagebox.showinfo("Saved", f"Saved merged CSL to {os.path.basename(self.output_path)}")
        self.log_message(f"Saved merged output to: {os.path.basename(self.output_path)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSLProcessorApp(root)
    root.mainloop()
