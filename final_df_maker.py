import pandas as pd
import numpy as np
from datetime import datetime, timedelta

window_size = 24 # How long you want your df
event_seperation = 12 # How long between df you define

meanc = 0.1 #mean
thresholdc = 0.2 #threshold

# files can be found per country at https://www.renewables.ninja/
df1 = pd.read_csv('ninja_wind_country_IE_current-merra-2_corrected.csv', skiprows=2)
df2 = pd.read_csv('ninja_pv_country_IE_merra-2_corrected.csv', skiprows=2)

pv = df2['national'].tolist()
onshore = df1['onshore'].tolist()
offshore = df1['offshore'].tolist()
time = df2['time'].tolist()

lists = [onshore, offshore, pv, time]

list_of_events = []
start_dates = [datetime.strptime(time[0], "%Y-%m-%d %H:%M:%S")]

def lm(l,i, len):
    return [lists[l][j] for j in range(i, i + window_size + len)]


def dunelflauten_checker(event, rate):
    if np.mean(event) < rate:
        return True
    else:
        return False


def mean(e1, e2, e3, cutoff):
    if dunelflauten_checker(e1, cutoff) and dunelflauten_checker(e2, cutoff) and dunelflauten_checker(e3, cutoff):
        return True
    else:
        return False


def threshold(e1, e2, e3, ngt):
    if all(all(sub_event < ngt for sub_event in event) for event in [e1, e2, e3]):
        return True
    else:
        return False


def end_chcker(l, thresholdc):
    if l[0] > thresholdc and l[1] > thresholdc and l[2] < thresholdc:
        return "wind"
    if l[0] > thresholdc and l[1] > thresholdc and l[2] > thresholdc:
        return "all"
    if l[0] > thresholdc and l[1] < thresholdc and l[2] < thresholdc:
        return "onshore"
    if l[0] < thresholdc and l[1] > thresholdc and l[2] < thresholdc:
        return "offshore"
    if l[0] < thresholdc and l[1] < thresholdc and l[2] > thresholdc:
        return "pv"
    else:
        return "mix"


for i in range(len(pv) - window_size):

    # find our first period where the potential lies below a defined mean or threshold
    if datetime.strptime(time[i], "%Y-%m-%d %H:%M:%S") not in start_dates:
        if mean(lm(0, i, 0), lm(1, i, 0), lm(2, i, 0), meanc) and threshold(lm(0, i, 0), lm(1, i, 0), lm(2, i, 0), thresholdc):
            j = 0
            egb = 0
            while mean(lm(0, i, j), lm(1, i, j), lm(2, i, j), meanc) and threshold(lm(0, i, j), lm(1, i, j), lm(2, i, j), thresholdc):
                j += 1
                egb = 1
            j = j-egb

            # if we have room left in the dataset, keep looking for and adding more hours
            # if they are below a defined potential
            # once out of hours or above a threshold, add the event to a csv file
            if datetime.strptime(time[i], "%Y-%m-%d %H:%M:%S") <= start_dates[-1] + timedelta(hours=event_seperation):
                endl = (onshore[i + j + window_size], offshore[i + j + window_size], pv[i + j + window_size])
                diff = datetime.strptime(time[i], "%Y-%m-%d %H:%M:%S") - start_dates[-1]
                hours_diff = int(diff.total_seconds() / 3600)
                dt_ij = datetime.strptime(time[i + j + window_size], "%Y-%m-%d %H:%M:%S")
                list_of_events[-1][8] = [(onshore[k], offshore[k], pv[k]) for k in range(i - list_of_events[-1][7] - hours_diff,i + list_of_events[-1][7] + j + window_size + hours_diff)]
                list_of_events[-1][4] = dt_ij.month
                list_of_events[-1][5] = dt_ij.day
                list_of_events[-1][6] = dt_ij.hour
                list_of_events[-1][7] = list_of_events[-1][7] + j + window_size + hours_diff
                list_of_events[-1][-1] = end_chcker(endl, thresholdc)

                for k in range(i - hours_diff, i + window_size + j):
                    start_dates.append(datetime.strptime(time[k], "%Y-%m-%d %H:%M:%S"))

            # if no new hours can be added to the current event, add it to the csv file
            else:
                endl = (onshore[i + j + window_size], offshore[i + j + window_size], pv[i + j + window_size])
                dt_i = datetime.strptime(time[i], "%Y-%m-%d %H:%M:%S")
                dt_ij = datetime.strptime(time[i + j + window_size], "%Y-%m-%d %H:%M:%S")
                list_of_events.append(
                    [dt_i.year, dt_i.month, dt_i.day, dt_i.hour,
                     dt_ij.month, dt_ij.day, dt_ij.hour,
                     j + window_size,
                     [(onshore[k], offshore[k], pv[k]) for k in
                      range(i, i + window_size + j)], end_chcker(endl, thresholdc)])

                for k in range(i, i + window_size + j):
                    start_dates.append(datetime.strptime(time[k], "%Y-%m-%d %H:%M:%S"))


Dunkelflauten = pd.DataFrame(list_of_events,
                             columns=["year", "beginning_month", "beginning_day", "beginning_time", "end_month",
                                      "end_day", "end_time", "duration", "values", "df_end"])

Dunkelflauten.to_csv('Irish_DF(DUR24_ES12_M0.1_T0.1).csv', index=False)
