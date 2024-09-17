# display_output.py

import tkinter as tk
from tkinter import ttk

def display_in_gui(df, title="Financial Ratios Output"):
    # Create the main window
    root = tk.Tk()
    root.title(title)

    # Create a frame for the Treeview
    frame = ttk.Frame(root)
    frame.pack(padx=10, pady=10, fill='both', expand=True)

    # Create the Treeview widget with horizontal scrollbar support
    tree = ttk.Treeview(frame, columns=list(df.columns), show='headings')

    # Add a vertical scrollbar to the Treeview
    vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    vsb.pack(side='right', fill='y')
    tree.configure(yscroll=vsb.set)

    # Add a horizontal scrollbar to the Treeview
    hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
    hsb.pack(side='bottom', fill='x')
    tree.configure(xscroll=hsb.set)

    # Pack the Treeview
    tree.pack(side='left', fill='both', expand=True)

    # Define the columns
    for col in df.columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', width=120)

    # Insert data into the Treeview
    for index, row in df.iterrows():
        tree.insert('', 'end', values=list(row))

    # Run the application
    root.mainloop()
