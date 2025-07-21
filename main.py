import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import oracledb
import os
import threading


# -------------------- Oracle DB Connection Form --------------------
class DBConnectionForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Oracle DB Connection")
        self.geometry("340x250")
        self.values = {}

        labels = ["Host", "Port", "Service Name", "Username", "Password"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            entry = tk.Entry(self, width=30, show="*" if "Password" in label else "")
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[label.lower().replace(" ", "_")] = entry

        tk.Button(self, text="Connect", command=self.on_submit).grid(row=6, column=0, columnspan=2, pady=15)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()
        self.resizable(False, False)

    def on_submit(self):
        self.values = {k: e.get().strip() for k, e in self.entries.items()}
        if all(self.values.values()):
            self.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    def on_close(self):
        self.values = None
        self.destroy()


# -------------------- Progress Bar Dialog --------------------
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, total_records):
        super().__init__(parent)
        self.title("Processing Records")
        self.geometry("360x120")
        self.resizable(False, False)
        self.total = total_records

        tk.Label(self, text="Progress").pack(pady=(15, 5))

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self, maximum=self.total, variable=self.progress_var, length=300)
        self.progress.pack(pady=5)

        self.status_label = tk.Label(self, text="")
        self.status_label.pack(pady=(5, 15))

        self.grab_set()

    def update_progress(self, current):
        self.progress_var.set(current)
        self.status_label.config(text=f"Processed {current} of {self.total}")
        self.update_idletasks()


# -------------------- Oracle DB Connection --------------------
def connect_to_oracle(host, port, service_name, username, password):
    try:
        dsn = f"{host}:{port}/{service_name}"
        conn = oracledb.connect(user=username, password=password, dsn=dsn, encoding="UTF-8")
        return conn
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect:\n{e}")
        return None


# -------------------- Query Functions --------------------
def get_customer_ref(conn, user_id):
    try:
        with conn.cursor() as cursor:
            quoted_user = f"'{user_id}'"
            cursor.execute(f"SELECT customer_ref FROM v_nonvzw_customer WHERE userid = {quoted_user}")
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error fetching customer_ref for {user_id}: {e}")
        return None


def get_latest_subscription(conn, customer_ref):
    try:
        with conn.cursor() as cursor:
            quoted_ref = f"'{customer_ref}'"
            cursor.execute(f"""
                SELECT start_date, end_date FROM (
                    SELECT start_date, end_date
                    FROM scm_subscription
                    WHERE customer_number = {quoted_ref}
                    ORDER BY CASE WHEN end_date IS NULL THEN 1 ELSE 0 END DESC, end_date DESC
                )
                WHERE ROWNUM = 1
            """)
            result = cursor.fetchone()
            return result if result else (None, None)
    except Exception as e:
        print(f"Error fetching subscription for {customer_ref}: {e}")
        return (None, None)


# -------------------- Processing Thread --------------------
def process_file_threaded(file_path, user_id_column, conn, progress, root):
    try:
        is_excel = file_path.endswith(".xlsx")
        df = pd.read_excel(file_path) if is_excel else pd.read_csv(file_path)

        total_records = len(df)
        status_list, start_list, end_list = [], [], []

        for i, user_id in enumerate(df[user_id_column]):
            customer_ref = get_customer_ref(conn, user_id)

            if customer_ref:
                start_date, end_date = get_latest_subscription(conn, customer_ref)
                start_str = start_date.strftime("%d-%b-%Y") if start_date else None
                end_str = end_date.strftime("%d-%b-%Y") if end_date else None

                start_list.append(start_str)
                end_list.append(end_str)
                status_list.append("Subscription Canceled" if end_date else "Subscription Active")
            else:
                start_list.append(None)
                end_list.append(None)
                status_list.append("Customer Ref Not Found")

            progress.after(0, lambda i=i+1: progress.update_progress(i))

        df["Subscription_Status"] = status_list
        df["Subscription_Start_Date"] = start_list
        df["Subscription_End_Date"] = end_list

        output_file = os.path.splitext(file_path)[0] + "_updated." + ("xlsx" if is_excel else "csv")
        if is_excel:
            df.to_excel(output_file, index=False)
        else:
            df.to_csv(output_file, index=False)

        conn.close()
        progress.after(0, progress.destroy)
        progress.after(0, lambda: messagebox.showinfo("Success", f"Processed file saved as:\n{output_file}"))
    except Exception as e:
        progress.after(0, progress.destroy)
        messagebox.showerror("Error", str(e))


# -------------------- Main App Workflow --------------------
def gui_app():
    root = tk.Tk()
    root.withdraw()

    # Step 1: DB Form
    conn_form = DBConnectionForm(root)
    root.wait_window(conn_form)
    if not conn_form.values:
        return

    conn = connect_to_oracle(
        conn_form.values["host"],
        conn_form.values["port"],
        conn_form.values["service_name"],
        conn_form.values["username"],
        conn_form.values["password"]
    )
    if not conn:
        return

    # Step 2: File
    file_path = filedialog.askopenfilename(
        title="Select CSV/XLSX file",
        filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
    )
    if not file_path:
        return

    is_excel = file_path.endswith(".xlsx")
    df = pd.read_excel(file_path) if is_excel else pd.read_csv(file_path)

    user_id_column = simpledialog.askstring("User ID Column", f"Enter user_id column from:\n{df.columns.tolist()}")
    if not user_id_column or user_id_column not in df.columns:
        messagebox.showerror("Error", "Invalid or missing user_id column.")
        return

    # Step 3: Show Progress
    progress_win = ProgressDialog(root, total_records=len(df))

    # Step 4: Start Threaded Processing
    thread = threading.Thread(
        target=process_file_threaded,
        args=(file_path, user_id_column, conn, progress_win, root),
        daemon=True
    )
    thread.start()

    root.mainloop()
