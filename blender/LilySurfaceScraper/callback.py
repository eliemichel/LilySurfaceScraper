# Copyright (c) 2019 - 2020 Elie Michel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided “as is”, without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and noninfringement. In no event shall
# the authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other dealings in the
# Software.
#
# This file is part of LilySurfaceScraper, a Blender add-on to import materials
# from a single URL

import random

"""
This module is used to register callbacks that operators will call once they are done.
It works around a bpy API issue which is that it makes very hard to wait for an
operator to finish. It converts callbacks into numeric handles that can be provided
through operator properties.
"""

callback_dict = {}

def register_callback(callback):
	"""
	@param callback: a function to call after.an operator is done,
	taking a unique argument which is the context
	@return: a handle to the callback, to be provided to the operator
	"""
	limit = 1677216
	if len(callback_dict) > limit / 4:
		print("Too many callback registered")
		return -1
	handle = random.randint(0,limit)
	while handle in callback_dict:
		handle = random.randint(0,limit)
	callback_dict[handle] = callback
	return handle

def get_callback(handle):
	return callback_dict.get(handle, lambda context: None)
