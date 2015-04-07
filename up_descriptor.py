class Descriptor(object):
	'''
		Descriptor of database object.
		Contains full list of available fields and field-specific lists of validators and access controllers

		Example:

		class CollectionDescriptor(Descriptor):
			Fields = {
				'_id' : {
					'validator': [
						up.fvalids.FValid_String(
							required = True,
							msg = "Site ID"),
						up.fvalids.FValid_Unchangeable(
							msg = "Site ID"
						)
					],
					'accesscontrol' : {
						'*': up.ac.FAC_ReadOnly(),
						'admin': up.ac.FAC_Read(),
					},
				}
			}
	'''

	# Name of collection in database
	Collection = None
	# Describes fields for upsertor and getter
	Fields = {}

	def GetCollection(self):
		return self.Collection

	def GetFields(self):
		return [f for f, v in self.Fields.items()]
	
	def GetFieldValidators(self, field):
		return self.Fields.get(field, {}).get('validators')

	def GetFieldAccessControl(self, field):
		return self.Fields.get(field, {}).get('accesscontrol')

	def GetFieldsValidatorsDict(self):
		'''
			returns {'field0' : [validator1, validator2], 'field1' : [validator1] }
		'''
		ret = {}
		for field, description in self.Fields.items():
			ret[field] = description.get('validators', []) 
		return ret

	def GetFieldsAccessControllersDict(self):
		'''
			returns {'field' : {'role1' : accesscontroler, 'role2' : accesscontroler}, 'field2' : {...}}
		'''
		ret = {}
		for field, description in self.Fields.items():
			ret[field] = description.get('accesscontrol', {})
		return ret

# EOF
