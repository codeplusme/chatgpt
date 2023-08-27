import os
import shutil

import config


def parse_filepath(*fps):
	retval = ""

	if fps:
		paths = fps
		paths = [path2[:-1] if (path2 and path2[-1] in ['/', '\\']) else path2 for path2 in paths]
		paths = [path2[1:] if path2 and path2[0] in ['/', '\\'] else path2 for path2 in paths]
		paths = [path2 for path2 in paths if path2]

		for fp in paths:
			retval = os.path.join(retval, fp)
		retval = os.path.realpath(retval)
	return retval


def load_conversation(filename):
	filepath = os.path.join('.', 'data', 'conversations', filename) + '.txt'
	if os.path.exists(filepath):
		with open(filepath, 'r') as file:
			return file.read().strip()
	else:
		return f"Error: {filename} not found."


def list_conversations():
	return [conversation.replace('.txt', '') for conversation in os.listdir(config.CONVERSATIONS_DIR)]


def save_conversation(filename):
	filepath = os.path.join('.', 'data', 'conversations', filename + '.txt')
	with open(filepath, 'w') as file:
		file.write(prompt)
	return f"Conversation saved as {filename}."


def execute_fs_command(command, parameters):
	"""

	@param command:
	@param parameters:
	@return:
	"""
	recursive = parameters.get("recursive", "false")
	recursive = str(recursive).lower() == "true"
	path = parse_filepath(parameters.get("path", ''))
	src = parse_filepath(parameters.get("src", ''))
	dest = parse_filepath(parameters.get("dest", ''))
	if command == "fs.cat":
		path = os.path.join(config.STORAGE_DIR, path)
		with open(path, 'r') as file:
			return True, file.read()

	elif command == "fs.cp":
		src = os.path.join(config.STORAGE_DIR, src)
		dest = os.path.join(config.STORAGE_DIR, dest)
		if os.path.isdir(src):
			shutil.copytree(src, dest)
		else:
			shutil.copy2(src, dest)
		return False, f"Copied {parameters['src']} to {parameters['dest']}"

	elif command == "fs.mv":
		shutil.move(src, dest)
		return False, f"Moved/Renamed {parameters['src']} to {parameters['dest']}"

	elif command == "fs.rm":
		if parse_filepath('storage', '') == path:
			return True, 'Error: Cannot delete '
		if not path.endswith('*'):
			paths = [path]
		else:
			paths = os.listdir(os.path.dirname(path))
		for child in paths:
			if recursive and os.path.isdir(child):
				shutil.rmtree(child)
			else:
				os.remove(child)

		return False, f"Removed {parameters['path']}"

	elif command == "fs.touch":
		with open(path, 'a'):
			os.utime(path, None)
		return False, f"Created {parameters['path']}"

	elif command == "fs.mkdir":
		os.makedirs(path, exist_ok=True)
		return False, f"Created directory {parameters['path']}"

	elif command == "fs.rmdir":
		if parse_filepath('storage', '') == path:
			return 'Error: Cannot delete base directory.'
		os.rmdir(path)  # Note: This will only remove empty directories.
		return False, f"Removed directory {parameters['path']}"

	elif command == "fs.ls":

		path = parse_filepath('storage', parameters.get("path", ""))
		if recursive:
			all_files = []
			for dirpath, dirnames, filenames in os.walk(path):
				for fname in filenames:
					all_files.append(os.path.join(dirpath, fname).replace(config.STORAGE_DIR, ''))
			return True, all_files
		else:
			return True, os.listdir(path)

	elif command == "fs.save":

		with open(path, 'w') as file:
			file.write(parameters["data"])
		return False, f"Saved data to {parameters['path']}"

	else:
		return True, f"Error:Invalid command: {command}"
