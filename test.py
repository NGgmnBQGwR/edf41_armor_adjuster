import ctypes
from ctypes import wintypes
import win32con
import win32api
import struct
import win32process
# win32api.GetLastError()


import sys
print(sys.version)

class PROCESSENTRY32(ctypes.Structure):
     _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * wintypes.MAX_PATH),
        ("th32MemoryBase", wintypes.DWORD),
        ("th32AccessKey", wintypes.DWORD),
    ]

class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD) , 
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD) ,
        ("modBaseAddr", ctypes.POINTER(wintypes.BYTE)) ,
        ("modBaseSize", wintypes.DWORD) , 
        ("hModule", wintypes.HMODULE) ,
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * wintypes.MAX_PATH),
    ]

class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", wintypes.LPVOID),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", wintypes.LPVOID),
    ]


def errcheck(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())


CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
Process32First = ctypes.windll.kernel32.Process32First
Process32Next = ctypes.windll.kernel32.Process32Next
Module32First = ctypes.windll.kernel32.Module32First
Module32Next = ctypes.windll.kernel32.Module32Next
GetLastError = ctypes.windll.kernel32.GetLastError
OpenProcess = ctypes.windll.kernel32.OpenProcess
GetPriorityClass = ctypes.windll.kernel32.GetPriorityClass
CloseHandle = ctypes.windll.kernel32.CloseHandle
GetModuleInformation = ctypes.windll.psapi.GetModuleInformation

ReadProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).ReadProcessMemory
ReadProcessMemory.errcheck = errcheck
ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPCVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = ctypes.wintypes.BOOL

WriteProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).WriteProcessMemory
WriteProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPVOID, ctypes.wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
WriteProcessMemory.restype = ctypes.wintypes.BOOL
WriteProcessMemory.errcheck = errcheck

# Includes all processes in the system in the snapshot.
TH32CS_SNAPPROCESS = 0x00000002
# Includes all modules of the process specified in th32ProcessID in the snapshot.
TH32CS_SNAPMODULE = 0x00000008

def find_process_by_name(wanted_name):
    hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe32 = PROCESSENTRY32()
    pe32.dwSize = ctypes.sizeof(PROCESSENTRY32)

    ret = Process32First(hProcessSnap, ctypes.byref(pe32))
    if ret == win32con.FALSE:
        print(ctypes.GetLastError())
        return None

    while ret != win32con.FALSE:
        process_name = pe32.szExeFile.decode('utf-8')
        if process_name == wanted_name:
            return pe32

        ret = Process32Next(hProcessSnap, ctypes.byref(pe32))

    CloseHandle(hProcessSnap)

    return None

def find_module_by_name(process_id, wanted_name):
    me32 = MODULEENTRY32()
    me32.dwSize = ctypes.sizeof(MODULEENTRY32)
    hModuleSnap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, process_id)

    ret = Module32First(hModuleSnap, ctypes.pointer(me32))
    if ret == win32con.FALSE:
        print(ctypes.GetLastError())
        CloseHandle(hModuleSnap)
        return None

    while ret != win32con.FALSE:
        module_name = me32.szModule.decode('utf-8')
        if module_name == wanted_name:
            return me32

        ret = Module32Next(hModuleSnap , ctypes.pointer(me32))

    CloseHandle(hModuleSnap)

    return None

def get_module_info(process_handle, module_handle):
    mi = MODULEINFO()
    res = GetModuleInformation(process_handle, module_handle, ctypes.byref(mi), GetModuleInformation)
    if res == win32con.FALSE:
        raise ctypes.WinError()
    return mi

resp = find_process_by_name('EDF41.exe')
resm = find_module_by_name(resp.th32ProcessID, 'EDF41.exe')
print(resm)
print(resm.modBaseAddr)
wat = resm.modBaseAddr.contents
print(dir(wat))


def get_memory(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    #bytesRead = ctypes.c_size_t(0)
    bytesRead = ctypes.c_ulonglong(0)
    #return_code = ReadProcessMemory(handle, address, buffer, size, ctypes.byref(bytesRead))
    return_code = ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytesRead))
    assert bytesRead.value == size
    return buffer.raw, return_code


def write_memory(handle, address, value):
    bytesWrote = ctypes.c_size_t(0)
    return_code = WriteProcessMemory(handle, address, ctypes.byref(ctypes.c_long(value)), 4, ctypes.byref(bytesWrote))
    return bytesWrote.value, return_code

proc_hand = win32api.OpenProcess(win32con.PROCESS_VM_WRITE | win32con.PROCESS_VM_READ | win32con.PROCESS_QUERY_INFORMATION, False, resp.th32ProcessID)
for module_info in win32process.EnumProcessModules(proc_hand):
    module_path = win32process.GetModuleFileNameEx(proc_hand, module_info)
    if module_path.endswith('EDF41.exe'):
        print(module_info)
        break

OFFSET = 0xCC84A0

