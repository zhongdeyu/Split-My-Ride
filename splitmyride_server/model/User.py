import sys
sys.path.append("../")
import logging
import uuid
import datetime
import MongoMixIn



class User(MongoMixIn.MongoMixIn):    
    MONGO_DB_NAME           = 'user'
    MONGO_COLLECTION_NAME   = 'user_c'
    
    A_USER_ID               = 'user_id'
    A_FIRST_NAME            = 'first_name'
    A_LAST_NAME             = 'last_name'
    A_IMAGE_URL             = 'image_url'
    A_PHONE                 = 'phone'

    ### Do I need to do this?
    @classmethod
    def setup_mongo_indexes(klass):
        from pymongo import ASCENDING
        coll = klass.mdbc()
        coll.ensure_index([(klass.A_PHONE, ASCENDING)], unique=True)
        coll.ensure_index([(klass.A_USER_ID, ASCENDING)], unique=True)
    
    @classmethod
    def create_or_update_user(klass, doc=None):      
        if not doc: doc = {}

        user_id = doc.get(klass.A_USER_ID)
        if not user_id:
            user_id = str(uuid.uuid4())
        spec = {klass.A_USER_ID:user_id}

        try:
            klass.mdbc().update(spec=spec, document={"$set": doc}, upsert=True, safe=True)
        except Exception, e:
            logging.error("COULD NOT UPSERT document in model.User Exception: %s" % e.message)
            return False
            
        return user_id

    @classmethod
    def get_user_by_phone(klass, phone):
        spec = {klass.A_PHONE:phone}
        return klass.mdbc().find_one(spec)
    
    @classmethod
    def get_users_by_user_ids(klass, user_ids):
        users_info = {}
        
        for user_id in user_ids:
            spec = {klass.A_USER_ID:user_id}
            user = klass.mdbc().find_one(spec)
            
            if user:
                users_info[user_id] = user
        
        return users_info