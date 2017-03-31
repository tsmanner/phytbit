import auth
import datetime
import os
import sqlite3 as sql
import tkinter as tk

FONT="courier 9"
client_id = "227TSG"
client_secret = "990aeae2c7e7f735dbbd305bc5ae98e5"


class TkFitBit(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.db = os.path.join(os.path.dirname(__file__), "heart.db")
        self.menu = tk.Menu(master)
        master.config(menu=self.menu)
        self.menu.add_command(label="Refresh", command=self.get_heart_rate_data)
        self.menu.add_command(label="Reload", command=self.reload_data)
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
        [self.table.insert(tk.END, f"{i[0]}   {i[1]:>3}")
         for i in conn.execute("SELECT * FROM heartrate ORDER BY 'time'")]
        conn.close()

    def get_heart_rate_data(self):
        auth_server = auth.OAuth2Server(client_id, client_secret)
        auth_server.browser_authorize()
        fitbit = auth_server.fitbit
        user = "-"
        resource = "activities/heart"
        query_date = datetime.datetime.now() - datetime.timedelta(days=1)
        period = "1d"
        frequency = "1sec"
        response = fitbit.make_request(f"https://api.fitbit.com/1/user/{user}/{resource}/date/"
                                       f"{query_date.strftime('%Y-%m-%d')}/{period}/{frequency}.json")
        if "activities-heart-intraday" in response:
            if "dataset" in response["activities-heart-intraday"]:
                data = response["activities-heart-intraday"]["dataset"]
                for item in data:
                    t = datetime.datetime.strptime(item["time"], "%H:%M:%S")
                    t = t.replace(year=query_date.year, month=query_date.month, day=query_date.day)
                    item["time"] = t.strftime("%Y-%m-%d %H:%M:%S")
                conn = sql.connect(self.db)
                conn.execute("CREATE TABLE IF NOT EXISTS heartrate(time DATETIME, bpm INT, UNIQUE(time))")
                conn.executemany("INSERT OR REPLACE INTO heartrate VALUES(?, ?)",
                                 [(item['time'], item['value']) for item in data])
                conn.commit()
                conn.close()
            else:
                print("'dataset' not found!")
        else:
            print("'activities-heart-intraday' not found!")
        self.reload_data()


if __name__ == '__main__':
    root = tk.Tk()
    tfb = TkFitBit(root)
    root.mainloop()
    # tfb.get_heart_rate_data()
