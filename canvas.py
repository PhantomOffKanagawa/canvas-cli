import os
import argparse
import json
import requests
from pathlib import Path

CONFIG_PATH = Path.home() / ".canvascli" / "config.json"

# Load API config
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    else:
        raise FileNotFoundError("Canvas CLI not configured. Run 'canvas config --set-token <token> --set-host <host>'")

# Save API config
def save_config(token, host):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = {"token": token, "host": host}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

# Get authorization headers
def get_headers():
    config = load_config()
    return {
        "Authorization": f"Bearer {config['token']}"
    }

# Submit assignment file
def submit_assignment(course_id, assignment_id, file_path):
    config = load_config()
    base_url = f"https://{config['host']}/api/v1"

    # Step 1: Upload file
    file_name = os.path.basename(file_path)
    size = os.path.getsize(file_path)
    upload_params = {
        "name": file_name,
        "size": size,
        "content_type": "application/octet-stream",
        "on_duplicate": "overwrite"
    }

    session_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self/files"
    session_res = requests.post(session_url, headers=get_headers(), json=upload_params)
    session_res.raise_for_status()
    upload_data = session_res.json()

    # Step 2: Upload file to upload_url
    upload_url = upload_data['upload_url']
    upload_response = requests.post(upload_url, data=upload_data['upload_params'], files={'file': open(file_path, 'rb')})
    upload_response.raise_for_status()
    file_id = upload_response.json()['id']

    # Step 3: Submit the assignment
    submit_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions"
    payload = {
        "submission": {
            "submission_type": "online_upload",
            "file_ids": [file_id]
        }
    }
    submit_res = requests.post(submit_url, headers=get_headers(), json=payload)
    submit_res.raise_for_status()
    print("Assignment submitted successfully.")

# Main CLI interface
def main():
    parser = argparse.ArgumentParser(description="Canvas CLI tool")
    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--set-token", required=True)
    config_parser.add_argument("--set-host", required=True)

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("course_id", help="Course ID")
    push_parser.add_argument("assignment_id", help="Assignment ID")
    push_parser.add_argument("--file", required=True, help="Path to the file to submit")

    args = parser.parse_args()

    if args.command == "config":
        save_config(args.set_token, args.set_host)
        print("Configuration saved.")

    elif args.command == "push":
        if not args.file:
            print("Error: --file argument is required.")
            return
        submit_assignment(args.course_id, args.assignment_id, args.file)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
