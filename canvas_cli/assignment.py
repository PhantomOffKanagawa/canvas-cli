import os
import requests
from pathlib import Path
from .config import Config
import sys
import time

def spinner(msg, duration=2):
    """Simple spinner for CLI feedback."""
    spinner_chars = "|/-\\"
    sys.stdout.write(msg)
    sys.stdout.flush()
    for _ in range(duration * 10):
        sys.stdout.write(spinner_chars[_ % 4])
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')
    sys.stdout.write("done\n")

def submit_assignment(course_id, assignment_id, file_path):
    """Submit assignment file to Canvas"""
    config = Config.load_global()
    
    # Check if global configuration is set
    if not config:
        print("Error: Global configuration not found.")
        print("Please run 'canvas config set --global token <token>' and 'canvas config set --global host <host>' to set them.")
        return
    
    # Check if token and host are set in the configuration
    if not config.get("token") or not config.get("host"):
        print("Error: Missing token or host in configuration.")
        print("Please run 'canvas config set --global token <token>' and 'canvas config set --global host <host>' to set them.")
        return

    base_url = f"https://{config['host']}/api/v1"

    # Follow Canvas LMS API Flow (https://developerdocs.instructure.com/services/canvas/basics/file.file_uploads)
    # Step 1: Telling canvas about the file upload and getting a token
    file_name = os.path.basename(file_path)
    size = os.path.getsize(file_path)
    upload_params = {
        "name": file_name,
        "size": size,
        "content_type": "application/octet-stream", # May need to be dependent for limited submissions
        "on_duplicate": "overwrite"
    }

    print("Step 1/3: Requesting upload session...", end=' ')
    spinner("", 1)

    # POST to relevent API endpoint
    # With the name, size in bytes, content type,
    session_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self/files"
    session_res = requests.post(session_url, headers=Config.get_headers(), json=upload_params)
    session_res.raise_for_status()
    upload_data = session_res.json()

    # Step 2: Upload file data to the URL given in the previous response
    print("Step 2/3: Uploading file...", end=' ')
    spinner("", 2)

    # The upload URL and parameters are in the response
    # The upload URL is a temporary URL for the file upload
    upload_url = upload_data['upload_url']
    # Upload following the parameters given in the response
    with open(file_path, 'rb') as f:
        upload_response = requests.post(upload_url, data=upload_data['upload_params'], files={'file': f})
    upload_response.raise_for_status()
    file_id = upload_response.json()['id']

    # Step 3: Submit the assignment
    print("Step 3/3: Submitting assignment...", end=' ')
    spinner("", 1)

    # The file ID is used to submit the assignment
    # The submission URL is the same as the one used to get the upload session
    submit_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions"
    payload = {
        "submission": {
            "submission_type": "online_upload",
            "file_ids": [file_id]
        }
    }
    submit_res = requests.post(submit_url, headers=Config.get_headers(), json=payload)
    submit_res.raise_for_status()
    print("Assignment submitted successfully.")
