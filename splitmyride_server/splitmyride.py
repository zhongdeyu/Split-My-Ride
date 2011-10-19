import re
import urlparse
import urllib
from urlparse import parse_qs, parse_qsl

import tornado.httpserver
import tornado.ioloop
import tornado.web

from model.User import User
from lib.UserHelper import UserHelper

from lib import ApiResponse

## Sets up all the HTTP Get / Post requests using Tornado, listening on port 80
class UserHandler(tornado.web.RequestHandler):
    
    # Get user info
    def get(self):
        user = {}
        m = re.match('^/user/([\d].*)$', self.request.uri)
        if m:
            phone = m.group(1)
            user = self.get_user_by_phone(phone)
        self.write(user)
    
    # Get user info from database        
    def get_user_by_phone(self, phone):
        return UserHelper.get_user_by_phone(phone)
       
    # Add a new user with first_name, last_name, phone and image_url
    def post(self):
        resp = self.add_user()
        self.write(resp)
        
    # Add user to database
    def add_user(self):
        first_name = self.get_argument('first_name') 
        last_name = self.get_argument('last_name')
        image_url = self.get_argument('image_url') 
        phone = self.get_argument('phone')
        return UserHelper.add_user(first_name, last_name, image_url, phone)
        

class RideHandler(tornado.web.RequestHandler):

    # Add a new ride
    def post(self):
        resp = self.add_ride()
        self.write(resp)

    # Add user to database
    def add_ride(self):
        user_id = self.get_argument('user_id') 
        origin = self.get_argument('origin')
        dest_lon = self.get_argument('dest_lon') 
        dest_lat = self.get_argument('dest_lat')
        departure_time = self.get_argument('departure_time')
        return RideHelper.create_or_update_ride(user_id, origin, dest_lon, dest_lat, departure_time)

class MatchHandler(tornado.web.RequestHandler):
    
    def get(self):
        matches = {}
        m = re.match('^/match/([0-9a-f]){32}$', self.request.uri)
        if m:
            ride_id = m.group(1)
            matches = self.get_matches(ride_id)
        self.write(matches)
    
    def post(self):
        resp = self.do_match_action()
        pass self.write(resp)
        
    # Request, accept or decline a match
    def do_match_action():
        action = self.get_argument('action')
        curr_user_ride_id = self.get_argument('curr_user_ride_id')
        match_ride_id = self.get_argument('match_ride_id')
        return RideHelper.do_SMS_action(action, curr_user_ride_id, match_ride_id)
        
    def get_matches(self, ride_id):
        return RideHelper.get_matches(ride_id)

class TerminalHandler(tornado.web.RequestHandler):

    def get(self):
        terminals = {}
        m = re.match('^/terminal/([a-zA-Z]){3}$', self.request.uri)
        if m:
            airport = m.group(1)
            terminals = self.get_terminals(airport)
        self.write(terminals)
    
    def get_terminals(self, airport):
        return TerminalHelper.get_terminals(airport)

application = tornado.web.Application([
    #(r"/", MainHandler),                 # get() - homepage - link to app
    (r"/user/.*", UserHandler),          # get() - get user data; post() - create a user
    (r"/ride/.*", RideHandler),          # post() - create or edit a ride
    (r"/match/.*", MatchHandler),        # get() - list of matches / match for a ride; post() - request/accept/decline a match
    (r"/terminal/.*", TerminalHandler),  # get() - get a list of terminals by airline
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()
    
## Convert string into a dictionary

# --- urls ---
# user/:phone
# - get() a user's data, e.g. http://splitmyri.de/user/6469152002
# user/add
# - post() to create a user, e.g. http://splitmyri.de/user/add with a POST body containing all the data to create the user
