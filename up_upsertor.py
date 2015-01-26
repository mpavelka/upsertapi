import bson
from datetime import datetime
from flask.ext.login import current_user
from ..services.service_mongo import DB

class Upsertor(object):

	def __init__(self, origObj=None):

		self.origObj = origObj
		self.isNew 	= origObj is None or origObj == {}

		self.mod_Inc = { '_v' : 1 } # Increment '_v' at every change
		self.mod_Set = {}
		self.mod_Unset = {}
		self.mod_Push = {}
		self.mod_Pull = {}


	def __GetVal(self, dotConvField):
		v = self.origObj
		for k in dotConvField.split('.'):
			if not isinstance(v, dict): raise RuntimeError("Dictionary is expected.")
			v = v.get(k)
			if v is None: break;
		return v

	def __KeyDotsReplace(self, dictobj):
		# for k, v in dictobj.items():
		# 	dictobj[k]
		# 	__KeyDotsReplace(v)
		return

	def GenPK(self):
		return bson.ObjectId()

	@staticmethod
	def GetKeyName():
		return '_id'
## Modificators
	def FromDict(self, upsertDict):
		for key, val in upsertDict.items():
			
			if key == '$set':
				if not isinstance(val, dict):
					raise RuntimeError("Dictionary is expected.")
				for k, v in val.items():
					self.SetScalar(k, v)
			if key == '$unset':
				if not isinstance(val, dict):
					raise RuntimeError("Dictionary is expected.")
				for k, v in val.items():
					self.UnsetScalar(k, v)

	def Scalar(self, action, objField, value):
		if action == "$set":
			self.SetScalar(objField, value)
		elif action == "$unset":
			self.UnsetScalar(objField)

	def SetScalar(self, objField, value):
		origVal = None if self.isNew else self.__GetVal(objField)

		if origVal == value:
			return False
		if origVal is None and value is '' :
			return False

		if value is None or value == '':
			self.UnsetScalar(objField)
		else:
			self.mod_Set[objField] = value

	def UnsetScalar(self, obj_field):
		self.mod_Unset[obj_field] = ""

	def PullItem(self):
		pass

	def Execute(self):
		addobj = {}
		delobj = {}
		logWhat = {}

		userId 		= current_user.id if current_user.is_authenticated() else "0"
		userName 	= current_user.firstName+" "+current_user.lastName if current_user.is_authenticated() else "unathenticated"

		pkName = self.GetKeyName()
		if self.isNew:
			pk = self.GenPK()
		else:
			pk = self.origObj.get(pkName, '_id')
		
		if len(self.mod_Set):
			addobj['$set'] = self.mod_Set
			logWhat['set'] = self.mod_Set
			for k, v in self.mod_Set.items():
				logWhat['set'][k.replace('.', '__')] = v

		if len(self.mod_Inc):
			addobj['$inc'] = self.mod_Inc
			logWhat['inc'] = self.mod_Inc
			for k, v in self.mod_Inc.items():
				logWhat['inc'][k.replace('.', '__')] = v


		if len(self.mod_Push):
			addobj['$pushAll'] = self.mod_Push
			logWhat['pushAll'] = self.mod_Push
			for k, v in self.mod_Push.items():
				logWhat['pushAll'][k.replace('.', '__')] = v

		if len(self.mod_Pull):
			delobj['$pull'] = self.mod_Pull
			logWhat['pull'] = {}
			for k, v in self.mod_Pull.items():
				logWhat['pull'][k.replace('.', '__')] = v

		if len(self.mod_Unset):
			delobj['$unset'] = self.mod_Unset
			# remove Dot Convention for logging
			logWhat['unset'] = {}
			for k, v in self.mod_Unset.items():
				logWhat['unset'][k.replace('.', '__')] = v

		query = {'_id' : pk}
		if self.isNew:
			query['_v'] = 0 # Ensure that new document is really inserted
		else: query['_v'] = self.origObj.get('_v')

		# First wave (adding stuff)
		if len(addobj) > 0:
			ret = self.Collection.find_and_modify(
				query = query,
				update = addobj,
				upsert = self.isNew,
				full_response = True
			)
			if not ret.get('ok') == 1:
				return ret
			if ret.get('value') == None:
				ret.update({ 'ok' : 0, 'alert' : 'warning', 'errors' : { "_id" : ["Not saved. Data modified by different user!"]} })
				return ret
		# Second wave (deleting stuff)
		if len(delobj) > 0 and not self.isNew:
			ret = self.Collection.find_and_modify(
				query = query,
				update = delobj,
				upsert = self.isNew,
				full_response = True
			)
			if not ret.get('ok') == 1:
				return ret
			if ret.get('value') == None:
				ret.update({ 'ok' : 0, 'alert' : 'warning', 'errors' : { "_id" : ["Not saved. Data modified by different user!"]} })
				return ret
		# Audit Log
		if len(logWhat) > 0:
			DB.AuditLog.insert(
			{
				'pk' 	: pk,
				'who'	: { 'Id' : userId, 'Name' : userName},
				'when'	: datetime.now(),
				'where'	: self.Collection.name,
				'what'	: logWhat,
			})
		
		return {'ok':1, 'log': logWhat}

class Remover(object):

	def __init__(self, objectId):
		self.objectId = objectId

	def Execute(self):
		ret = self.Collection.find_and_modify(
			query= {'_id' : self.objectId},
			remove=True,
			full_response=True,
		)
		if (ret.get('ok', False) == 1 ):
			DB.AuditLog.insert(
			{
				'pk' 	: self.objectId,
				'who'	: { 'Id' : userId, 'Name' : userName},
				'when'	: datetime.now(),
				'where'	: self.Collection.name,
				'what'	: { 'rem' : ret['value'] }
			})

		return ret
# EOF
