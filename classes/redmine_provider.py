#!/usr/bin/env python
# encoding: utf-8

from collections import OrderedDict
import redmine


class Redmine(object):
    """
    Redmine connection class
    """

    connection = None
    activities_id = {}
    activities = []

    def __init__(self, host, key):
        self.connection = redmine.Redmine(host, key=key)

        # Prefetch redmine activities
        data = self.connection.enumeration.filter( \
                                resource="time_entry_activities")
        for activity in data:
            name = activity.name.lower()
            self.activities.append(name)
            self.activities_id[name] = activity.id

    def save_entry(self, item):
        # Detect activity by tags (with set intersections)
        intersection = list(set(item["activity"].split(",")) & \
                            set(self.activities))
        if intersection:
            activity = intersection[0]
        else:
            activity = self.activities[0]

        entry = self.connection.time_entry.new()
        entry.issue_id = item['issue_id']
        entry.activity_id = self.activities_id[activity]
        entry.spent_on = item["spent_on"]
        entry.hours = item["hours"]
        entry.comments = item["comments"]
        entry.save()
