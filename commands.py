"""
gpt's Custom Python API
------------------------

This module provides an interface to interact with file paths and manage conversations. It's equipped with command execution capabilities and various utilities to assist in handling file-related operations and conversation-based actions.

"""
import os

import shutil
import config
from dataclasses import dataclass


@dataclass
class CommandResult:
	"""
	Represents the result of a command's execution.

	:param success: Indicates if the command was successful.
	:type success: bool
	:param message: A message associated with the command's execution.
	:type message: str
	:param value: A value that may be returned from successful command execution. Default is None.
	:type value: Any, optional
	"""

	def __init__(self, success: bool, message: str, value=None):
		self.success = success
		self.message = message
		self.value = value

	def to_dict(self):
		return {
			"success": self.success,
			"message": self.message,
			"value": self.value
		}


def sanitize_path(*fps: str) -> str:
	"""
	Obtains the absolute path from given file paths.

	:param fps: The file paths to combine and sanitize.
	:type fps: str
	:return: The sanitized absolute path.
	:rtype: str
	"""

	combined = os.path.join(*fps)
	if not os.path.isabs(combined):  # Check if the path is not absolute
		combined = os.path.join(config.STORAGE_DIR, combined)
	return os.path.realpath(combined)


def execute_fs_command(command: str, parameters: dict) -> CommandResult:
	"""
	Handle file-based operations like reading, copying, moving, and others.

	:param command: The type of file operation to perform (e.g., "fs.cat", "fs.cp").
	:type command: str
	:param parameters: The parameters needed for the specific operation.
	:type parameters: dict
	:return: The result of the command's execution, encapsulated in a CommandResult object.
	:rtype: CommandResult
	"""
	try:
		path: str = sanitize_path(parameters.get("path", ''))
		src = sanitize_path(parameters.get("src", ''))
		dest = sanitize_path(parameters.get("dest", parameters.get("destination", '')))
		recursive = parameters.get("recursive", False)

		if command == "fs.cat":
			with open(path) as file:
				return CommandResult(True, "File read successfully.", file.read())

		elif command == "fs.cp":
			if os.path.isdir(src):
				shutil.copytree(src, dest)
			else:
				shutil.copy2(src, dest)
			return CommandResult(True, f"Copied to {parameters.get('dest', dest)}")

		elif command == "fs.mv":
			shutil.move(src, dest)
			return CommandResult(True, f"Moved/Renamed {parameters['src']} to {parameters.get('dest', dest)}")

		elif command == "fs.rm":
			if sanitize_path('storage', '') == path:
				return CommandResult(False, 'Error: Cannot delete storage root.')
			if recursive and os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
			return CommandResult(True, f"Removed {parameters['path']}")

		elif command == "fs.touch":
			with open(path, 'a'):
				os.utime(path, None)
			return CommandResult(True, f"Created {parameters['path']}")

		elif command == "fs.mkdir":
			os.makedirs(path, exist_ok=True)
			return CommandResult(True, f"Created directory {parameters['path']}")

		elif command == "fs.rmdir":
			if sanitize_path('storage', '') == path:
				return CommandResult(False, 'Error: Cannot delete storage root.')
			os.rmdir(path)  # Note: This will only remove empty directories.
			return CommandResult(True, f"Removed directory {parameters['path']}")

		elif command == "fs.ls":
			path = sanitize_path(parameters.get("path", ""))
			if recursive:
				all_files = []
				for dirpath, dirnames, filenames in os.walk(path):
					for fname in filenames:
						all_files.append(os.path.join(dirpath, fname).replace(config.STORAGE_DIR, ''))
				return CommandResult(True, "Listing completed.", all_files)
			else:
				return CommandResult(True, "Listing completed.", os.listdir(path))

		elif command == "fs.save":
			with open(path, 'w') as file:
				file.write(parameters["data"])
			return CommandResult(True, f"Saved data to {parameters['path']}")

		else:
			return CommandResult(False, "Invalid command.")

	except Exception as e:
		return CommandResult(False, str(e))


def execute_conv_command(command: str, parameters: dict) -> CommandResult:
	"""
	Handles conversation-based commands like saving, loading, and listing conversations.

	:param command: The type of conversation operation to perform (e.g., "conv.save", "conv.load").
	:type command: str
	:param parameters: The parameters needed for the specific operation.
	:type parameters: dict
	:return: The result of the command's execution, encapsulated in a CommandResult object.
	:rtype: CommandResult
	"""
	try:
		conversation_name = parameters.get('name', config.conversation_name)
		filepath = os.path.join(config.CONVERSATIONS_DIR, f"{conversation_name}.txt")

		if command == 'conv.save':

			return CommandResult(True, f"Conversation saved as {conversation_name}.", save_conversation(filepath))

		elif command == 'conv.load':
			if os.path.exists(filepath):
				with open(filepath) as file:
					return CommandResult(True, f"Loaded conversation {conversation_name}.", file.read().strip())
			else:
				return CommandResult(False, f"Error: {conversation_name} not found.")

		elif command == 'conv.ls':
			return CommandResult(True, "Conversations listed successfully.", list_convsersations)

		else:
			return CommandResult(False, "Invalid command.")

	except Exception as e:
		return CommandResult(False, str(e))


def save_conversation(conversation_name: str = ''):
	conversation_name = conversation_name if conversation_name else config.conversation_name
	filepath = os.path.join(config.CONVERSATIONS_DIR, f"{conversation_name}.txt")
	with open(filepath, 'w') as file:
		file.write(config.prompt)


def list_convsersations():
	return [conversation.replace('.txt', '') for conversation in os.listdir(config.CONVERSATIONS_DIR)]


def validate_command(command_obj: object) -> object:
	"""
	Validates and prepares a command for execution.

	:param command_obj: The command object to validate.
	:type command_obj: object
	:return: An error message if validation fails, otherwise an empty string. Also returns the prepared parameters.
	:rtype: object
	"""
	if not isinstance(command_obj, dict):
		return f'Error: Unable to parse command: "{command_obj}".\n', {}

	command = command_obj.get("commandName", "")
	parameters = command_obj.get("parameters", {})

	if not isinstance(parameters, dict):
		parameters = {str(parameters): ""}

	if command not in config.COMMANDS_DICT:
		return f'Error: Command not found: "{command}".\n', {}

	required_params = config.COMMANDS_DICT[command]['params']
	missing_params = [param for param in required_params if param not in parameters]

	if missing_params:
		return f"Error: Missing parameters for {command}: {', '.join(missing_params)}.\n", {}

	# Check for extraneous parameters
	optional_params = config.COMMANDS_DICT[command].get('optional_params', [])
	allowed_params = set(required_params + optional_params)
	extraneous_params = [param for param in parameters if param not in allowed_params]

	if extraneous_params:
		return f"Error: Unexpected parameters for {command}: {', '.join(extraneous_params)}.\n", {}

	return "", parameters


def route_and_execute_command(command: str, parameters: dict) -> CommandResult:
	"""
	Routes the command to its corresponding executor and executes it.

	:param command: The type of command to route and execute.
	:type command: str
	:param parameters: The parameters needed for the specific command.
	:type parameters: dict
	:return: The result of the command's execution, encapsulated in a CommandResult object.
	:rtype: CommandResult
	"""
	if command.startswith("fs."):
		return execute_fs_command(command, parameters)
	elif command.startswith("conv."):
		return execute_conv_command(command, parameters)
	else:
		return CommandResult(False, "Command not found")


def execute_commands(response: dict) -> dict:
	"""
	Processes the response, identifies commands, and executes them.

	:param response: The response dictionary containing potential commands.
	:type response: dict
	:return: Dictionary containing results of the executed commands, any errors encountered, and a flag indicating further interactions.
	:rtype: dict
	"""
	commands_list = response.get('commands', [])
	results = {}
	errors = []
	for command_obj in commands_list:
		command_name = command_obj.get("commandName", "")

		# Validate and prepare the command for execution.
		error_msg, prepared_params = validate_command(command_obj)

		if error_msg:
			errors.append(error_msg)
			continue

		command_result = route_and_execute_command(command_name, prepared_params)

		# Storing the results
		results[command_name] = command_result.to_dict()

	return {
		"errors": errors,
		"results": results,
		"return_flag": True  # Modify this based on your requirements.
	}
