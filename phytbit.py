import auth
import datetime
import functools

client_id = "227TSG"
client_secret = "990aeae2c7e7f735dbbd305bc5ae98e5"


if __name__ == '__main__':
    a = auth.OAuth2Server(client_id, client_secret)
    a.browser_authorize()
    # root = tk.Tk()

    user = "-"
    resource = "activities/heart"
    date = datetime.datetime.now()# - datetime.timedelta(days=30)
    period = "1d"
    frequency = "1sec"
    url = f"https://api.fitbit.com/1/user/{user}/{resource}/date/{date.strftime('%Y-%m-%d')}/{period}/{frequency}.json"
    print(url)
    response = a.fitbit.make_request(url)
    data = response["activities-heart-intraday"]["dataset"]
    # print(data["activities-heart-intraday"]["dataset"])
    print(f"avg={sum([item['value'] for item in data]) / len(data):.4}"
          f" max={max([item['value'] for item in data])}"
          f" min={min([item['value'] for item in data])}")
    # print(a.fitbit.time_series("activities/heart", period="max"))
