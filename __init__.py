"""
GPT's Custom Python API Interface
----------------------------------

Overview:
---------
This project delivers an advanced API designed to enhance interactions with GPT through various utilities. By leveraging this API, users can manipulate file paths, manage conversations, and execute a wide range of commands with ease.

Key Features:
-------------
1. File System Operations: Facilitates a suite of commands for interfacing with the internal file system. Users can perform actions like reading, writing, moving, copying, and deleting files within specified storage directories.

2. Conversation Management: Provides functionalities for storing and retrieving conversation logs, granting users the ability to review and analyze previous interactions.

3. Logging Capabilities: Integrates a robust logging mechanism that records user interactions, system responses, and pertinent metadata, aiding in debugging and analysis.

4. Command Execution Framework: Introduces a versatile command handling system that interprets and processes an array of commands, offering standardized results via the `CommandResult` class.

5. System Messaging: Equips the API with a messaging component that details its functions, apprising users of the supported commands and their expected JSON structures.

Core Modules:
-------------
- Constants: Establishes critical paths (e.g., `DATA_DIR`, `STORAGE_DIR`) and variables essential for the API's operation.
- CommandResult Class: Ensures a uniform format for command outcomes, enhancing consistency across varying command results.
- Logging: Incorporates the `write_to_log` function to document interactions and metadata, optimizing for repeated content and promoting system traceability.

Usage:
------
To initiate, users can dispatch commands in a structured JSON format. These commands are then directed to their corresponding execution functions, processed, and the results are returned in the `CommandResult` format.
"""
version = "0.1.1"
import config
import log
import commands
import main
