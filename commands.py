import os
import shutil

from config import CONVERSATIONS_DIR, STORAGE_DIR
from gpt import LOG_FILE, prompt, parse_filepath


def write_to_log(code_tag, user_input='', response='', **kwargs):
	global prompt
	global logged_response_count
	global response_count
	global last_logged
	lines = {"code_tag": code_tag + '[' + str(response_count) + ']', "user_input": user_input,
			 "prompt": '"' + repr(prompt.strip()) + '"',
			 "response": response}
	if logged_response_count == response_count:
		ks = list(lines)
		for k in ks:
			if last_logged.get(k, '') == lines[k]:
				del lines[k]
			else:
				last_logged[k] = lines[k]
	else:
		last_logged = lines
	text = '\n'.join([key + ':' + str(var) for d in [lines, kwargs] for key, var in d.items() if var])
	text += '\n\n'
	if logged_response_count != response_count:
		text = '\n' + '-' * 25 + '#' + str(response_count) + '\n'
		last_logged = lines

	with open(LOG_FILE, 'a') as file:
		file.write(text)
	logged_response_count = response_count


def load_conversation(filename):
	filepath = os.path.join('.', 'data', 'conversations', filename) + '.txt'
	if os.path.exists(filepath):
		with open(filepath, 'r') as file:
			return file.read().strip()
	else:
		return f"Error: {filename} not found."


def list_conversations():
	return [conversation.replace('.txt', '') for conversation in os.listdir(CONVERSATIONS_DIR)]


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
		path = os.path.join(STORAGE_DIR, path)
		with open(path, 'r') as file:
			return True, file.read()

	elif command == "fs.cp":
		src = os.path.join(STORAGE_DIR, src)
		dest = os.path.join(STORAGE_DIR, dest)
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
					all_files.append(os.path.join(dirpath, fname).replace(STORAGE_DIR, ''))
			return True, all_files
		else:
			return True, os.listdir(path)

	elif command == "fs.save":

		with open(path, 'w') as file:
			file.write(parameters["data"])
		return False, f"Saved data to {parameters['path']}"

	else:
		return True, f"Error:Invalid command: {command}"
