#!/usr/bin/env python3

import os
import sys
sys.path.append("../lib")

from BinanceAPI import *
import time
from datetime import date, timedelta, datetime
import calendar
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

if len(sys.argv) != 5:
    print('usage: coinA coinB year/month HourInterval')
    sys.exit(1)


hourinterval = sys.argv[4]
bapi = BinanceAPI("", "")
coinA = sys.argv[1]
coinB = sys.argv[2]
symbol = coinB + coinA
rootdir = "."

def toTimestampDate(s):
    return time.mktime(datetime.strptime(s, "%Y-%m-%d").timetuple())

def computeDF(klines):
    klines = [[pd.Timestamp(int(x[0]/1000), unit='s', tz='Asia/Hong_Kong'), \
            float(x[1]), \
            float(x[2]), \
            float(x[3]), \
            float(x[4]), \
            float(x[5]), \
            float(x[6]), \
            float(x[7]), \
            float(x[8]), \
            float(x[9]), \
            float(x[10])] \
            for x in klines]
    df = pd.DataFrame(np.array(klines), \
        columns=['Timestamp', 'open', 'high', 'low', 'close', \
        'volume', 'close_time', 'quote_asset_volume', 'num_trades', \
        'take_buy_base_vol', 'take_buy_quote_vol'])
    df = df.set_index("Timestamp")
    return df

# Get candles for a particular range of days
def getHourKlines(sdate, edate):
    st = int(toTimestampDate(sdate) * 1000)
    et = int(toTimestampDate(edate) * 1000) - 1
    kls = bapi.getKlines(symbol, hourinterval, stime=st, \
        etime=et, limit=1000)
    finalDf = computeDF(kls)
    return finalDf

# Save dataframe into a parquet file
def saveParquet(df, path2parquet):
    df.to_parquet(path2parquet)


def genMonth(month):
    month = datetime.strptime(month, "%Y-%m-%d")
    nextmonth = month + relativedelta(months=1)
    sdate = month.strftime("%Y-%m-%d")
    edate = nextmonth.strftime("%Y-%m-%d")
    df = getHourKlines(sdate, edate)
    (yy, mm, dd) = sdate.split("-")
    logfile = "%s-%s.parquet" % (yy, mm)
    dirname = os.path.join(rootdir, "hourdata/%s/%s/%s" % \
            (symbol, hourinterval, yy))
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    path2parquet = "%s/%s" % (dirname, logfile)
    print("saving parquet to %s" % path2parquet)
    saveParquet(df, path2parquet)
    
def getAllFiles(folder):
    allFiles = []
    for filename in os.listdir(folder):
        allFiles.append(filename.split(".")[0])
    return allFiles

def genYear(yy):
    yy = int(yy)
    num_months = 12 
    months = ["{:04d}-{:02d}-01".format(yy, mm) \
        for mm in range(1, num_months+1)]
    for i in range(len(months)):
        month = months[i]
        monthDay = datetime.strptime(month, "%Y-%m-%d")
        (yy, mm, dd) = month.split("-")
        dirname = os.path.join(rootdir, "hourdata/%s/%s/%s" % \
                (symbol, hourinterval, yy))
        filename = "%s-%s" % (yy, mm)
        if os.path.exists(dirname):
            files = getAllFiles(dirname)
            if filename in files:
                print("Month %s has already been processed. Skip..." % filename)
                continue
        if not os.path.exists(dirname):
            print("=== [%s] Processing %s ===" % (yy, month))
            genMonth(month)
        elif date.today() <= monthDay.date():
            print("%s >= today. Break" % monthDay)
            break
        else:
            print("=== Processing %s ===" % month)
            genMonth(month)
        time.sleep(2)

if len(sys.argv[3]) == 4:
    genYear(sys.argv[3])
else:
    genMonth("%s-%s" % (sys.argv[3], "01"))
