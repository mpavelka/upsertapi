class AccessController(object):
	origObj 	= {}
	upformObj 	= {}

	def __init__(self):		
		pass

	def _control(self, operation, userRoles, fieldsAccessControllersDict, fieldList=[]):
		errors = {}
		access = True

		for field in fieldList:
			access = False
			for ac_role, ac_control in fieldsAccessControllersDict.get(field, {}).items():
				if not isinstance(ac_control, list): ac_control = [ac_control]
				if not isinstance(userRoles, list): userRoles = [userRoles]
				for control in ac_control:
					access = control(ac_role, userRoles, operation)
					if access: break
				if access: break
			if not access:
				if not errors.has_key(field): errors[field]=list()
				errors[field].append('Operation "{0}" on field "{1}" is not permitted for active user'.format(operation, field));
		return True if errors == {} else errors

	def controlSet(self, userRoles, fieldsAccessControllersDict, fieldList=[]):
		return self._control('set', userRoles, fieldsAccessControllersDict, fieldList)

	def controlGet(self, userRoles, fieldsAccessControllersDict, fieldList=[]):
		return self._control('get', userRoles, fieldsAccessControllersDict, fieldList)

# EOF
