#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import json
import boto3

import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import timedelta

# GLOBALS SET BY ENVIRONMENT VARIABLES
MONTHS = int(os.environ.get('MONTHS'))
if not MONTHS:
    MONTHS = 3

CURRENT_MONTH = (str(os.environ.get('CURRENT_MONTH')
                     ).strip().lower() == "true")
LAST_MONTH_ONLY = (str(os.environ.get('LAST_MONTH_ONLY')
                       ).strip().lower() == "true")

class QlikCostExplorer:

    def __init__(self, current_month=False, months=12):
        self.reports = []
        self.client = boto3.client('ce')
        self.end = datetime.date.today().replace(day=1)
        self.riend = datetime.date.today()
        if current_month or CURRENT_MONTH:
            self.end = self.riend

        if LAST_MONTH_ONLY:
            # 1st day of month a month ago
            self.start = (datetime.date.today() -
                          relativedelta(months=+1)).replace(day=1)
        else:
            # Default is last Months
            # 1st day of month Months ago
            self.start = (datetime.date.today() -
                          relativedelta(months=+months)).replace(day=1)

        # 1st day of month Months ago
        self.ristart = (datetime.date.today() -
                        relativedelta(months=+months-1)).replace(day=1)

        try:
            self.accounts = self.get_accounts()
            df = pd.DataFrame(self.accounts)
            self.upload_s3(df, 'accounts_list')
        except BaseException:
            logging.exception("Getting Account names failed")
            self.accounts = {}
            
    def upload_s3(self, df, name):
        os.chdir('/tmp')
        df.to_csv(name + '.csv', index=False)
        if os.environ.get('S3_BUCKET'):
            s3 = boto3.client('s3')
            s3.upload_file(
                name + '.csv', os.environ.get('S3_BUCKET'), name + '.csv')

    def get_accounts(self):
        accounts = {}
        client = boto3.client('organizations', region_name='us-east-1')
        paginator = client.get_paginator('list_accounts')
        response_iterator = paginator.paginate()
        for response in response_iterator:
            for acc in response['Accounts']:
                accounts[acc['Id']] = acc
        if os.environ.get('S3_BUCKET'):
            os.chdir('/tmp')
            with open("accounts.json", "w") as outfile:
                outfile.write(accounts)
                s3 = boto3.client('s3')
                s3.upload_file(
                    'accounts.json', os.environ.get('S3_BUCKET'), 'accounts.json')

        return accounts

    def process(self, results, start, end, group_by, metric, granularity):

        time_period = {
            'Start': start.isoformat(),
            'End': end.isoformat()
        }

        response = self.client.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity=granularity,
            Metrics=metric,
            GroupBy=group_by
        )
        if response:
            results.extend(response['ResultsByTime'])
            while 'nextToken' in response:
                next_token = response['nextToken']
                response = self.client.get_cost_and_usage(
                    TimePeriod=time_period,
                    Granularity=granularity,
                    Metrics=[
                        metric,
                    ],
                    GroupBy=group_by,
                    NextPageToken=next_token
                )
                results.extend(response['ResultsByTime'])
                next_token = response['nextToken'] if (
                    'nextToken' in response) else False
        return results

    def create_report(self, name="Default", group_by=[{"Type": "DIMENSION", "Key": "SERVICE"}, ],
                      metrics=['UnblendedCost'],  granularity='MONTHLY', split_time=False):
        results = []
        if split_time == False:
            results = self.process(results, self.start,
                                   self.end, group_by, metrics, granularity)
        else:
            start = self.start
            while start <= self.end:
                end = start + \
                    relativedelta(
                        months=1) if granularity == 'MONTHLY' else start + timedelta(days=1)
                results = self.process(
                    results, start, end, group_by, metrics, granularity)
                start = end
        rows = []
        for r in results:
            for g in r['Groups']:
                row = {'date': r['TimePeriod']['Start']}
                for i in range(len(group_by)):
                    row.update({group_by[i]["Key"]: g["Keys"][i]})
                for metric in metrics:
                    row.update({
                        metric+'_amount': round(float(g['Metrics'][metric]['Amount']), 5),
                        metric+'_unit': g['Metrics'][metric]['Unit'],
                    })
                rows.append(row)
        df = pd.DataFrame(rows)
        self.upload_s3(df, name)


def main_handler(event=None, context=None):
    ce_obj = QlikCostExplorer(current_month=CURRENT_MONTH, months=MONTHS)
    file = open('reports.json')
    reps = json.load(file)
    for e in reps:
        split = "Split" in e.keys() and (
            str(e["Split"]).strip().lower() == "true")
        if "Metric" in e.keys():
            metrics = str(e["Metric"]).split(',')
        else:
            metrics = ['UnblendedCost']
        ce_obj.create_report(name=e["Report"], group_by=e["GroupBy"],
                             granularity=str(e["Granularity"]).upper(), split_time=split, metrics=metrics)


if __name__ == '__main__':
    main_handler()
