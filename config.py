"""
# Constants and Descriptions for the Custom Python API

This module provides constants and descriptions that facilitate interaction with a custom Python API. The features of this API encompass the handling of file paths and conversations, as well as the execution of various commands.

## Constants

* **DATA_DIR**: Absolute path pointing towards the primary data directory.
* **STORAGE_DIR**: Specifies the path to the storage sub-directory inside the main data directory.
* **CONVERSATIONS_DIR**: Refers to the path leading to the conversations sub-directory within the main data directory.
* **LOG_DIR**: Indicates the path for the logs sub-directory inside the primary data directory.
* **conversation_name**: Denotes the name assigned to the current conversation based on the timestamp.
* **log_filename**: Filename designed for logging, determined by the timestamp.
* **response_count**: Keeps a count of the responses provided.
* **logged_response_count**: Counts the number of responses that have been logged.
* **last_logged**: A placeholder that keeps the last logged item, stored in a dictionary format.
* **prompt**: A string placeholder reserved for any prompt.
* **COMMANDS_DICT**: A dictionary that enlists all the commands supported by the system, along with the required parameters for each.
* **SYSTEM_MESSAGE**: An introduction that elucidates the functionality of the API, detailing the supported commands and providing insights on the expected JSON structures.

"""
import datetime
import os
from typing import Dict, Any, List

# Constants
MAX_RECURSION_DEPTH = 5
DATA_DIR: str = os.path.realpath(os.path.join(os.getcwd(), 'data'))
STORAGE_DIR: str = os.path.join(DATA_DIR, 'storage')
CONVERSATIONS_DIR: str = os.path.join(DATA_DIR, 'conversations')
LOG_DIR: str = os.path.join(DATA_DIR, 'logs')
conversation_name: str = 'conversation_' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
log_filename = os.path.join(LOG_DIR, datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f") + ".txt")
response_count: int = 0
logged_response_count: int = 0
last_logged: Dict[Any, Any] = {}
prompt: str = ''

COMMANDS_DICT: Dict[str, Dict[str, Any]] = {
    "conv.ls": {
        "params": [],
        "optional_params": [],
        "description": "Lists saved conversations.",
        "returns_to_chatgpt": True
    },
    "conv.load": {
        "params": [],
        "optional_params": ["name"],
        "description": "Retrieves content of a specified conversation file.",
        "returns_to_chatgpt": True
    },
    "conv.save": {
        "params": [],
        "optional_params": ["name"],
        "description": "Saves the current conversation.",
        "returns_to_chatgpt": False
    },
    "fs.cat": {
        "params": ["path"],
        "optional_params": [],
        "description": "Displays the contents of the specified file.",
        "returns_to_chatgpt": True
    },
    "fs.cp": {
        "params": ["src", "destination"],
        "optional_params": [],
        "description": "Copies the source file or directory to the specified destination.",
        "returns_to_chatgpt": False
    },
    "fs.mv": {
        "params": ["src", "dest"],
        "optional_params": [],
        "description": "Moves or renames the source file or directory to the specified destination.",
        "returns_to_chatgpt": False
    },
    "fs.rm": {
        "params": ["path"],
        "optional_params": ["recursive"],
        "description": "Removes the specified file or directory. If 'recursive' is set to true, it will recursively remove directories and their contents.",
        "returns_to_chatgpt": False
    },
    "fs.touch": {
        "params": ["path"],
        "optional_params": [],
        "description": "Creates a new empty file with the given filename.",
        "returns_to_chatgpt": False
    },
    "fs.mkdir": {
        "params": ["path"],
        "optional_params": [],
        "description": "Creates a new directory in the storage space.",
        "returns_to_chatgpt": False
    },
    "fs.rmdir": {
        "params": ["path"],
        "optional_params": [],
        "description": "Removes the specified directory. Note: This will only remove empty directories.",
        "returns_to_chatgpt": False
    },
    "fs.ls": {
        "params": [],
        "optional_params": ["path", "recursive"],
        "description": "Lists contents in the storage directory or a specified path. If 'recursive' is set to true, it lists all files and directories under the specified path recursively.",
        "returns_to_chatgpt": True
    },
    "fs.save": {
        "params": ["path", "data"],
        "optional_params": [],
        "description": "Saves provided data to the specified filename.",
        "returns_to_chatgpt": False
    }
}

_SYSTEM_MESSAGE_INTRO: str = '''Hello! You are an efficient assistant with the ability to interact with a custom python API. When sending a query or request, 
create a valid JSON object to be parsed by the API. Regardless of the question, make sure to follow this structure in your answer. EVERY SINGLE RESPONSE SHOULD BE READABLE BY json.loads(json_response)
The response create a valid JSON array of objects:
	
		"commands": [
			{
				"commandName": "SpecificCommand",
				"parameters": {
					"paramKey1": "value1",
					"paramKey2": "value2",
					// ... any additional parameters
				}
			},
			// ... any additional command structures as needed
		], 
		"user": "Message or response meant for the user"
	}
'''


def generate_system_message() -> str:
    commands_section = "**Supported Commands:**\n"
    for cmd, details in COMMANDS_DICT.items():
        commands_section += f"- `{cmd}:{{}}`: \n\t- Description: {details['description']}\n"
    return _SYSTEM_MESSAGE_INTRO + commands_section


# Update the SYSTEM_MESSAGE after the COMMANDS_DICT has been fully updated.
SYSTEM_MESSAGE = generate_system_message()
