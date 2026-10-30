"""Keep user pronunciation dictionaries when replacing an older add-on.

Older releases allowed dictionaries to be placed beside the synthesizer
driver. NVDA removes that directory while updating the add-on, so copy those
files to the persistent user configuration directory before the replacement
is activated. Existing files in the persistent location always take priority.
"""

import configparser
import os
import shutil


def onInstall():
	try:
		import globalVars

		config_path = globalVars.appArgs.configPath
	except Exception:
		return
	if not config_path:
		return

	addons_path = os.path.join(config_path, "addons")
	new_addon_path = os.path.dirname(os.path.abspath(__file__))
	destination = os.path.join(config_path, "openevv", "dictionaries")
	to_copy = []

	try:
		candidates = os.listdir(addons_path)
	except OSError:
		return

	for candidate in candidates:
		old_addon_path = os.path.join(addons_path, candidate)
		if not os.path.isdir(old_addon_path):
			continue
		if os.path.normcase(os.path.abspath(old_addon_path)) == os.path.normcase(new_addon_path):
			continue

		manifest_path = os.path.join(old_addon_path, "manifest.ini")
		manifest = configparser.ConfigParser()
		try:
			with open(manifest_path, "r", encoding="utf-8") as manifest_file:
				manifest.read_string("[addon]\n" + manifest_file.read())
			if manifest.get("addon", "name", fallback="").lower() != "openevv":
				continue
		except (OSError, configparser.Error):
			continue

		driver_path = os.path.join(old_addon_path, "synthDrivers")
		try:
			filenames = os.listdir(driver_path)
		except OSError:
			continue
		for filename in filenames:
			if filename.lower().endswith(".dic"):
				path = os.path.join(driver_path, filename)
				if os.path.isfile(path):
					to_copy.append((path, os.path.join(destination, filename)))

	if not to_copy:
		return

	os.makedirs(destination, exist_ok=True)
	for source, target in to_copy:
		if os.path.exists(target):
			continue
		# An error must abort the install: NVDA will then keep the old add-on
		# directory, which still contains the dictionary that could not be copied.
		shutil.copy2(source, target)
