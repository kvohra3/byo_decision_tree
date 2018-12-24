import datetime
import requests
import pandas as pd

def download_data(verbose=True):
    """
    Pull data from public servers.

    Parameters
    -----------
    verbose: boolean

    Returns
    -------
    trips
    """

    # Harvard Square, Red line stop, outbound
    harvard_stop_id = '70068'
    # JFK / UMass, Red line stop, inbound
    jfk_stop_id = '70086'

    # Gather trip data from a time window from each day,
    # over many days.
    start_time = datetime.time(7, 0)
    end_time = datetime.time(10, 0)
    start_date = datetime.date(2015, 5, 1)
    end_date = datetime.date(2018, 5, 1)

    TTravelURL = "http://realtime.mbta.com/developer/api/v2.1/traveltimes"
    TKey = "?api_key=wX9NwuHnZU2ToO7GmGR9uw"
    TFormat = "&format=json"
    from_stop = "&from_stop=" + str(jfk_stop_id)
    to_stop = "&to_stop=" + str(harvard_stop_id)

    # Cycle through all the days

    i_day = 0
    trips = []
    while True:
        check_date = start_date + datetime.timedelta(days=i_day)
        if check_date > end_date:
            break
        # Formulate the query.
        from_time = datetime.datetime.combine(check_date, start_time)
        to_time = datetime.datetime.combine(check_date, end_time)
        TFrom_time = "&from_datetime=" + str(int(from_time.timestamp()))
        TTo_time = "&to_datetime=" + str(int(to_time.timestamp()))

        SRequest = "".join([
            TTravelURL,
            TKey,
            TFormat,
            from_stop, to_stop,
            TFrom_time, TTo_time
        ])
        s = requests.get(SRequest)
        s_json = s.json()
        for trip in s_json['travel_times']:
            trips.append({
                'dep': datetime.datetime.fromtimestamp(
                    float(trip['dep_dt'])),
                'arr': datetime.datetime.fromtimestamp(
                    float(trip['arr_dt']))})
        if verbose:
            print(check_date, ':', len(s_json['travel_times']))

        i_day += 1

    return trips

def calculate_arrival_times(
    trips,
    harvard_walk=4,
    jfk_walk=6,
    target_hour=9,
    target_minute=0,
    train_dep_min=-60,
    train_dep_max=0,
    debug=False,
):
    """
    Based on the downloaded trips data, calculate the arrival times
    that each possible departure time would result in.

    The kwargs above default to our specific use case (work starts
    at 9:00, it takes 6 minutes to walk to JFK, and it takes
    4 minutes to walk from Harvard Square to work)

    Parameters
    ----------
    harvard_walk, jfk_walk: int
        The time in minutes it takes to make these walks.
    trips: DataFrame
    target_hour, target_minute: int
        The time work starts is target_hour:target_minute.
    train_dep_min, train_dep_max: int
        The time, relative to the target, in minutes when the train departs
        from JFK. Negative number means minutes **before** the target.
        Min and max define the time window under consideration.
    debug: boolean
    """
    minutes_per_hour = 60
    date_format = '%Y-%m-%d'
    trips_expanded = []
    for raw_trip in trips:
        rel_dep = (
            minutes_per_hour * (raw_trip['dep'].hour - target_hour) +
            (raw_trip['dep'].minute - target_minute))
        rel_arr = (
            minutes_per_hour * (raw_trip['arr'].hour - target_hour) +
            (raw_trip['arr'].minute - target_minute))

        if rel_dep > train_dep_min and rel_dep <= train_dep_max:
            new_trip = {
                'departure': rel_dep,
                'arrival': rel_arr,
                'date': raw_trip['dep'].date(),
            }
            trips_expanded.append(new_trip)

    trips_df = pd.DataFrame(trips_expanded)

    if debug:
        print(trips_df)
    #     tools.custom_scatter(trips_df['departure'], trips_df['arrival'])

    # door_arrivals = {}
    # # Create a new DataFrame with minute-by-minute predictions
    # for day in trips_df.loc[:, 'date'].unique():
    #     datestr = day.strftime(date_format)
    #     trips_today = trips_df.loc[
    #         trips_df.loc[:, 'date'] == day, :]
    #     door_arrival = np.zeros(train_dep_max - train_dep_min)
    #     for i_row, door_departure in enumerate(
    #             np.arange(train_dep_min, train_dep_max)):
    #         # Find the next train departure time.
    #         station_arrival = door_departure + jfk_walk
    #         try:

    #             idx = trips_today.loc[
    #                 trips_today.loc[:, 'departure'] >=
    #                 station_arrival, 'departure'].idxmin()
    #             door_arrival[i_row] = (
    #                 trips_today.loc[idx, 'arrival'] + harvard_walk)
    #         except Exception:
    #             # Fill with not-a-numbers (NaN)
    #             door_arrival[i_row] = np.nan

    #     door_arrivals[datestr] = pd.Series(
    #         door_arrival, index=np.arange(train_dep_min, train_dep_max))
    # arrival_times_df = pd.DataFrame(door_arrivals)
    # return arrival_times_df

if __name__ == '__main__':
    """
    Arguments
    ---------
    strings
        Each command line argument is assumed to be a date string
        of the form YYYY-MM-DD
    """
    trips = download_data()
    arrival_times_df = calculate_arrival_times(trips, debug=True)
    print(trips)