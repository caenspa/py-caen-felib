import ctypes as ct
import json

from caen_felib import lib

class Endpoint:

	def __init__(self, handle):
		self.__h = handle

	def set_read_data_format(self, format):
		lib.SetReadDataFormat(self.__h, json.dumps(format).encode())
		# TODO: set lib.ReadData.argtypes, required on Apple ARM64

	def read_data(self, timeout, *args):
		lib.ReadData(self.__h, timeout, *args)

	def has_data(self, timeout):
		lib.HasData(self.__h, timeout)


class Device:

	def __init__(self, url):
		self.__h = self.__connect(url)
		self.endpoints = dict(self.__endpoints())

	def __del__(self):
		lib.Close(self.__h)

	@staticmethod
	def __connect(url):
		handle = ct.c_uint64()
		lib.Open(url.encode(), handle)
		return handle

	def __endpoints(self):
		for h in self.__get_child_handles(self.__h, '/endpoint'):
			name, type = self.__get_node_properties(h, None)
			if type == 4:
				yield name, Endpoint(h)

	@staticmethod
	def __get_child_handles(handle, path):
		b_path = None if path is None else path.encode()
		res = lib.GetChildHandles(handle, b_path, None, 0)
		n_child_handles = res
		child_handles = (ct.c_uint64 * n_child_handles)()
		res = lib.GetChildHandles(handle, b_path, child_handles, n_child_handles)
		if res != n_child_handles:
			raise RuntimeError('unexpected size')
		return [ct.c_uint64(h) for h in child_handles]

	@staticmethod
	def __get_node_properties(handle, path):
		b_path = None if path is None else path.encode()
		name = ct.create_string_buffer(32)
		type = ct.c_int()
		lib.GetNodeProperties(handle, b_path, name, type)
		return name.value.decode(), type.value

	def get_device_tree(self, initial_size = 2 ** 22):
		'''Wrapper to CAEN_FELib_GetDeviceTree'''
		while True:
			device_tree_size = initial_size
			device_tree = ct.create_string_buffer(device_tree_size)
			res = lib.GetDeviceTree(self.__h, device_tree, device_tree_size)
			if res < device_tree_size:
				return json.loads(device_tree.value.decode())
			else:
				device_tree_size = res

	def get_value(self, path):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(256)
		lib.GetValue(self.__h, path.encode(), value)
		return value.value.decode()

	def get_value_with_arg(self, path, arg):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(arg.encode(), 256)
		lib.GetValue(self.__h, path.encode(), value)
		return value.value.decode()

	def set_value(self, path, value):
		'''Wrapper to CAEN_FELib_setValue'''
		lib.SetValue(self.__h, path.encode(), value.encode())

	def get_user_register(self, addr):
		'''Wrapper to CAEN_FELib_GetUserRegister'''
		value = ct.c_uint32()
		lib.GetUserRegister(self.__h, addr, value)
		return value.value

	def set_user_register(self, addr, value):
		'''Wrapper to CAEN_FELib_SetUserRegister'''
		lib.SetUserRegister(self.__h, addr, value)

	def send_command(self, path):
		'''Wrapper to CAEN_FELib_SendCommand'''
		lib.SendCommand(self.__h, path.encode())
