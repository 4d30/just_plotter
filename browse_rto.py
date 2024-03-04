#!/bin/env python

import os
import re
import itertools as its
import configparser


def browse(rto_mount, control, subject=None):
    p_control = re.compile(control)
    config = configparser.ConfigParser()
    config.read("./config.ini")
    roots = {'val': "Corbett/Data/StudyData/sensor_original",
             'int': "Project Corbett - Intervention/Data_Assessments/Study_Data"
             }
    sub_pats = {'val': r'[A-Z]{2}[0-9]{3}',
                'int': r'[0-9]{3}-[0-9]+'}
    for arm in roots.keys():
        study_data = os.path.join(rto_mount, roots[arm])
        sub_dirs = map(os.path.join,
                       its.repeat(study_data),
                       os.listdir(study_data))
        sub_dirs = filter(os.path.isdir, sub_dirs)
        sub_pat = sub_pats[arm]
        sub_pat = re.compile(sub_pat)
        sub_dirs = filter(sub_pat.search, sub_dirs)
        if subject:
            sub_dirs = filter(lambda x: subject in x, sub_dirs)
        for sub_dir in sub_dirs:
            tp_dirs = map(os.path.join,
                          its.repeat(sub_dir),
                          os.listdir(sub_dir))
            tp_dirs = filter(os.path.isdir, tp_dirs)
            for tp_dir in tp_dirs:
                tp_path = os.path.join(sub_dir, tp_dir)
                for root, dirs, files in os.walk(tp_path):
                    for file in files:
                        if p_control.search(file):
                            yield os.path.abspath(os.path.join(root, file))


def browse_shrds(rto_mount, subject=None):
    for shrd in browse(rto_mount, r'.*\.shrd', subject):
        yield shrd


def browse_sensors(rto_mount, subject=None):
    for sensor in browse(rto_mount, r'.*accl_gyro_raw.csv', subject):
        yield sensor


def browse_events(rto_mount, subject=None):
    for event in browse(rto_mount, r'.*ECF.csv', subject):
        yield event


def main():
    config = configparser.ConfigParser()
    config.read("./config.ini")
    rto_mount = config['paths']['rto']
    for link in browse_events(rto_mount):
        print(link)
    return None


if __name__ == '__main__':
    main()
