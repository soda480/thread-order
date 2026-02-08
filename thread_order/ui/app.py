import queue
import threading
import json
from pathlib import Path
import importlib.metadata
from tkinter import messagebox
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.tableview import Tableview
from tkinter import filedialog
from tkinter import font as tkfont
from thread_order import (
    Scheduler,
    load_and_collect_functions,
    register_functions
)

CARD_WIDTH = 130
CARD_HEIGHT = 64

class Runner(tb.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.colors = self.master.style.colors
        self._status_icons = {
            'PASSED': self._make_swatch('#2ecc71'),  # green
            'FAILED': self._make_swatch('#e74c3c'),  # red
            'SKIPPED': self._make_swatch('#f1c40f'),  # yellow
        }
        self.setupui()
        self._uiqueue = queue.Queue()
        self._poll_uiqueue()
        self._running = False

    def setupui(self):
        self.pack()

        # menubar
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open Tasks', command=self.open_tasks)
        file_menu.add_command(label='Open State', command=self.open_state)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.master.quit)
        menubar.add_cascade(label='File', menu=file_menu)

        options_menu = tk.Menu(menubar, tearoff=0)
        self.log_all_var = tk.BooleanVar(value=False)
        options_menu.add_checkbutton(label='Log All', variable=self.log_all_var)
        self.skip_dependents_var = tk.BooleanVar(value=False)
        options_menu.add_checkbutton(label='Skip Dependents', variable=self.skip_dependents_var)
        menubar.add_cascade(label='Options', menu=options_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label='About', command=self.show_about)
        menubar.add_cascade(label='Help', menu=help_menu)

        self.master.config(menu=menubar)

        top_frame = tb.Frame(self.master, padding=4)
        top_frame.pack(fill=BOTH, expand=False)

        self.workers = tb.StringVar(value='16')
        label1 = tb.Label(
            top_frame,
            text='Workers:',
            justify='right')
        label1.grid(row=0, column=0, padx=(4, 2), pady=4, sticky=W)
        self.spinbox_workers = tb.Spinbox(
            name='workers',
            master=top_frame,
            width=4,
            from_=1,
            to=128,
            justify='right',
            textvariable=self.workers,
            command=self.on_workers_change)
        self.spinbox_workers.grid(row=0, column=1, padx=(0, 12), pady=4, sticky=W)
        self.run_button = tb.Button(
            top_frame,
            text='Run Tasks',
            command=self.run_tasks,
            state='enabled',
            width=10,
            bootstyle='primary',
            padding=(16, 10))
        self.run_button.grid(row=0, column=2, padx=(0, 4), pady=4, sticky=W)

        bot_frame = tb.Frame(self.master, padding=4)
        bot_frame.pack(fill=BOTH, expand=True)

        # setup tabs
        self.notebook = tb.Notebook(bot_frame)
        self.notebook.pack(padx=10, pady=(4, 2), fill=BOTH, expand=True)

        tab1 = tb.Frame(self.notebook)
        tab2 = tb.Frame(self.notebook)
        tab3 = tb.Frame(self.notebook)
        tab4 = tb.Frame(self.notebook)

        frame_state_top = tb.Frame(tab1)
        frame_state_bot = tb.Frame(tab1)
        frame_state_top.pack(fill=X, expand=False)
        frame_state_bot.pack(fill=BOTH, expand=True)

        self.key_value = tb.StringVar(value='')
        entry_key_value = tb.Entry(
            frame_state_top,
            width=50,
            justify='left',
            textvariable=self.key_value)
        entry_key_value.pack(side=LEFT, padx=4, pady=4, fill=X, expand=True)
        button_key_value = tb.Button(
            frame_state_top,
            text='Add Key Value',
            command=self.add_key_value,
            state='enabled',
            width=12,
            bootstyle='primary')
        entry_key_value.bind(
            '<Return>',
            lambda e: button_key_value.invoke())
        button_key_value.pack(side=LEFT, padx=4, pady=4)
        self.table_state = Tableview(
            master=frame_state_bot,
            coldata=['Key', 'Value', 'Source', ''],
            rowdata=[],
            paginated=False,
            autofit=False,
            searchable=False,
            bootstyle='primary',
            yscrollbar=True,
            stripecolor=(self.colors.light, None),
        )
        self.table_state.pack(fill=BOTH, expand=True)
        self.table_state.view.column(self.table_state.get_columns()[-1].cid, stretch=True)
        self.table_state.autofit_columns()

        # TASKS TAB
        tasks_frame = tb.Frame(tab2)
        tasks_frame.pack(fill=BOTH, expand=True, padx=4, pady=4)

        total_tasks_frame = tb.Frame(tasks_frame)
        total_tasks_frame.pack(fill=X, expand=False)
        self.tasks_total_var = tb.IntVar(value=0)
        self._make_counter(total_tasks_frame, 'Total', self.tasks_total_var, bootstyle='dark')

        self.table_tasks = Tableview(
            master=tasks_frame,
            coldata=['Tasks', 'Dependencies'],
            rowdata=[],
            paginated=False,
            autofit=False,
            searchable=False,
            bootstyle='primary',
            yscrollbar=True,
            stripecolor=(self.colors.light, None),
            disable_right_click=True,
        )
        self.table_tasks.load_table_data()
        self.table_tasks.pack(fill=BOTH, expand=True, padx=4, pady=4)
        table_tasks_view = self.table_tasks.view
        table_tasks_cols = self.table_tasks.get_columns()
        table_tasks_task_col = table_tasks_cols[0].cid
        table_tasks_view.heading(table_tasks_task_col, anchor='w')
        table_tasks_view.column(
            table_tasks_task_col, stretch=True, anchor='w', width=400, minwidth=120)
        table_tasks_view.configure(show='tree headings')
        table_tasks_view.heading('#0', text='#')
        table_tasks_view.column(
            '#0',
            width=40,
            minwidth=40,
            stretch=False,
            anchor='w'
        )

        # THREADS TAB
        threads_frame = tb.Frame(tab3)
        threads_frame.pack(fill=BOTH, expand=True, padx=4, pady=4)

        thread_viewer_frame = tb.Frame(threads_frame)
        thread_viewer_frame.pack(fill=X, expand=False)

        self.queued_var = tb.IntVar(value=0)
        self.active_var = tb.IntVar(value=0)
        self.closed_var = tb.IntVar(value=0)

        self._make_counter(thread_viewer_frame, 'Queued', self.queued_var, bootstyle='dark')
        self._make_counter(thread_viewer_frame, 'Active', self.active_var, bootstyle='primary')
        self._make_counter(thread_viewer_frame, 'Closed', self.closed_var, bootstyle='secondary')

        self.table_threads = Tableview(
            master=threads_frame,
            coldata=['Thread', 'Task'],
            rowdata=[(f'thread_{i}', '') for i in range(int(self.workers.get()))],
            paginated=False,
            autofit=False,
            searchable=False,
            bootstyle='primary',
            yscrollbar=True,
            stripecolor=(self.colors.light, None),
            disable_right_click=True,
        )
        self.table_threads.load_table_data()
        self.table_threads.pack(fill=BOTH, expand=True, padx=4, pady=4)
        table_threads_view = self.table_threads.view
        table_threads_cols = self.table_threads.get_columns()
        table_threads_task_col = table_threads_cols[1].cid
        table_threads_view.heading(table_threads_task_col, anchor="w")
        table_threads_view.column(
            table_threads_task_col, stretch=True, anchor="w", width=400, minwidth=120)

        # RUN TAB
        run_frame = tb.Frame(tab4)
        run_frame.pack(fill=BOTH, expand=True, padx=4, pady=4)

        summary_frame = tb.Frame(run_frame)
        summary_frame.pack(fill=X, expand=False)

        self.total_var = tb.IntVar(value=0)
        self.passed_var = tb.IntVar(value=0)
        self.failed_var = tb.IntVar(value=0)
        self.skipped_var = tb.IntVar(value=0)

        self._make_counter(summary_frame, 'Total', self.total_var, bootstyle='dark')
        self._make_counter(summary_frame, 'Passed', self.passed_var, bootstyle='success')
        self._make_counter(summary_frame, 'Failed', self.failed_var, bootstyle='danger')
        self._make_counter(summary_frame, 'Skipped', self.skipped_var, bootstyle='warning')

        self.table_run = Tableview(
            master=run_frame,
            coldata=['#', 'Task'],
            rowdata=[],
            paginated=False,
            autofit=False,
            searchable=False,
            bootstyle='primary',
            yscrollbar=True,
            stripecolor=(self.colors.light, None),
            disable_right_click=True,
        )
        self.table_run.load_table_data()
        self.table_run.pack(fill=BOTH, expand=True, padx=4, pady=4)

        table_run_view = self.table_run.view
        cols = self.table_run.get_columns()
        num_col = cols[0].cid
        task_col = cols[1].cid
        table_run_view.configure(show='tree headings')
        ICON_W = 46
        table_run_view.heading('#0', text='')
        table_run_view.column('#0', width=ICON_W, minwidth=ICON_W, stretch=False, anchor='center')
        table_run_view.heading(num_col, anchor='w')
        table_run_view.column(num_col, stretch=False, anchor='w', width=40, minwidth=40)
        table_run_view.heading(task_col, anchor='w')
        table_run_view.column(task_col, stretch=True, anchor='w', width=400, minwidth=120)

        self.after(0, self.hide_all_hscrollbars)

        self.notebook.add(tab1, text='State')
        self.notebook.add(tab2, text='Tasks')
        self.notebook.add(tab3, text='Threads')
        self.notebook.add(tab4, text='Run')

        # STATUS BAR
        self.footer = tb.Frame(self.master, padding=(8, 4))
        self.footer.pack(side=BOTTOM, fill=X)
        self.duration_var = tb.StringVar(value='')
        self.duration_label = tb.Label(
            self.footer,
            textvariable=self.duration_var,
            font=('Segoe UI', 8),
            anchor='w'
        )
        self.duration_label.pack(side=LEFT, fill=X, expand=False)
        self.running_frame = tb.Frame(self.footer)
        self.progress_var = tb.IntVar(value=0)
        self.progress = tb.Progressbar(
            self.running_frame,
            mode='determinate',
            variable=self.progress_var,
        )
        self.progress.pack(side=LEFT, fill=X, expand=True)
        self.percent_var = tb.StringVar(value="")
        self.percent_label = tb.Label(
            self.running_frame,
            textvariable=self.percent_var,
            width=4,
            font=('Segoe UI', 8),
            anchor='e')
        self.percent_label.pack(side=LEFT, padx=(8, 0))

        self._hide_running_footer()

    def add_key_value(self):
        key_value = self.key_value.get()
        if key_value and key_value.count('=') == 1:
            key_value_split = key_value.split('=')
            key = key_value_split[0].strip()
            value = key_value_split[1].strip()
            if value:
                self.table_state.insert_row(index=0, values=(key, value, 'user', ''))
                self.table_state.autofit_columns()
                self.key_value.set('')

    def on_workers_change(self):
        self.notebook.select(2)
        workers = int(self.workers.get())
        self.table_threads.delete_rows()
        self.table_threads.insert_rows(0, rowdata=[(f'thread_{i}', '') for i in range(workers)])
        self.table_threads.autofit_columns()

    def open_tasks(self):
        try:
            path = filedialog.askopenfilename(
                title='Select a file',
                filetypes=[
                    ('Python files', '*.py'),
                ],
            )
            if not path:
                return

            self.notebook.select(1)

            module, marked_functions, single_function_mode = load_and_collect_functions(path)

            # store for run
            self._tasks_path = path
            self._module = module
            self._marked_functions = marked_functions
            self._single_function_mode = single_function_mode

            preview_scheduler = Scheduler(
                workers=1,
                setup_logging=False
            )
            register_functions(preview_scheduler, marked_functions, None, False)

            # populate tasks table from preview graph
            self.table_tasks.delete_rows()
            self.table_tasks.insert_rows(0, rowdata=preview_scheduler.graph.dependency_counts)
            self._renumber_table(self.table_tasks)
            self.table_tasks.autofit_columns()

            total = len(preview_scheduler.graph.nodes())
            self.total_var.set(total)
            self.passed_var.set(0)
            self.failed_var.set(0)
            self.skipped_var.set(0)
            self.tasks_total_var.set(total)
            self.queued_var.set(total)
            self.table_run.delete_rows()
            self.progress.configure(maximum=total)
            self.progress_var.set(0)
            self.percent_var.set('0%')
            self.duration_var.set(f'Loaded {total} tasks from {Path(path).name}')

        except SystemExit as e:
            messagebox.showerror('Load Failed', str(e))
            return

    def open_state(self):
        path = filedialog.askopenfilename(
            title='Select a file',
            filetypes=[
                ('JSON files', '*.json'),
            ],
        )
        if not path:
            return

        self.notebook.select(0)
        self._load_state_from_json(path)
        self.duration_var.set(f'Loaded state from {Path(path).name}')

    def on_scheduler_start(self, meta):
        self._uiqueue_put(self._on_scheduler_start_ui, meta)

    def on_task_run(self, task_name, thread_name):
        self._uiqueue_put(self.on_task_run_ui, task_name, thread_name)

    def on_task_done(self, task_name, thread_name, status, count, total):
        self._uiqueue_put(self.on_task_done_ui, task_name, thread_name, status, count, total)

    def on_scheduler_done(self, summary):
        self._uiqueue_put(self.on_scheduler_done_ui, summary)

    def _on_scheduler_start_ui(self, meta):
        self._set_running_ui(True)
        self.duration_var.set('')
        self.progress_var.set(0)
        self.percent_var.set('0%')

    def on_task_run_ui(self, task_name, thread_name):
        thread_number = _get_thread_number(thread_name)
        if thread_number is not None:
            self.active_var.set(self.active_var.get() + 1)
            self.queued_var.set(max(0, self.queued_var.get() - 1))
            children = self.table_threads.view.get_children('')
            if thread_number >= len(children):
                return
            iid = children[thread_number]
            self.table_threads.view.item(iid, values=(thread_name, task_name))

    def on_task_done_ui(self, task_name, thread_name, status, count, total):
        key = str(status.value).upper()
        icon = self._status_icons.get(key)
        self.table_run.insert_row(index=0, values=(count, task_name,))
        iid = self.table_run.view.get_children('')[0]
        self.table_run.view.item(iid, image=icon)
        # highlight row that was just inserted
        tv = self.table_run.view
        tv.selection_set(iid)
        tv.focus(iid)
        tv.see(iid)

        if key == 'PASSED':
            self.passed_var.set(self.passed_var.get() + 1)
        elif key == 'FAILED':
            self.failed_var.set(self.failed_var.get() + 1)
        elif key == 'SKIPPED':
            self.skipped_var.set(self.skipped_var.get() + 1)

        thread_number = _get_thread_number(thread_name)
        if thread_number is not None:
            self.active_var.set(self.active_var.get() - 1)
            self.closed_var.set(self.closed_var.get() + 1)
            iid = self.table_threads.view.get_children('')[thread_number]
            self.table_threads.view.item(iid, values=(thread_name, ''))
        else:
            self.closed_var.set(self.closed_var.get() + 1)
            self.queued_var.set(max(0, self.queued_var.get() - 1))

        # progress
        self.progress_var.set(count)
        pct = int((count / total) * 100) if total else 0
        self.percent_var.set(f'{pct}%')

    def on_scheduler_done_ui(self, summary):
        self._set_running_ui(False)
        duration = summary['duration']
        self.duration_var.set(f'Completed in {duration:.2f}s')

    def _set_running_ui(self, running):
        self.spinbox_workers.configure(state='disabled' if running else 'enabled')
        self.run_button.configure(state='disabled' if running else 'enabled')
        if running:
            self._show_running_footer()
        else:
            self._hide_running_footer()

    def run_tasks(self):
        if getattr(self, '_running', False) or not hasattr(self, '_marked_functions'):
            return

        self.notebook.select(3)

        total = self.total_var.get()
        self._reset_for_run(total)

        self._running = True

        def runner():
            try:
                state = self._build_run_state()
                self.scheduler = Scheduler(
                    workers=int(self.workers.get()),
                    state=state,
                    setup_logging=self.log_all_var.get(),
                    add_stream_handler=False,
                    skip_dependents=self.skip_dependents_var.get(),
                    clear_results_on_start=True,
                    verbose=False,
                )
                register_functions(self.scheduler, self._marked_functions, None, False)
                self.scheduler.on_scheduler_start(self.on_scheduler_start)
                self.scheduler.on_task_run(self.on_task_run)
                self.scheduler.on_task_done(self.on_task_done, len(self.scheduler.graph.nodes()))
                self.scheduler.on_scheduler_done(self.on_scheduler_done)
                self.scheduler.start()
            except (Exception, SystemExit) as e:
                # surface the error on the UI thread
                self._uiqueue_put(messagebox.showerror, 'Run failed', str(e))
                self._uiqueue_put(self._set_running_ui, False)
            finally:
                self._running = False
                print('state' + json.dumps(self.scheduler.sanitized_state, indent=2, default=str))

        threading.Thread(target=runner, name='tdrun-scheduler', daemon=True).start()

    def _build_run_state(self):
        state = self.get_state_from_table()
        _maybe_call_setup_state(self._module, state)
        return state

    def _uiqueue_put(self, fn, *args):
        self._uiqueue.put((fn, args))

    def _poll_uiqueue(self):
        try:
            while True:
                fn, args = self._uiqueue.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        # schedule next poll
        self.after(50, self._poll_uiqueue)

    def _make_swatch(self, color, size=12):
        img = tk.PhotoImage(width=size * 2, height=size)
        img.put(color, to=(0, 0, size * 2, size))
        return img

    def hide_all_hscrollbars(self):
        for t in (self.table_state, self.table_tasks, self.table_threads, self.table_run):
            hide_tableview_hscroll(t)

    def _make_counter(self, parent, title, var, bootstyle='secondary'):
        card = tb.Frame(
            parent,
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
            bootstyle=bootstyle
        )
        card.pack_propagate(False)
        card.pack(side=LEFT, padx=4, pady=4)
        tb.Label(
            card,
            text=title,
            font=('Segoe UI', 10, 'bold'),
            bootstyle='inverse-' + bootstyle,
            anchor='w'
        ).pack(anchor='w')
        tb.Label(
            card,
            textvariable=var,
            font=('Segoe UI', 14, 'bold'),
            bootstyle='inverse-' + bootstyle,
            anchor='w'
        ).pack(anchor='w')

    def _renumber_table(self, table: Tableview, start=1):
        for i, iid in enumerate(table.view.get_children(""), start=start):
            table.view.item(iid, text=str(i))

    def _show_running_footer(self):
        if not self.running_frame.winfo_ismapped():
            self.running_frame.pack(side=LEFT, fill=X, expand=True)
        self.percent_var.set('0%')

    def _hide_running_footer(self):
        if self.running_frame.winfo_ismapped():
            self.running_frame.pack_forget()
        self.percent_var.set('')
        self.progress_var.set(0)

    def _load_state_from_json(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f'Failed to load JSON file: {path}') from e

        if not isinstance(data, dict):
            raise ValueError('State JSON must be an object (key/value pairs)')

        if any(k.startswith('_') for k in data.keys()):
            raise ValueError('State file keys cannot start with an underscore (_) character')

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            self._upsert_state_row(key, value_str, Path(path).name)

        self.table_state.autofit_columns()

    def get_state_from_table(self):

        def _parse_value(value):
            try:
                return json.loads(value)
            except Exception:
                return value

        state = {}
        tv = self.table_state.view
        for iid in tv.get_children(''):
            key, value = tv.item(iid, 'values')[:2]
            state[key] = _parse_value(value)
        return state

    def _upsert_state_row(self, key, value_str, source):
        tv = self.table_state.view
        for iid in tv.get_children(''):
            k = tv.item(iid, 'values')[0]
            if k == key:
                tv.item(iid, values=(key, value_str, source, ''))
                return
        self.table_state.insert_row(index='end', values=(key, value_str, source, ''))

    def show_about(self):
        version = importlib.metadata.version("thread-order")
        messagebox.showinfo(
            title="About tdrun-ui",
            message=(
                "tdrun-ui\n"
                "Windows UI for thread-order\n"
                "A lightweight framework for running functions concurrently across multiple "
                " threads while maintaining a defined execution order.\n\n"
                "Author: Emilio Reyes\n"
                "Email: soda480@gmail.com\n\n"
                "Package: thread-order[ui]\n"
                f"Version: {version}\n"
                "https://pypi.org/project/thread-order/\n\n"
            )
        )

    def _reset_for_run(self, total):
        # counters
        self.total_var.set(total)
        self.passed_var.set(0)
        self.failed_var.set(0)
        self.skipped_var.set(0)

        self.queued_var.set(total)
        self.active_var.set(0)
        self.closed_var.set(0)

        # progress/footer
        self.progress.configure(maximum=total)
        self.progress_var.set(0)
        self.percent_var.set('0%')
        self.duration_var.set('')

        # tables
        self.table_run.delete_rows()

        # clear thread assignments
        tv = self.table_threads.view
        for iid in tv.get_children(''):
            thread_name, *_ = tv.item(iid, 'values')
            tv.item(iid, values=(thread_name, ''))

def _maybe_call_setup_state(module, initial_state):
    """ invoke module-level setup_state(initial_state) if defined
    """
    setup_state_function = getattr(module, 'setup_state', None)
    if callable(setup_state_function):
        setup_state_function(initial_state)

def hide_tableview_hscroll(table):
    for child in table.winfo_children():
        # Only kill the scrollbar that is directly under the tableview container
        if child.winfo_class() == "TScrollbar":
            # This is the outer scrollbar (your horizontal one)
            child.pack_forget()

def _get_thread_number(thread_name, thread_prefix='thread_'):
    """ Extract the thread index from a thread name.
    """
    if not thread_name.startswith(thread_prefix):
        return
    try:
        return int(thread_name[len(thread_prefix):])
    except ValueError:
        return

def center_window(win, width=None, height=None):
    win.update_idletasks()
    w, h = width, height
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    win.geometry(f'{w}x{h}+{x}+{y}')
    win.update_idletasks()

def _tk_report_callback_exception(self, exc, val, tb):
    messagebox.showerror('Error', f'{exc.__name__}: {val}')

def main():
    app = tb.Window(themename='cosmo', title='tdrun-ui', size=(600, 600), resizable=(False, True))
    app.report_callback_exception = _tk_report_callback_exception.__get__(app, tb.Window)
    center_window(app, 600, 600)

    tkfont.nametofont('TkDefaultFont').configure(family='Segoe UI', size=9)
    tkfont.nametofont('TkTextFont').configure(family='Segoe UI', size=9)
    tkfont.nametofont('TkHeadingFont').configure(family='Segoe UI', size=9)

    # optional: room for the new font
    app.style.configure('Treeview', rowheight=28)

    menu_font = tkfont.Font(family='Segoe UI', size=9)
    app.option_add('*Menu.Font', menu_font)

    Runner(app)
    app.mainloop()

if __name__ == '__main__':
    main()
