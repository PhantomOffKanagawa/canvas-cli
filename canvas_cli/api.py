import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from canvas_cli.handler_helper import echo
from handlers.config_handler import get_key_static
import typer

class CanvasAPI:
    """Main class for interacting with the Canvas API"""
    
    @property
    def base_url(self):
        """Return the base URL for the Canvas API, computed each time it's accessed"""
        return f"https://{self.host}/api/v1"
    
    @property
    def headers(self):
        """Return the headers for the Canvas API, computed each time it's accessed"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
    @property
    def token(self):
        """Return the API token for the Canvas API, computed each time it's accessed"""
        return get_key_static('token')
    
    @property
    def host(self):
        """Return the host for the Canvas API, computed each time it's accessed"""
        return get_key_static('host')
    
    def __init__(self, ctx: typer.Context):
        """Initialize the Canvas API client"""

        # Cache Settings
        self.cache = {}  # Cache for storing API responses
        self.cache_expiry = 60 * 5  # Cache expiry time in seconds (5 minutes)
        self.cache_time = {}  # Cache time for each endpoint
        
        # Initialize the context
        self.ctx = ctx
        
    def get_submissions(self, course_id: int, assignment_id: int, props: dict | None = None) -> Dict:
        """Get the current user's submission for an assignment
        
        Args:
            course_id: The Canvas course ID
            assignment_id: The Canvas assignment ID
            
        Returns:
            Submission dictionary or empty dict on error
        """
        
        # Check if token and host are set in the configuration
        if not self.token or not self.host:
            echo("Error: Missing token or host in configuration.", ctx=self.ctx, level="error")
            echo("Please run 'canvas config set --global token <token>' and 'canvas config set --global host <host>' to set them.", ctx=self.ctx, level="error")
            return {}
        
        # Check if course_id and assignment_id are provided
        if not course_id or not assignment_id:
            echo("Error: Missing course_id or assignment_id.", ctx=self.ctx, level="error")
            return {}
        
        # Check if submission is already cached and not expired
        cache_key = f"submission_{course_id}_{assignment_id}"
        if cache_key in self.cache and (datetime.now() - self.cache_time.get(cache_key, datetime.min)).total_seconds() < self.cache_expiry:
            return self.cache[cache_key]

        # Default params
        if props is None:
            props = {
                'include[]': ['submission_history', 'submission_comments', 'submission_html_comments', 'rubric_assessment',
                              'assignment', 'visibility', 'course', 'user', 'group', 'read_status', 'student_entered_score'],
            }
            
        try:
            url = f"{self.base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self"
            response = requests.get(url, headers=self.headers, params=props)
            response.raise_for_status()
            submission_data = response.json()
            
            # Cache the submission data
            self.cache[cache_key] = submission_data
            self.cache_time[cache_key] = datetime.now()
            
            return submission_data
        except requests.RequestException as e:
            print(f"Error fetching submission: {e}")
            return {}

    def submit_assignment(self, course_id, assignment_id, file_path):
        """Submit assignment file to Canvas
        
        Args:
            course_id: The Canvas course ID
            assignment_id: The Canvas assignment ID
            file_path: The path to the file to be submitted
        
        Returns:
            None
        """

        # Check if token and host are set in the configuration
        if not self.token or not self.host:
            echo("Error: Missing token or host in configuration.", ctx=self.ctx, level="error")
            echo("Please run 'canvas config set --global token <token>' and 'canvas config set --global host <host>' to set them.", ctx=self.ctx, level="error")
            return
        
        # Check if course_id and assignment_id are provided
        if not course_id or not assignment_id:
            echo("Error: Missing course_id or assignment_id.", ctx=self.ctx, level="error")
            return
        
        # Check if the file exists
        if not os.path.exists(file_path):
            echo(f"Error: File '{file_path}' does not exist.", ctx=self.ctx, level="error")
            return

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

        echo("Step 1/3: Requesting upload session...", ctx=self.ctx)

        # POST to relevent API endpoint
        # With the name, size in bytes, content type,
        session_url = f"{self.base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self/files"
        session_res = requests.post(session_url, headers=self.headers, json=upload_params)
        session_res.raise_for_status()
        upload_data = session_res.json()

        # Step 2: Upload file data to the URL given in the previous response
        echo("Step 2/3: Uploading file...", ctx=self.ctx)

        # The upload URL and parameters are in the response
        # The upload URL is a temporary URL for the file upload
        upload_url = upload_data['upload_url']
        # Upload following the parameters given in the response
        with open(file_path, 'rb') as f:
            upload_response = requests.post(upload_url, data=upload_data['upload_params'], files={'file': f})
        upload_response.raise_for_status()
        file_id = upload_response.json()['id']

        # Step 3: Submit the assignment
        echo("Step 3/3: Submitting assignment...", ctx=self.ctx)

        # The file ID is used to submit the assignment
        # The submission URL is the same as the one used to get the upload session
        submit_url = f"{self.base_url}/courses/{course_id}/assignments/{assignment_id}/submissions"
        payload = {
            "submission": {
                "submission_type": "online_upload",
                "file_ids": [file_id]
            }
        }
        
        # Submit the assignment with the file ID
        # The payload is a JSON object with the file ID
        # The file ID is used to submit the assignment
        submit_res = requests.post(submit_url, headers=self.headers, json=payload)
        submit_res.raise_for_status()
        echo("Assignment submitted successfully.", ctx=self.ctx)
        
    # Helper functions for formatting API data
    @staticmethod
    def format_date(date_str):
        """Format a date string nicely
        
        Args:
            date_str: ISO format date string from Canvas API
            
        Returns:
            Formatted date string
        """
        if not date_str:
            return "No date specified"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return date_str

    @staticmethod
    def download_file(url: str, file_path: str, overwrite: bool = False) -> None | requests.Response:
        """Download a file from a URL

        Args:
            url: URL of the file to download
            file_path: Path to save the downloaded file
            overwrite: Flag to indicate whether to overwrite the file if it exists

        Returns:
            None | requests.Response: Response object if the download is successful, None otherwise
        """
        if not overwrite and os.path.exists(file_path):
            print(f"File {file_path} already exists. Overwrite? (y/N): ", end='')
            
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                return None

        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return response