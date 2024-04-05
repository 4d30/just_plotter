#!/bin/env python

import os
import sys
import csv
import json
import random
import configparser
from array import array
import math
import operator as op
import itertools as its
import functools as fts
import statistics as sts
import multiprocessing as mp

import matplotlib.pyplot as plt

import browse_rto as rto

all_sensors = (
    'Chest',
    'LeftUpperArm',
    'LeftWrist',
    'LeftUpperLeg',
    'LeftLowerLeg',
    'RightUpperArm',
    'RightWrist',
    'RightUpperLeg',
    'RightLowerLeg',
    'Head',
    )


def get_file(subj_id, time_point, sensor):
    if not sensor:
        return None
    config = configparser.ConfigParser()
    config.read("config.ini")
    filepattern = '_'.join([subj_id, time_point, sensor])
    file = rto.browse(config['paths']['rto'], filepattern,
                      subject=subj_id)
    file = filter(lambda x: 'accl_gyro_raw' in x, file)
    file = next(file, None)
    return file


def read_csv(file):
    if not file:
        return None
    handle = open(file, 'r')
    data = csv.DictReader(handle)
    data = tuple(data)
    handle.close()
    return data


def spl2files(spl_row):
    subj_id = spl_row['SubjID']
    time_point = spl_row['TimePoint']
    sensors = map(fts.partial, its.repeat(op.itemgetter), all_sensors)
    sensors = map(op.call, sensors)
    sensors = map(op.call, sensors, its.repeat(spl_row))
    sensors = tuple(sensors)
    files = map(get_file, its.repeat(subj_id),
                its.repeat(time_point),
                sensors)

    return files


def get_handles(spl_row):
    files = spl2files(spl_row)
    pool = mp.Pool()
    data = pool.map(read_csv, files)
    pool.close()
    pool.join()
    return data


def read_time(data):
    if not data:
        return array('f', [])
    config = configparser.ConfigParser()
    config.read("config.ini")
    resample_rate = config.getint('params', 'resample_rate_hz')
    resample_rate = op.truediv(208, resample_rate)
    resample_rate = int(round(resample_rate, 0))
    header = tuple(data[0].keys())
    foo = map(op.methodcaller('lower'), data[0].keys())
    foo = tuple(foo)
    is_time = map(op.contains, foo, its.repeat('time'))
    col = its.compress(foo, is_time)
    col = next(col)
    col = header[foo.index(col)]
    data = map(op.itemgetter(col), data)
    data = map(float, data)
    data = map(op.truediv, data, its.repeat(1000))
    data = array('f', data)[::resample_rate]
    return data


def square(num):
    return math.pow(num, 2)


def read_timeseries(instrument_axis_handle_config):
    instrument, axis, handle, config = instrument_axis_handle_config
    if not handle:
        return array('f', [])
    resample_rate = config.getint('params', 'resample_rate_hz')
    resample_rate = op.truediv(208, resample_rate)
    resample_rate = int(round(resample_rate, 0))
    header = tuple(handle[0].keys())
    foo = map(op.methodcaller('lower'), handle[0].keys())
    foo = tuple(foo)
    is_instrument = map(op.contains, foo, its.repeat(instrument))
    is_instrument = tuple(is_instrument)
    mag_cols = its.compress(header, is_instrument)
    mag = map(op.itemgetter(*mag_cols), handle)
    mag = map(map, its.repeat(float), mag)
    mag = map(map, its.repeat(square), mag)
    mag = map(sum, mag)
    mag = map(math.sqrt, mag)
    mag = array('f', mag)[::resample_rate]
    is_axis = map(op.contains, foo, its.repeat(axis))
    col = map(op.and_, is_instrument, is_axis)
    col = its.compress(foo, col)
    col = next(col, None)
    col = header[foo.index(col)]
    data = map(op.itemgetter(col), handle)
    data = map(float, data)
    data = array('f', data)[::resample_rate]
    return data, mag


def scale(data, ii):
    abss = map(abs, data)
    vert_offset = 2*ii
    try:
        minabs = min(abss)
    except ValueError:
        breakpoint()
    abss = map(abs, data)
    maxabs = max(abss)
    data = map(op.sub, data, its.repeat(minabs))
    data = map(op.truediv, data, its.repeat(maxabs))
    data = map(op.add, data, its.repeat(vert_offset))
    data = array('f', data)
    return data


def plot_serieses(args):
    ii, jj, axs, sen, times, timeseries = args
    if sen not in timeseries:
        return None
    data = timeseries[sen]
    if not data:
        return None
    data = scale(timeseries[sen], jj)
    axs[ii].scatter(times[sen], data, s=1, alpha=0.5)
    axs[ii].annotate(sen, (times[sen][-1], data[0] - 0.25))
    return None


def user_input(inp):
    os.system('clear')
    match inp:
        case 'n':
            return 'n'
        case 'd':
            return 'd'
        case 'q':
            return 'q'
        case _:
            usr_input = input("Enter input:\n(n)ext axis\n(d)one w session\n(q)uit\n")
            return user_input(usr_input)


def load_ecf(spl_row):
    config = configparser.ConfigParser()
    config.read("config.ini")
    filepattern = '_'.join([spl_row['SubjID'], spl_row['TimePoint'], 'ECF'])
    ecf = rto.browse(config['paths']['rto'], filepattern,
                     subject=spl_row['SubjID'])
    ecf = next(ecf, None)
    if not ecf:
        return None
    ecf_handle = open(ecf, 'r')
    ecf = csv.DictReader(ecf_handle)
    ecf = tuple(ecf)
    return ecf


def filter_events(pair):
    a = op.ne(pair[0]['Event'], '8')
    b = op.eq(pair[1]['Event'], '8')
    return op.and_(a, b)


def lookup_fw_version(file, fw_versions):
    if not file:
        return None
    file = os.path.basename(file)
    fw_version = filter(lambda x: x['sens'] == file, fw_versions)
    fw_version = next(fw_version, {})
    if 'fw_ver' in fw_version:
        version = fw_version['fw_ver']
    else:
        version = None
    return version


def test_489_condition(file, fw_versions):
    if not file:
        return None
    fw_version = lookup_fw_version(file, fw_versions)
    is_ammonitor = op.eq(fw_version, 'N/A')
    is_S = op.contains(file, '_S')
    return op.and_(is_ammonitor, is_S)


def do_489_tests(spl_row):
    config = configparser.ConfigParser()
    config.read("config.ini")
    fw_versions_handle = config['paths']['fw_versions']
    fw_versions_handle = open(fw_versions_handle, 'r')
    all_fw_versions = json.load(fw_versions_handle)
    fw_versions_handle.close()
    files = spl2files(spl_row)
    add_489 = map(test_489_condition, files, its.repeat(all_fw_versions))
    add_489 = tuple(add_489)
    return add_489


def get_initials(initials):
    if not initials:
        user_input = input("Enter your initials:\n")
        user_input = user_input.strip().upper()
        return get_initials(user_input)
    return initials


def mark_done(spl_row, initials):
    config = configparser.ConfigParser()
    config.read("config.ini")
    file = config['paths']['viewed_sessions']
    if os.path.exists(file):
        handle = open(file, 'a')
    else:
        handle = open(file, 'w')
    write = csv.writer(handle)
    write.writerow([spl_row['SubjID'], spl_row['TimePoint'], initials])
    handle.flush()
    handle.close()
    return None


def crank_handle(spl, initials, contnue, debug=False):
    if contnue:
        spl_row = next(spl)
        contnue = plot_spl_row(spl_row, initials, debug)
        return crank_handle(spl, initials, contnue, debug)
    else:
        return None


def plot_spl_row(spl_row, initials, debug=False):
    config = configparser.ConfigParser()
    config.read("config.ini")
    ecf = load_ecf(spl_row)
    handles = get_handles(spl_row)
    add_489 = do_489_tests(spl_row)
    instuments = its.cycle(('(g)', '(dps)',))
    axes = its.cycle(('z(', 'x(', 'y('))

    times = map(read_time, handles)
    times = zip(all_sensors, times)
    times = dict(times)
    max_time = times.values()
    max_time = filter(bool, max_time)
    max_time = map(max, max_time)
    max_time = max(max_time)
    pool = mp.Pool()
    while True:
        fig, axs = plt.subplots(3, sharex=True, figsize=(10, 5))
        fig.supxlabel('Time (s)')
        for ii, inst in enumerate(instuments):
            if ii > 1:
                break
            for pair in filter(filter_events, its.pairwise(ecf)):
                event = pair[0]['Event']
                t0 = float(pair[0]['Sensor Time(ms)'])/1000
                t1 = float(pair[1]['Sensor Time(ms)'])/1000
                color = ''.join(['C', event])
                axs[ii].axvspan(t0, t1, alpha=0.5, color=color)
            axis = next(axes)
            args = zip(its.repeat(inst), its.repeat(axis), handles,
                       its.repeat(config))
            if debug:
                timeseries = map(read_timeseries, args)
                timeseries = tuple(timeseries)
            else:
                timeseries = pool.map(read_timeseries, args)
            timeseries = zip(all_sensors, timeseries)
            timeseries = dict(timeseries)
            args = zip(its.repeat(ii),
                       range(len(all_sensors)),
                       its.repeat(axs),
                       all_sensors,
                       its.repeat(times),
                       its.repeat(timeseries))
            for jj, sen in enumerate(all_sensors):
                if sen not in timeseries:
                    continue
                data = timeseries[sen]
                axial_data, mag = data
                if not data:
                    continue
                time_vec = times[sen]
                if add_489[jj]:
                    time_vec = map(op.add, times[sen], its.repeat(489/1000))
                    time_vec = array('f', time_vec)
                data = scale(axial_data, jj)
                axs[ii].scatter(time_vec, data, s=1, alpha=0.5)
                axs[ii].set_yticklabels([])
                if '(g)' in inst:
                    axs[ii].set_ylabel('Accl')
                if '(dps)' in inst:
                    axs[ii].set_ylabel('Ang. Vel')
                axs[ii].annotate(sen, (max_time, sts.mean(data)))
                if add_489[jj]:
                    axs[ii].annotate('489', (0, sts.mean(data)))
                if op.eq(inst, '(g)'):
                    axs[2].scatter(time_vec, scale(mag, jj), s=1, alpha=0.5)
                    axs[2].set_yticklabels([])
                    axs[2].set_ylabel('Accel Mag')
                    axs[2].set_xlabel('Time (s)')
        fig.tight_layout()
        fig.suptitle('_'.join([spl_row['SubjID'],
                               spl_row['TimePoint'],
                               axis[0]
                               ]))
        plt.show()
        usr_input = user_input('')
        match usr_input:
            case 'n':
                continue
            case 'd':
                mark_done(spl_row, initials)
                break
            case 'q':
                print("quitting")
                pool.close()
                pool.join()
                return False
    return True


def already_viewed():
    config = configparser.ConfigParser()
    config.read("config.ini")
    file = config['paths']['viewed_sessions']
    if os.path.exists(file):
        handle = open(file, 'r')
        viewed = csv.reader(handle)
        viewed = list(viewed)
    else:
        handle = open(file, 'w')
        handle.close()
        viewed = []
    return viewed


def predicate(viewed, spl_row):
    for v in viewed:
        if v[0] == spl_row['SubjID'] and v[1] == spl_row['TimePoint']:
            return False
    return True


def load_spl():
    config = configparser.ConfigParser()
    config.read("config.ini")
    spl = config['paths']['spl']
    spl_handle = open(spl, 'r')
    spl = csv.DictReader(spl_handle)
    viewed = already_viewed()
    foo = fts.partial(predicate, viewed)
    spl = filter(foo, spl)
    spl = list(spl)
    spl_handle.close()
    random.shuffle(spl)
    spl = iter(spl)
    return spl


def main():
    args = sys.argv
    if '-d' in args:
        debug = True
    else:
        debug = False
    spl = load_spl()
    initials = get_initials('')
    crank_handle(spl, initials, True, debug)
    return None


if __name__ == "__main__":
    main()
