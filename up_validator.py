
class Validator(object):
	Fields = {}

	def __init__(self, upformObj={}, origObj=None):
		'''
		:param upformObj: is expected in this format:
			{
				'field' 	: {'$set' : 'value'},
				'field2' 	: {'$unset' : 1 }
			}
		:param origObj: original object to compare fields againts (e. g. required fields)
		'''
		self.upformObj 	= upformObj
		self.origObj 	= origObj if origObj is not None else {}
		self.validated 	= False

	def ObjectValidator(self, upformObj, origObj={}):
		return True

	def Upsert(self, upsertor):
		'''
			!!! DEPRECATED !!!
		'''
		if not self.validated:
			return False

		for fldName, val in self.Fields.items():
			upformField = self.upformObj.get(fldName)
			if upformField is None:
				continue
			if not isinstance(upformField, dict):
				continue
			for action, value in upformField.items():
				fldAction 	= action
				fldValue 	= value
			upsertor.Scalar(fldAction, fldName, fldValue)
		return upsertor.Execute()

	def Validate(self, fieldsValidators={}, upformObj={}, origObj={}):
		'''
			Fields, upfromObj and origObj can be passed as arguments to this method
			so that they don't have to be set on object initialization
		'''
		errs = {}
		success = True
		self.Fields 	= fieldsValidators if fieldsValidators != {} else self.Fields
		self.upformObj 	= upformObj if upformObj != {} else self.upformObj
		self.origObj 	= origObj if origObj != {} else self.origObj
		# Field validation
		for fname, fvalids in fieldsValidators.iteritems():
			# load field from upform obj
			objField = self.upformObj.get(fname, {}) # TODO: Customize for delta object

			fldAction 	= None
			fldValue 	= None
			if isinstance(objField, dict):
				for action, value in objField.items():
					fldAction 	= action
					fldValue 	= value if action != "$unset" else None

			if not isinstance(fvalids, list): fvalids = [fvalids]

			for fvalid in fvalids:
				try:
					orig_value = self.origObj.get(fname)
					r = fvalid(
							upform_action 	= fldAction,
							upform_value 	= fldValue if fldAction is not None else orig_value,
							orig_value 		= orig_value
					)
				except Exception, e:
					r = "{}".format(e)
				if r is True:
					continue
				if not errs.has_key(fname): errs[fname]=list()
				errs[fname].append(r);
				success = False

		# Object level validation
		try:
			r = self.ObjectValidator(self.upformObj, self.origObj)
		except Exception, e:
			r = "{}".format(e)
			success = False
		if r is not True:
			if not errs.has_key('.obj'): errs['.obj']=list()
			errs['.obj'].append(r);
		
		if r and success:
			self.validated = True
			return True
		else:
			return errs
# EOF
