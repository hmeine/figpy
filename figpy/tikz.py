class Options(list):
	def __setitem__(self, key, value):
		if isinstance(key, int):
			list.__setitem__(self, key, value)
		else:
			for i, (existing, _) in enumerate(self):
				if key == existing:
					del self[i]
					break
			self.append((key, value))

	def __getitem__(self, index):
		if isinstance(index, int):
			list.__getitem__(self, index)
		else:
			for key, value in self:
				if key == index:
					return value
			raise KeyError("Option '%s' not set!" % index)

	def __delitem__(self, index):
		if isinstance(index, int):
			list.__delitem__(self, index)
		else:
			for i, (existing, value) in enumerate(self):
				if index == existing:
					list.__delitem__(self, i)
					return
			raise KeyError("Option '%s' not set!" % index)

	def commaSeparated(self):
		result = []
		for key, value in self:
			if value is not None:
				if key in ("style", "color"):
					result.append(value)
				else:
					result.append("%s=%s" % (key, value))
			else:
				result.append(key)
		return ",".join(result)

	def __str__(self):
		if not self:
			return ""
		return "[%s]" % (self.commaSeparated(), )

	def get(self, key, default):
		for existing, value in self:
			if existing == key:
				return value
		return default

	def __contains__(self, key):
		for existing, value in self:
			if existing == key:
				return True
		return False

	def append(self, option):
		if isinstance(option, str):
			option = (option, None)
		else:
			assert len(option) == 2
		list.append(self, option)

	def insert(self, index, option):
		if isinstance(option, str):
			option = (option, None)
		else:
			assert len(option) == 2
		list.insert(self, index, option)
