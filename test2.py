# encoding: utf-8

import ctypes
import struct
# import numpy


def errcheck(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())


def get_memory(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    #bytesRead = ctypes.c_ulong(0)
    bytesRead = ctypes.c_size_t(0)
    return_code = ReadProcessMemory(handle, address, buffer, size, ctypes.byref(bytesRead))
    assert bytesRead.value == size
    return buffer.raw, return_code


def write_memory(handle, address, value):
    bytesWrote = ctypes.c_size_t(0)
    return_code = WriteProcessMemory(handle, address, ctypes.byref(ctypes.c_long(value)), 4, ctypes.byref(bytesWrote))
    return bytesWrote.value, return_code


def looks_like_a_pointer(addr):
    if (addr % 4 == 0) and (0x29B000 <= addr < 0x2884000):
        return True
    return False


def is_nearby_address(addr1, addr2):
    return abs(addr1 - addr2) <= 0x1000


def get_value(ints, address):
    index = (address - 0x29B000) / 4
    if index < 0:
        raise IndexError(index)
    return ints[index]


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


OpenProcess = ctypes.windll.kernel32.OpenProcess

CloseHandle = ctypes.windll.kernel32.CloseHandle

#ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory
ReadProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).ReadProcessMemory
ReadProcessMemory.errcheck = errcheck
ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPCVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = ctypes.wintypes.BOOL

WriteProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).WriteProcessMemory
WriteProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPVOID, ctypes.wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
WriteProcessMemory.restype = ctypes.wintypes.BOOL
WriteProcessMemory.errcheck = errcheck

PROCESS_ALL_ACCESS = 0x1F0FFF
PID = 3760
MEMORY_BLOCK_ADDRESS = 0x2029B000
MEMORY_BLOCK_SIZE = 0x25E9000

processHandle = OpenProcess(PROCESS_ALL_ACCESS, False, PID)

