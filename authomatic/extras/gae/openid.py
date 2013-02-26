# We need absolute iport to import from openid library which has the same name as this module
from __future__ import absolute_import
from google.appengine.ext import ndb
import datetime
import logging
import openid.store.interface



class NDBOpenIDStore(ndb.Expando, openid.store.interface.OpenIDStore):
    serialized = ndb.StringProperty()
    expiration_date = ndb.DateTimeProperty()
    # we need issued to sort by most recently issued
    issued = ndb.IntegerProperty()
    
    # Logging method.
    _log = lambda level, message: None
    
    @classmethod
    def storeAssociation(cls, server_url, association):
        # store an entity with key = server_url
                
        issued = datetime.datetime.fromtimestamp(association.issued)
        lifetime = datetime.timedelta(0, association.lifetime)
        
        expiration_date = issued + lifetime
        
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Getting or inserting OpenID association from datastore.')
        
        
        
        cls._log(logging.DEBUG, '------------------------------------------------')
        cls._log(logging.DEBUG, '| Association')
        cls._log(logging.DEBUG, '------------------------------------------------')
        cls._log(logging.DEBUG, '| server_url = {}'.format(server_url))
        cls._log(logging.DEBUG, '|')
        cls._log(logging.DEBUG, '| Association:')
        cls._log(logging.DEBUG, '| \t issued = {}'.format(association.issued))
        cls._log(logging.DEBUG, '| \t lifetime = {}'.format(association.lifetime))
        cls._log(logging.DEBUG, '| \t handle = {}'.format(association.handle))
        cls._log(logging.DEBUG, '------------------------------------------------')
        
        
        
        entity = cls.get_or_insert(association.handle, parent=ndb.Key('ServerUrl', server_url))
        
        entity.serialized = association.serialize()
        entity.expiration_date = expiration_date
        entity.issued = association.issued
        
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Putting OpenID association to datastore.')
        
        entity.put()
    
    
    @classmethod
    def cleanupAssociations(cls):
        
        # query for all expired
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Querying datastore for OpenID associations.')
        query = cls.query(cls.expiration_date <= datetime.datetime.now())
        
        # fetch keys only
        expired = query.fetch(keys_only=True)
        
        # delete all expired
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Deleting expired OpenID associations from datastore.')
        ndb.delete_multi(expired)
        
        return len(expired)
    
    
    @classmethod
    def getAssociation(cls, server_url, handle=None):
        
        cls.cleanupAssociations()
        
        if handle:
            key = ndb.Key('ServerUrl', server_url, cls, handle)
            cls._log(logging.DEBUG, 'NDBOpenIDStore: Getting OpenID association from datastore by key.')
            entity = key.get()
        else:
            # return most recently issued association
            cls._log(logging.DEBUG, 'NDBOpenIDStore: Querying datastore for OpenID associations by ancestor.')
            entity = cls.query(ancestor=ndb.Key('ServerUrl', server_url)).order(-cls.issued).get()
        
        if entity and entity.serialized:
            return openid.association.Association.deserialize(entity.serialized)
    
    
    @classmethod
    def removeAssociation(cls, server_url, handle):
        key = ndb.Key('ServerUrl', server_url, cls, handle)
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Getting OpenID association from datastore by key.')
        if key.get():
            cls._log(logging.DEBUG, 'NDBOpenIDStore: Deleting OpenID association from datastore.')
            key.delete()
            return True
    
    @classmethod
    def useNonce(cls, server_url, timestamp, salt):
        
        cls._log(logging.DEBUG, '------------------------------------------------')
        cls._log(logging.DEBUG, '| Nonce')
        cls._log(logging.DEBUG, '------------------------------------------------')
        cls._log(logging.DEBUG, '| server_url = {}'.format(server_url))
        cls._log(logging.DEBUG, '| timestamp = {}'.format(timestamp))
        cls._log(logging.DEBUG, '| salt = {}'.format(salt))
        cls._log(logging.DEBUG, '------------------------------------------------')
        
        
        # check whether there is already an entity with the same ancestor path in the datastore
        key = ndb.Key('ServerUrl', str(server_url) or 'x', 'TimeStamp', str(timestamp), cls, str(salt))
        
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Getting OpenID nonce from datastore by key.')
        result = key.get()
        
        if result:
            # if so, the nonce is not valid so return False
            return False
        else:
            # if not, store the key to datastore and return True
            nonce = cls(key=key)
            nonce.expiration_date = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(0, openid.store.nonce.SKEW)
            cls._log(logging.DEBUG, 'NDBOpenIDStore: Putting OpenID nonce to datastore.')
            nonce.put()
            return True
    
    
    @classmethod
    def cleanupNonces(cls):
        # get all expired nonces
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Querying datastore for OpenID nonces ordered by expiration date.')
        expired = cls.query().filter(cls.expiration_date <= datetime.datetime.now()).fetch(keys_only=True)
        
        # delete all expired
        cls._log(logging.DEBUG, 'NDBOpenIDStore: Deleting expired OpenID nonces from datastore.')
        ndb.delete_multi(expired)
        
        return len(expired)
