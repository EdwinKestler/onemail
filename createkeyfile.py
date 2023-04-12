
"""
this is the createkeyfile.py file, it creates the key.key file inthe desired directory
    
    """
import os
from pathlib import Path
from cryptography.fernet import Fernet

# Get the user's Documents folder
documents_folder = os.path.join(Path.home(), "Documents")

# Create the onemail folder inside Documents if it does not exist
onemail_folder = os.path.join(documents_folder, "onemail")
Path(onemail_folder).mkdir(parents=True, exist_ok=True)

# Generate and save the key to the onemail folder
key = Fernet.generate_key()
key_file_path = os.path.join(onemail_folder, "key.key")
with open(key_file_path, "wb") as key_file:
    key_file.write(key)