import ctypes
from ctypes import wintypes
import datetime
import os
import shutil
import zipfile
import struct

import win32api
import win32con
import win32gui
import win32process

SAVE_FOLDER_PATH = os.path.join(os.path.expanduser('~'), 'Documents', 'My Games', 'EDF4.1', 'SAVE_DATA')


class EDFMemoryEditorHelper(object):
    ARMOR_STRUCT_OFFSET = 0xCC84A0
    FIRST_LAUNCH_FLAG_NAME = '_first_time_armor_adjustment_done'

    class ArmorOffset(object):
        RANGER_MAX = 0x25F0
        RANGER_CURRENT = 0x26BC
        WING_DIVER_MAX = 0x25F4
        WING_DIVER_CURRENT = 0x26C0
        AIR_RIDER_MAX = 0x25F8
        AIR_RIDER_CURRENT = 0x26C4
        FENCER_MAX = 0x25FC
        FENCER_CURRENT = 0x26C8

    def __init__(self, process_handle, main_module_start_address):
        self.initial_adjustment_flag_filepath = os.path.join(os.getcwd(), self.FIRST_LAUNCH_FLAG_NAME)
        self._armor_struct_pointer_cache = None
    
        self.process_handle = process_handle
        self.main_module_start_address = main_module_start_address
        self.main_pointer_address = self.main_module_start_address + self.ARMOR_STRUCT_OFFSET

        self.ReadProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).ReadProcessMemory
        self.ReadProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPCVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.ReadProcessMemory.restype = ctypes.wintypes.BOOL
        self.ReadProcessMemory.errcheck = self._errcheck

        self.WriteProcessMemory = ctypes.WinDLL('kernel32', use_last_error=True).WriteProcessMemory
        self.WriteProcessMemory.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.LPVOID, ctypes.wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.WriteProcessMemory.restype = ctypes.wintypes.BOOL
        self.WriteProcessMemory.errcheck = self._errcheck

    @property
    def _armor_struct_pointer(self):
        if not self._armor_struct_pointer_cache:
            self._armor_struct_pointer_cache = self._read_memory(self.main_pointer_address, 8)
        return self._armor_struct_pointer_cache

# RANGER
    @property
    def _ranger_max_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.RANGER_MAX, 4)
    @_ranger_max_armor.setter
    def _ranger_max_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.RANGER_MAX, value)

    @property
    def _ranger_current_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.RANGER_CURRENT, 4)
    @_ranger_current_armor.setter
    def _ranger_current_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.RANGER_CURRENT, value)

# WING DIVER
    @property
    def _wing_diver_max_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.WING_DIVER_MAX, 4)
    @_wing_diver_max_armor.setter
    def _wing_diver_max_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.WING_DIVER_MAX, value)

    @property
    def _wing_diver_current_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.WING_DIVER_CURRENT, 4)
    @_wing_diver_current_armor.setter
    def _wing_diver_current_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.WING_DIVER_CURRENT, value)

# AIR RIDER
    @property
    def _air_rider_max_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.AIR_RIDER_MAX, 4)
    @_air_rider_max_armor.setter
    def _air_rider_max_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.AIR_RIDER_MAX, value)

    @property
    def _air_rider_current_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.AIR_RIDER_CURRENT, 4)
    @_air_rider_current_armor.setter
    def _air_rider_current_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.AIR_RIDER_CURRENT, value)

# FENCER
    @property
    def _fencer_max_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.FENCER_MAX, 4)
    @_fencer_max_armor.setter
    def _fencer_max_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.FENCER_MAX, value)

    @property
    def _fencer_current_armor(self): return self._read_memory(self._armor_struct_pointer + self.ArmorOffset.FENCER_CURRENT, 4)
    @_fencer_current_armor.setter
    def _fencer_current_armor(self, value): self._write_memory(self._armor_struct_pointer + self.ArmorOffset.FENCER_CURRENT, value)

    def _is_first_launch(self):
        return not os.path.exists(self.initial_adjustment_flag_filepath)

    def _errcheck(self, result, func, args):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())

    def _read_memory(self, address, size):
        assert size in [4, 8]
        buffer = ctypes.create_string_buffer(size)
        bytesRead = ctypes.c_ulonglong(0)
        self.ReadProcessMemory(self.process_handle.handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytesRead))
        assert bytesRead.value == size
        if size == 4:
            return struct.unpack('<L', buffer.raw)[0]
        elif size == 8:
            return struct.unpack('<Q', buffer.raw)[0]
        else:
            raise AssertionError()

    def _write_memory(self, address, value):
        assert value < 0xFFFFFFFF
        bytesWrote = ctypes.c_size_t(0)
        self.WriteProcessMemory(self.process_handle.handle, address, ctypes.byref(ctypes.c_long(value)), 4, ctypes.byref(bytesWrote))
        return bytesWrote.value

    def _confirm_adjustment(self):
        result = input("Continue with armor adjustment? [y/n]:")
        if result.strip().lower() == 'y':
            return True
        return False

    def print_armor_info(self):
        print("Ranger: {}/{}\n"
        "Wing Diver: {}/{}\n"
        "Air Rider: {}/{}\n"
        "Fencer: {}/{}".format(
            self._ranger_current_armor, self._ranger_max_armor,
            self._wing_diver_current_armor, self._wing_diver_max_armor,
            self._air_rider_current_armor, self._air_rider_max_armor,
            self._fencer_current_armor, self._fencer_max_armor,
        ))

    def _initial_armor_adjustment(self):
        print("Armor before complete re-adjustment:")
        self.print_armor_info()

        if not self._confirm_adjustment():
            return False

        all_armor = self._ranger_max_armor + self._wing_diver_max_armor + self._air_rider_max_armor + self._fencer_max_armor
        self._ranger_max_armor = all_armor
        self._ranger_current_armor = all_armor
        self._wing_diver_max_armor = all_armor
        self._wing_diver_current_armor = all_armor
        self._air_rider_max_armor = all_armor
        self._air_rider_current_armor = all_armor
        self._fencer_max_armor = all_armor
        self._fencer_current_armor = all_armor

        print("Armor after complete re-adjustment:")
        self.print_armor_info()

        with open(self.initial_adjustment_flag_filepath, 'wb') as out:
            out.write(b'\x00')

        return True

    def _subsequent_armor_adjustment(self):
        print("Armor before adjustment:")
        self.print_armor_info()

        if not self._confirm_adjustment():
            return False

        previous_min_armor = min(self._ranger_max_armor, self._wing_diver_max_armor, self._air_rider_max_armor, self._fencer_max_armor)

        new_ranger_armor = self._ranger_max_armor - previous_min_armor
        new_wing_diver_armor = self._wing_diver_max_armor - previous_min_armor
        new_air_rider_armor = self._air_rider_max_armor - previous_min_armor
        new_fencer_armor = self._fencer_max_armor - previous_min_armor
        new_armor = previous_min_armor + new_ranger_armor + new_wing_diver_armor + new_air_rider_armor + new_fencer_armor

        self._ranger_max_armor = new_armor
        self._ranger_current_armor = new_armor
        self._wing_diver_max_armor = new_armor
        self._wing_diver_current_armor = new_armor
        self._air_rider_max_armor = new_armor
        self._air_rider_current_armor = new_armor
        self._fencer_max_armor = new_armor
        self._fencer_current_armor = new_armor

        print("Armor after adjustment:")
        self.print_armor_info()

        return True

    def adjust_armor(self):
        if self._is_first_launch():
            self._initial_armor_adjustment()
        else:
            self._subsequent_armor_adjustment()


class EDFProcessHandle():
    def __init__(self):
        self.process_handle = None

    def __enter__(self):
        self.process_handle = get_edf_process_handle()
        return self.process_handle

    def __exit__(self, *args):
        win32api.CloseHandle(self.process_handle)


def backup_save():
    archive_name = "backup_{}.zip".format(datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S_%f"))

    archive_path = os.path.join(os.getcwd(), archive_name)
    if os.path.isfile(archive_path):
        raise RuntimeError("Backup file '{}' already exists, which should be impossible. Exiting.".format(archive_path))

    with zipfile.ZipFile(archive_path, 'w') as zip:
        for root, dirs, files in os.walk(SAVE_FOLDER_PATH):
            for f in files:
                filename_path = os.path.join(root, f)
                archive_path = os.path.relpath(filename_path, SAVE_FOLDER_PATH)
                zip.write(filename_path, archive_path)


def get_edf_process_handle():
    window_handle = win32gui.FindWindow(None, "EarthDefenceForce 4.1 for Windows")
    if not window_handle:
        print("No game window found.")
        return None

    thread_id, process_id = win32process.GetWindowThreadProcessId(window_handle)
    if not thread_id:
        print("Unable to get process id.")
        return None

    process_handle = win32api.OpenProcess(win32con.PROCESS_VM_WRITE | win32con.PROCESS_VM_READ | win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_OPERATION, False, process_id)
    if not process_handle:
        print("Unable to get process handle.")
        return None

    return process_handle


def get_edf_module_base_address(process_handle):
    for module_handle in win32process.EnumProcessModules(process_handle):
        module_path = win32process.GetModuleFileNameEx(process_handle, module_handle)
        if module_path.endswith('EDF41.exe'):
            return module_handle

    print("Unable to find main executable module.")
    return None


def main():
    if not os.path.exists(SAVE_FOLDER_PATH):
        raise RuntimeError("Unable to locave save folder at '{}'".format(SAVE_FOLDER_PATH))

    backup_save()

    with EDFProcessHandle() as process_handle:
        if not process_handle:
            return

        edf_module_base_address = get_edf_module_base_address(process_handle.handle)
        if not edf_module_base_address:
            return

        helper = EDFMemoryEditorHelper(process_handle, edf_module_base_address)
        if helper.adjust_armor():
            input("Done. Press <Enter> to quit.")
        else:
            input("No changes performed. Press <Enter> to quit.")


if __name__ == "__main__":
    main()
