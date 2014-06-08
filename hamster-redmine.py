#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import argparse
import re

import sqlite3

import datetime as dt
from datetime import datetime, date, timedelta

import gconf

from classes import ProgressBar, Redmine


# Main config will load here
CONFIG = None

# Constants
DEFAULT_DB = os.path.expanduser("~/.local/share/hamster-applet/hamster.db")
DEFAULT_CONFIG = "hamster-redmine.conf"


def load_config(path):
    """
    Loads main config file and
    normalize them if needed
    """

    with open(path, 'r') as f:
        config = eval(f.read())

    if not config["db_path"]:
        config["db_path"] = DEFAULT_DB

    return config

def parse_args():
    """
    CLI arguments parsing

    :return: argparse.Namespace
    """

    # Parse arguments
    parser = argparse.ArgumentParser(description="Synchronize your " \
                                     "hamster-applet with Redmine")
    parser.add_argument("-c", "--config", dest="c", help="Config file path")
    parser.add_argument("-d", "--date", dest="d", \
                        help="Single date or date range in format " \
                        "dd.mm.yyyy or dd.mm.yyyy-dd.mm.yyyy")
    parser.add_argument("-p", "--project", dest="project",\
                        help="Specific project name")
    parser.add_argument("-t", "--tags", dest="t", help="Specific tags " \
                        "separated by commas")

    args = parser.parse_args()

    # Date or date range parsing
    conf = gconf.client_get_default()
    day_start = timedelta( \
              minutes=conf.get_int("/apps/hamster-applet/day_start_minutes"))

    if not args.d:
        today = datetime.combine((datetime.today() - day_start).date(), \
                                 dt.time(0, 0)) + day_start
        args.from_date, args.to_date = today, today
    else:
        dates = map(lambda x: datetime.strptime(x, '%d.%m.%Y') + day_start,
                     args.d.split('-'))
        args.from_date = dates[0]
        args.to_date = dates[1] if len(dates) > 1 else dates[0]

    # Tags parsing
    args.tags = filter(None, args.t.split(",")) if args.t else ()

    return args

def db_connect(file):
    """
    Database connection

    :param file: Path to the database
    :type file: string
    """

    def regexp(expr, item):
        reg = re.compile(expr, re.I)
        return reg.search(item) is not None

    conn = sqlite3.connect(file)
    conn.create_function("REGEXP", 2, regexp)
    conn.row_factory = sqlite3.Row

    return conn.cursor()

def get_time_entries(dbcur, act_date, tags=(), project=''):
    """
    Retrieve time entries from Hamster's database (SQLite3)
    specified by date for 1 full day

    :param dbcur: SQLite3 cursor
    :type dbcur: sqlite3.Cursor
    :param act_date: Activities date
    :type act_date: datetime.datetime
    """

    query = """SELECT {0}
        FROM facts AS f
        LEFT JOIN activities AS a ON f.activity_id = a.id
        LEFT JOIN categories AS c ON a.category_id = c.id
        WHERE {1}
        GROUP BY f.description
        ORDER BY f.start_time"""

    select = ",".join(("a.name", "f.description",
        # Total time
        """ROUND(SUM(CAST(
            (strftime('%s', f.end_time) - strftime('%s', f.start_time)) AS REAL
            )/60/60), 2
        ) AS `total_time`""",
        # Tags, concatenated with ","
        """lower((
            SELECT GROUP_CONCAT(t.name, ',')
            FROM fact_tags AS ft
            JOIN tags AS t ON ft.tag_id = t.id
            WHERE ft.fact_id = f.id
        )) AS tags""",
    ))
    condition = "(f.start_time BETWEEN :from AND :to)"

    params = {"from": act_date,
              "to": act_date + timedelta(hours=24),}

    if project:
        condition += " AND c.name = :project"
        params["project"] = project

    if tags:
        condition += " AND tags REGEXP :regexp"
        params["regexp"] = r"(^|,)(%s)(,|$)" % "|".join(tags)

    dbcur.execute(query.format(select, condition), params)
    return dbcur.fetchall()

def main():
    "Entry point"

    # Date range iterator
    def date_range(a, b):
        iter = a
        while iter <= b:
            yield iter
            iter += timedelta(days=1)

    # CLI arguments parsing
    args = parse_args()

    CONFIG = load_config(args.c if args.c else DEFAULT_CONFIG)

    # Database connection
    try:
        db = db_connect(CONFIG["db_path"])
    except sqlite3.Error:
        return "Database connection error"

    # Data retrieval
    total = 0
    data = []

    try:
        for day in date_range(args.from_date, args.to_date):
            entries = get_time_entries(db, day, args.tags, args.project)
            if entries:
                data.append({"date": day, "entries": entries})
                total += len(entries)
    except BaseException as e:
        return e

    if not total:
        return "There is no time entries to synchronize"

    # Data export
    try:
        redmine = Redmine(CONFIG["redmine_host"], CONFIG["redmine_key"])

        progress = ProgressBar()
        increment_value = 100.0 / total

        for row in data:
            for item in row["entries"]:
                redmine.save_entry({
                    "issue_id": re.search("#([0-9]+)", item["name"]).group(1),
                    "activity": item["tags"],
                    "spent_on": row["date"].strftime("%Y-%m-%d"),
                    "hours": item["total_time"],
                    "comments": item["description"],
                })

                # Draw progress bar
                progress += increment_value
                progress.draw()
    except BaseException as e:
        return e

    sys.stdout.write("\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
