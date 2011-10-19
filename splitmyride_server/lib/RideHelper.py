from model.Ride import Ride
from model.User import User
import simplejson
from lib import ApiResponse
from lib.UserHelper import UserHelper

class RideHelper(object):
    
    @classmethod
    def create_or_update_ride(klass, user_id, origin, dest_lon, dest_lat, departure_time):
        ## Convert the origin and destination dictionaries into a string
        origin_dict = {}
        destination_dict = {}
        origin_dict = simplejson.loads(origin)
        origin_1 = origin_dict.get('origin_1')
        origin_2 = origin_dict.get('origin_2')

        doc = {
            Ride.A_USER_ID:user_id,
            Ride.A_ORIGIN_1:origin_1,
            Ride.A_ORIGIN_2:origin_2,
            Ride.A_DESTINATION_LON:dest_lon,
            Ride.A_DESTINATION_LAT:dest_lat,
            Ride.A_TIMESTAMP_DEPARTURE:departure_time
        }

        ride_id = Ride.create_or_update_ride(doc)

        if not ride_id:
            return ApiResponse.RIDE_COULD_NOT_CREATE
        else:
            return ride_id
        
    @classmethod
    def get_ride(klass, ride_id):
        ride = Ride.get_ride(ride_id)
        if not ride:
            return ApiResponse.RIDE_NOT_FOUND
        else:
            del ride[Ride.A_OBJECT_ID]
            return ride
    
    # Return the appropriate match(es) depending on the ride_id status
    #       if status = STATUS_PREPENDING, return complete list of potential matches
    #       if status = STATUS_PENDING, return a list with pending match on top along with other possible matches
    #       if status = STATUS_MATCHED, return the matched ride
    @classmethod
    def get_matches(klass, ride_id):        
        ride_doc = klass.get_ride(ride_id)
        status = ride_doc.get(Ride.A_STATUS)
        
        if status==0:
            return klass.get_matches_for_status_prepending(ride_doc)
        elif status==1:
            return klass.get_matches_for_status_pending(ride_doc)
        elif status==2:
            return klass.get_matches_for_status_matched(ride_doc)
        else:
            return ApiResponse.RIDE_NO_MATCHES_FOUND
    
    @classmethod
    def get_matches_for_status_prepending(klass, ride_doc):
        rides = []
        users = {}
        user_ids = []
                
        # Get all rides that match ride_doc specs
        rides = Ride.get_matches(ride_doc)
        
        # Get list of user_ids in rides  
        for ride in rides:
            user_id = ride.get(Ride.A_USER_ID)
            if user_id:
                user_ids.append(user_id)
        
        # Make batch call to get all user info
        users = UserHelper.get_users_by_id(user_ids)
        
        # Get the rides that match
        rides = Ride.get_matches(ride_doc)
        
        # Append each ride with user info
        if not rides:
            return ApiResponse.RIDE_NO_MATCHES_FOUND
        
        else:
            for ride in rides:
                del ride[Ride.A_OBJECT_ID]
                user_id = ride.get(Ride.A_USER_ID)
                ride["user"] = users.get(user_id)
            return rides

    @classmethod
    def get_matches_for_status_pending(klass, ride_doc):
        rides = []
        
        # first ensure status is pending
        if not ride_doc.get(Ride.A_STATUS)==1: return klass.get_matches_for_status_prepending(ride_doc)
        
        # get the match ride and user info
        pending_ride_id = ride_doc.get(Ride.A_PENDING_RIDE_ID)
        if not pending_ride_id: return klass.get_matches_for_status_prepending(ride_doc)
        
        rides.append(klass.get_ride_and_user_docs_from_ride_id(pending_ride_id))
        
        # Add other potential matches with prepending status
        prepending_rides = klass.get_matches_for_status_prepending(ride_doc)
        rides.append(prepending_rides)
        
        return rides
    
    @classmethod
    def get_matches_for_status_matched(klass, ride_doc):
        doc = ""
        
        # first ensure status is matched
        if not ride_doc.get(Ride.A_STATUS)==2: return doc
            
        # get the match ride and user info
        match_ride_id = ride_doc.get(Ride.A_MATCH_RIDE_ID)    
        if not match_ride_id: return doc
        
        return klass.get_ride_and_user_docs_from_ride_id(match_ride_id)

    @classmethod
    def get_ride_and_user_docs_from_ride_id(klass, ride_id):
        doc = ""
        
        if not ride_id: return doc
        
        ride_doc = klass.get_ride(ride_id)
        if not ride_doc: return doc
        
        user_id = ride_doc.get(klass.A_USER_ID)
        if not user_id: return doc
        
        user_doc = UserHelper.get_users_by_id(user_id)
        if not user_doc: return ride_and_user_doc
        
        ride_doc["user"]=user_doc
        return ride_doc
    
    
    @classmethod
    def do_match_action(klass, action, curr_user_ride_id, match_ride_id):
        # Complete appropriate SMS action
        if action == 'request':
            return klass.request_ride(curr_user_ride_id, match_ride_id)
        else if action == 'accept':
            return klass.accept_ride(curr_user_ride_id, match_ride_id)
        else if action == 'decline':
            return klass.decline_ride(curr_user_ride_id, match_ride_id)
        else: 
            return ApiResponse.RIDE_NO_ACTION
    
    @classmethod
    def request_ride(klass, curr_user_ride_id, match_ride_id):
        # update the status of both ride ids to be STATUS_PENDING
        curr_update_doc = {
                Ride.A_RIDE_ID:curr_user_ride_id,
                Ride.A_STATUS:1,
                Ride.A_PENDING_RIDE_ID:match_ride_id
                }
        match_update_doc = {
                Ride.A_RIDE_ID:match_ride_id
                Ride.A_STATUS:1,
                Ride.A_PENDING_RIDE_ID:curr_user_ride_id
            }
        curr_update_success = Ride.create_or_update_ride(curr_update_doc)
        match_update_success = Ride.create_or_update_ride(match_update_doc)
        if not curr_update_success or match_update_success: return ApiResponse.RIDE_COULD_NOT_REQUEST_MATCH
        
        # get name of the curr_user
        curr_ride_doc = klass.get_ride_and_user_docs_from_ride_id(curr_user_ride_id)        
        if not curr_ride_doc: return ApiResponse.RIDE_COULD_NOT_REQUEST_MATCH
        from_first_name = curr_ride_doc.get("user").get(USER.A_FIRST_NAME)
        from_last_name = curr_ride_doc.get("user").get(USER.A_LAST_NAME)
        
        # get the phone number of the match_id
        match_doc = klass.get_ride_and_user_docs_from_ride_id(match_ride_id) 
        if not match_doc: return ApiResponse.RIDE_COULD_NOT_REQUEST_MATCH
        to_first_name = match_doc.get("user").get(USER.A_FIRST_NAME)
        to_last_name = match_doc.get("user").get(USER.A_LAST_NAME)
        to_phone_number = match_doc.get("user").get(USER.A_PHONE)

        # send sms and return twilio response
        note = "Hi %s, great news! %s wants to split a ride with you! Go to the app to check out details!" 
            % (to_first_name, from_first_name +" "+ from_last_name)
        return TwilioHelper.send_sms(note=note, to=to_phone_number)
    
    @classmethod
    def accept_ride(klass, curr_user_ride_id, match_ride_id):
        # ensure that both rides have STATUS_PENDING
        curr_update_doc = {
                Ride.A_RIDE_ID:curr_user_ride_id,
                Ride.A_STATUS:2,
                Ride.A_PENDING_RIDE_ID:match_ride_id
                }
        match_update_doc = {
                Ride.A_RIDE_ID:match_ride_id
                Ride.A_STATUS:2,
                Ride.A_PENDING_RIDE_ID:curr_user_ride_id
            }
        curr_update_success = Ride.create_or_update_ride(curr_update_doc)
        match_update_success = Ride.create_or_update_ride(match_update_doc)
        if not curr_update_success or match_update_success: return ApiResponse.RIDE_COULD_NOT_ACCEPT_MATCH
        
        # update the status of both ride ids to be MATCHED
        # get info of the curr_user_ride_id
        # send an sms to match_ride_id to notify them of the acceptance
        # return twilio response or error if status_pending is not there
        return ""
    
    @classmethod
    def decline_ride(klass, curr_user_ride_id, match_ride_id):
        # ensure that both rides have STATUS_PENDING
        # update the status of both ride ids to be UNMATCHED
        # add both ride_ids to blacklists of each other's rides
        # return
        return ""