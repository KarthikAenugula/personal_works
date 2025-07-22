import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import oracledb
import os
import threading
import time


# ---------------- Oracle Connection Dialog ----------------
class DBConnectionForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Oracle DB Connection")
        self.geometry("360x320")
        self.values = {}

        labels = ["Host", "Port", "Service Name", "Username", "Password", "Subscription Service"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            entry = tk.Entry(self, width=30, show="*" if "Password" in label else "")
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[label.lower().replace(" ", "_")] = entry

        tk.Button(self, text="Connect", command=self.on_submit).grid(row=len(labels), column=0, columnspan=2, pady=15)

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


# ---------------- Processing Progress Dialog ----------------
class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, total_records):
        super().__init__(parent)
        self.title("Processing Records")
        self.geometry("380x160")
        self.resizable(False, False)
        self.total = total_records
        self.start_time = None

        tk.Label(self, text="Progress").pack(pady=(12, 5))
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self, maximum=self.total, variable=self.progress_var, length=300)
        self.progress.pack(pady=6)

        self.status_label = tk.Label(self, text="Processed 0 of 0")
        self.status_label.pack()

        self.time_label = tk.Label(self, text="Estimated time remaining: calculating...")
        self.time_label.pack(pady=(4, 10))

        self.grab_set()

    def update_progress(self, current):
        self.progress_var.set(current)
        self.status_label.config(text=f"Processed {current} of {self.total}")
        self.update_time_remaining(current)
        self.update_idletasks()

    def update_time_remaining(self, current):
        if current == 1:
            self.start_time = time.time()
        elif self.start_time:
            elapsed = time.time() - self.start_time
            avg_time = elapsed / current
            remaining = (self.total - current) * avg_time
            minutes, seconds = divmod(int(remaining), 60)
            self.time_label.config(text=f"Estimated time remaining: {minutes}m {seconds}s")


# ---------------- Oracle Connection ----------------
def connect_to_oracle(host, port, service_name, username, password):
    try:
        dsn = f"{host}:{port}/{service_name}"
        conn = oracledb.connect(user=username, password=password, dsn=dsn, encoding="UTF-8")
        return conn
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to Oracle:\n{e}")
        return None


# ---------------- Bulk Data Fetch Functions ----------------
def fetch_customer_refs(conn, user_ids):
    try:
        with conn.cursor() as cursor:
            chunks = [user_ids[i:i+1000] for i in range(0, len(user_ids), 1000)]
            results = []

            for chunk in chunks:
                query = f"""
                    SELECT userid, customer_ref
                    FROM v_nonvzw_customer
                    WHERE userid IN ({','.join([':{}'.format(i+1) for i in range(len(chunk))])})
                """
                cursor.execute(query, chunk)
                results.extend(cursor.fetchall())

            return {str(row[0]): row[1] for row in results}
    except Exception as e:
        print("Error fetching customer_refs:", e)
        return {}


def fetch_latest_subscriptions(conn, customer_refs, service_name):
    try:
        with conn.cursor() as cursor:
            chunks = [customer_refs[i:i+1000] for i in range(0, len(customer_refs), 1000)]
            results = []

            for chunk in chunks:
                query = f"""
                SELECT * FROM (
                    SELECT customer_number, start_date, end_date,
                           RANK() OVER (PARTITION BY customer_number ORDER BY 
                                CASE WHEN end_date IS NULL THEN 1 ELSE 0 END DESC, end_date DESC) rnk
                    FROM scm_subscription
                    WHERE customer_number IN ({','.join([':{}'.format(i+1) for i in range(len(chunk))])})
                      AND service = :service
                ) WHERE rnk = 1
                """
                cursor.execute(query, chunk + [service_name])
                results.extend(cursor.fetchall())

            return {row[0]: (row[1], row[2]) for row in results}
    except Exception as e:
        print("Error fetching subscriptions:", e)
        return {}


# ---------------- Background Processing ----------------
def process_file_threaded(file_path, user_id_column, conn, progress, root, subscription_service):
    try:
        is_excel = file_path.endswith(".xlsx")
        df = pd.read_excel(file_path) if is_excel else pd.read_csv(file_path)

        total_records = len(df)
        user_ids = df[user_id_column].astype(str).tolist()
        progress.after(0, lambda: progress.update_progress(1))

        # Bulk fetch
        user_to_ref = fetch_customer_refs(conn, user_ids)
        customer_refs = list(set(filter(None, user_to_ref.values())))
        ref_to_subs = fetch_latest_subscriptions(conn, customer_refs, subscription_service)

        # Final list for output
        status_list, start_list, end_list = [], [], []

        for i, user_id in enumerate(user_ids):
            customer_ref = user_to_ref.get(str(user_id))
            start_str = end_str = status = None

            if customer_ref:
                sub = ref_to_subs.get(customer_ref)
                if sub:
                    start_date, end_date = sub
                    start_str = start_date.strftime("%d-%b-%Y") if start_date else None
                    end_str = end_date.strftime("%d-%b-%Y") if end_date else None
                    status = "Subscription Canceled" if end_date else "Subscription Active"
                else:
                    status = "Subscription Not Found"
            else:
                status = "Customer Ref Not Found"

            start_list.append(start_str)
            end_list.append(end_str)
            status_list.append(status)
            progress.after(0, lambda i=i+1: progress.update_progress(i))

        # Append to DataFrame
        df["Subscription_Status"] = status_list
        df["Subscription_Start_Date"] = start_list
        df["Subscription_End_Date"] = end_list

        # Save file
        output_file = os.path.splitext(file_path)[0] + "_updated." + ("xlsx" if is_excel else "csv")
        if is_excel:
            df.to_excel(output_file, index=False)
        else:
            df.to_csv(output_file, index=False)

        conn.close()

        def on_done():
            progress.destroy()
            messagebox.showinfo("Success", f"Processed file saved as:\n{output_file}")
            root.quit()
            root.destroy()

        progress.after(0, on_done)

    except Exception as e:
        progress.after(0, progress.destroy)
        root.quit()
        root.destroy()
        messagebox.showerror("Error", str(e))


# ---------------- Main GUI App ----------------
def gui_app():
    root = tk.Tk()
    root.withdraw()

    form = DBConnectionForm(root)
    root.wait_window(form)
    if not form.values:
        return

    conn_data = form.values
    conn = connect_to_oracle(
        conn_data["host"],
        conn_data["port"],
        conn_data["service_name"],
        conn_data["username"],
        conn_data["password"]
    )
    if not conn:
        return

    subscription_service = conn_data["subscription_service"]

    # File Load
    file_path = filedialog.askopenfilename(
        title="Select Excel/CSV file", filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
    )
    if not file_path:
        return

    df = pd.read_excel(file_path) if file_path.endswith(".xlsx") else pd.read_csv(file_path)

    user_id_column = simpledialog.askstring("User ID Column", f"Enter user_id column from:\n{df.columns.tolist()}")
    if not user_id_column or user_id_column not in df.columns:
        messagebox.showerror("Error", "Invalid or missing user_id column.")
        return

    progress = ProgressDialog(root, total_records=len(df))

    thread = threading.Thread(
        target=process_file_threaded,
        args=(file_path, user_id_column, conn, progress, root, subscription_service),
        daemon=True
    )
    thread.start()
    root.mainloop()


# ---------------- Run App ----------------
if __name__ == "__main__":
    gui_app()
