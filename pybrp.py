#!/usr/local/bin/python3.6

import requests
from requests.auth import HTTPBasicAuth
from datetime import date
from datetime import timedelta
from datetime import datetime


class BRPClient:
    config = {
        'basicAuth': ''
    }

    def __init__(self, baseUrl, apiKey, userName, passWord):
        self.config['basicAuth'] = HTTPBasicAuth(userName, passWord)
        self.config['apiKey'] = apiKey
        self.config['baseUrl'] = baseUrl
        self.todayd = date.today()
        self.today = self.todayd.isoformat()
        self.fortnight = (self.todayd + timedelta(days=14)).isoformat()

    def apikeyparam(self):
        return 'apikey=' + self.config['apiKey']

    def postEndpointWithData(self, res, payload):
        url = self.config['baseUrl'] + res + '.json' + '?' + self.apikeyparam()
        res = requests.post(url, data=payload, auth=self.config['basicAuth'])
        return res

    def getEndpointWithData(self, res, params):
        url = self.config['baseUrl'] + res + '.json' + '?' + self.apikeyparam() + '&' + params
        res = requests.get(url, auth=self.config['basicAuth'])
        return res

    def getEmployee(self, brpObject):
        brpEmployee = {'id': 0, 'name': ''}
        if 'resources' in brpObject:
            for brpResource in brpObject['resources']:
                if (brpResource['type'] == 'Personal') and ('employee' in brpResource):
                    brpEmployee = brpResource['employee']
        return brpEmployee

    def getPerson(self):
        r = self.getEndpointWithData('persons', 'requestauthtoken=true')
        return r

    # Not implemented here
    def cancelBooking(self):
        # endpoint: activitybookings
        # apichannel=2
        # id=<bookingid>
        # type=ordinary (is probably waitinglist if you are in queue)
        # apikey=
        return 0

    def createBooking(self, activityId):
        payload = {'apichannel': 'value', 'type': 'ordinary', 'activityid': activityId}
        res = self.postEndpointWithData('activitybookings', payload)
        return res

    def getActivityBookings(self, bookingType):
        res = self.getEndpointWithData('activitybookings', 'type=' + bookingType)
        return res

    def getOrdinaryActivityBookings(self):
        return self.getActivityBookings('ordinary')

    def getWaitinglistActivityBookings(self):
        return self.getActivityBookings('waitinglist')

    def getAllActivityBookings(self):
        result = {
            "status_code": 500,
            "activityBookings": []
        }

        # ordinary bookings == "Booked"
        brp_ordinary_bookings = self.getOrdinaryActivityBookings()
        if brp_ordinary_bookings.status_code == 200:
            result["status_code"] = 200
            bookings_record = brp_ordinary_bookings.json()
            if ('activitybookings' in bookings_record) and ('activitybooking' in bookings_record['activitybookings']):
                brp_activity_bookings = bookings_record['activitybookings']['activitybooking']
                result["brp_from"] = datetime.strptime(bookings_record['activitybookings']['startdate'], '%Y-%m-%d')
                result["brp_to"] = datetime.strptime(bookings_record['activitybookings']['enddate'], '%Y-%m-%d')
                for brp_booking in brp_activity_bookings:
                    brp_booking['coach'] = self.getEmployee(brp_booking)
                    result["activityBookings"].append(brp_booking)

        # waitinglist bookings == "On queue"
        brp_waitinglist_bookings = self.getWaitinglistActivityBookings()
        if brp_waitinglist_bookings.status_code == 200:
            result["status_code"] = 200
            bookings_record = brp_waitinglist_bookings.json()
            if ('activitybookings' in bookings_record) and (
                    'activitybooking' in bookings_record['activitybookings']):
                brp_activity_bookings = bookings_record['activitybookings']['activitybooking']
                brp_from = datetime.strptime(bookings_record['activitybookings']['startdate'], '%Y-%m-%d')
                brp_to = datetime.strptime(bookings_record['activitybookings']['enddate'], '%Y-%m-%d')
                # if waiting list window is greater on either side, expand
                if brp_from < result["brp_from"]:
                    result["brp_from"] = brp_from
                if brp_to > result["brp_to"]:
                    result["brp_to"] = brp_to
                for brp_booking in brp_activity_bookings:
                    brp_booking['coach'] = self.getEmployee(brp_booking)
                    result["activityBookings"].append(brp_booking)
        return result

    # Simple text representation
    def bookingTextLine(self, brpBooking):
        if brpBooking["type"] == 'ordinary':
            type = 'BOOKED:'
        else:
            type = "QUEUEING AT POSITION {}:".format(brpBooking["waitinglistposition"])
        # print("bTL from: " + json.dumps(brpBooking))
        return "{} {} {} {} {} {} ({}/{}/{})".format(
            type,
            brpBooking['id'],
            brpBooking['activityid'],
            brpBooking['start']['timepoint']['datetime'],
            brpBooking['activity']['product']['name'],
            brpBooking['coach']['name'],
            brpBooking['activity']['totalslots'],
            brpBooking['activity']['freeslots'],
            brpBooking['activity']['waitinglistsize']
        )

    def getActivities(self, fromDate, toDate):
        interval = 'startdate=' + fromDate.isoformat() + '&enddate=' + toDate.isoformat()
        params = 'includebooking=true&businessunitids=1&' + interval
        res = self.getEndpointWithData('activities', params)
        activities = []
        if res.status_code == 200:
            j = res.json()
            activities = j['activities']['activity']
        return activities
