# Copyright (c) 2019 - 2022 Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import sys
import os
from os.path import join as P
import shutil
from subprocess import run

#------------------------------------------------------------
# Config

addon_list = [
	"LilySurfaceScraper",
]

#------------------------------------------------------------
# Main

def main():
	with cd(this_scripts_directory()):
		addon = "LilySurfaceScraper"
		addon_path = P("blender", addon)
		version = get_addon_version(addon_path)
		zip(addon_path, P("releases", f"{addon}-v{version}"))

		print(f"Done! You may install in Blender the addon releases/{addon}-v{version}.zip.")

#------------------------------------------------------------
# Utils

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, directory):
        self.directory = os.path.expanduser(directory)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.directory)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

def ensure_dir(directory):
	os.makedirs(directory, exist_ok=True)

def zip(directory, zipfile):
	"""compresses a directory into a zip file"""
	print(f"Zipping {directory} into {zipfile}...")
	directory = os.path.realpath(directory)
	parent = os.path.dirname(directory)
	base = os.path.basename(directory)
	shutil.make_archive(zipfile, 'zip', parent, base)

def get_addon_version(addon_directory):
	"""Extract the version of the addon from its init file"""
	with open(P(addon_directory, "__init__.py"), 'r') as f:
		text = f.read()
	bl_info = eval(text[text.find("{"):text.find("}")+1])
	return "{}.{}.{}".format(*bl_info["version"])

def this_scripts_directory():
	return os.path.dirname(os.path.realpath(__file__))

def find_python39():
	path_sep = ";" if sys.platform == "win32" else ":"
	python_exe = "python.exe" if sys.platform == "win32" else "python"
	python3_exe = "python3.exe" if sys.platform == "win32" else "python3"
	path = os.environ["PATH"].split(path_sep)
	for p in path:
		try:
			files = os.listdir(p)
		except FileNotFoundError:
			continue
		full_python_exe = None
		if python_exe in files:
			full_python_exe = os.path.join(p, python_exe)
		if python3_exe in files:
			full_python_exe = os.path.join(p, python3_exe)
		if full_python_exe is not None:
			ret = run([full_python_exe, "--version"], capture_output=True)
			if ret.stdout.startswith(b"Python 3.9"):
				return full_python_exe
	print("Could not find Python 3.9 in your PATH!")
	exit(1)

#------------------------------------------------------------

main()
