import auth
import datetime
import json
import matplotlib.pyplot as plt
import multiprocessing as mp
import os
import sqlite3 as sql
import tkinter as tk

from typing import Dict

FONT = "courier 9"
FITBIT_TIME_FORMAT = "%Y-%m-%d"
SQLITE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

"""
Config must contain:
  "client_id": "CLIENTID",
  "client_secret": "ITSASECRET"
"""
config = json.load(open(os.path.join(os.path.dirname(__file__), "config.json")))


class TkFitBit(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.db = os.path.join(os.path.dirname(__file__), "heart.db")
        conn = sql.connect(self.db)
        conn.execute("CREATE TABLE IF NOT EXISTS heartrate(time DATETIME, bpm INT, UNIQUE(time))")
        conn.commit()
        conn.close()
        self.data = {}
        self.plot = None
        self.menu = tk.Menu(master)
        master.config(menu=self.menu)
        self.menu.add_command(label="Refresh", command=self.get_heart_rate_data)
        self.menu.add_command(label="Reload", command=self.reload_data)
        self.menu.add_command(label="Plot", command=self.make_plot)
        self.header = tk.Label(self, font=FONT, text="   DATE     TIME     BPM  ")
        self.header.pack()
        self.table_frame = tk.Frame(self)
        self.table = tk.Listbox(self.table_frame, font=FONT, height=30, width=25)
        self.table.scroll = tk.Scrollbar(self.table_frame, command=self.table.yview)
        self.table.config(yscrollcommand=self.table.scroll.set)
        self.table.pack(side=tk.LEFT)
        self.table.scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.table_frame.pack()
        self.pack()
        self.reload_data()

    def reload_data(self):
        self.table.delete(0, tk.END)
        conn = sql.connect(self.db)
        self.data = {datetime.datetime.strptime(i[0], SQLITE_TIME_FORMAT): i[1]
                     for i in conn.execute("SELECT * FROM heartrate ORDER BY 'time'")}
        conn.close()
        [self.table.insert(tk.END, f"{i}   {self.data[i]:>3}") for i in self.data]
        self.refresh_plot()

    def make_plot(self):
        self.plot = mp.Process(target=plot_data, args=(self.data,))
        self.plot.start()

    def refresh_plot(self):
        if self.plot is not None:
            self.plot.terminate()
            self.plot.join()
            self.plot = mp.Process(target=plot_data, args=(self.data,))
            self.plot.start()

    def get_heart_rate_data(self):
        auth_server = auth.OAuth2Server(config["client_id"], config["client_secret"])
        auth_server.browser_authorize()
        fitbit = auth_server.fitbit
        user = "-"
        resource = "activities/heart"
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period = "1d"
        frequency = "1sec"
        conn = sql.connect(self.db)
        start_date = conn.execute("SELECT time FROM heartrate ORDER BY time DESC LIMIT 1").fetchone()
        if start_date:
            start_date = datetime.datetime.strptime(start_date[0], SQLITE_TIME_FORMAT)
        else:
            start_date = today - datetime.timedelta(days=30)
        end_date = today
        print(start_date, "-->", end_date)
        response = fitbit.make_request(f"https://api.fitbit.com/1/user/{user}/{resource}/date/"
                                       f"{today.strftime(FITBIT_TIME_FORMAT)}/{period}/{frequency}.json")
        if "activities-heart-intraday" in response:
            if "dataset" in response["activities-heart-intraday"]:
                data = response["activities-heart-intraday"]["dataset"]
                for item in data:
                    t = datetime.datetime.strptime(item["time"], "%H:%M:%S")
                    t = t.replace(year=today.year, month=today.month, day=today.day)
                    item["time"] = t.strftime(SQLITE_TIME_FORMAT)  # SQLITE3's expected DATETIME format
                conn.executemany("INSERT OR REPLACE INTO heartrate VALUES(?, ?)",
                                 [(item['time'], item['value']) for item in data])
            else:
                print("'dataset' not found!")
        else:
            print("'activities-heart-intraday' not found!")
        conn.commit()
        conn.close()
        self.reload_data()

    def destroy(self):
        if self.plot:
            self.plot.terminate()
            self.plot.join()
        super().destroy()


def plot_data(data: Dict[datetime.datetime, int]):
    plt.plot(list(data.keys()), list(data.values()))
    plt.show()

if __name__ == '__main__':
    root = tk.Tk()
    tfb = TkFitBit(root)
    root.mainloop()
    # tfb.get_heart_rate_data()
