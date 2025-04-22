"""
API module for Canvas CLI
Handles communication with the Canvas REST API
"""

import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from .config import Config

class CanvasAPI:
    """Main class for interacting with the Canvas API"""
    
    def __init__(self):
        """Initialize the Canvas API client"""
        config = Config.load_global()
        if not config:
            raise ValueError("Canvas CLI not configured. Run 'canvas config set --global token <token>' and 'canvas config set --global host <host>'.")
        
        self.token = config.get('token')
        self.host = config.get('host')
        
        if not self.token or not self.host:
            raise ValueError("Canvas API token or host not configured.")
            
        self.base_url = f"https://{self.host}/api/v1"
        self.headers = {"Authorization": f"Bearer {self.token}"}

        self.cache = {}  # Cache for storing API responses
        self.cache_expiry = 60 * 5  # Cache expiry time in seconds (5 minutes)
        self.cache_time = {}  # Cache time for each endpoint
        
    def get_canvas_page(self, url: str, params: dict | None = None) -> Optional[Dict]:
        """Get a page from the Canvas API
        
        Args:
            url: The URL to fetch
            params: Additional parameters for the request
        
        Returns:
            JSON response as a dictionary or None on error
        """
        if params is None:
            params = {}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None
    
    def get_courses(self, params: dict | None = None) -> List[Dict]:
        """Get list of courses from Canvas API
        
        Returns:
            List of course dictionaries
        """

        # Check if courses are already cached and not expired
        if 'courses' in self.cache and (datetime.now() - self.cache_time.get('courses', datetime.min)).total_seconds() < self.cache_expiry:
            return self.cache['courses']

        url = f"{self.base_url}/courses"
        if params is None:
            params = {
                'enrollment_state': 'active',
                'include[]': 'favorites',
                'per_page': 100 # TODO: Handle pagination if needed
            }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            courses = response.json()
            
            # Filter out courses without a name (likely access restricted)
            valid_courses = [c for c in courses if 'name' in c]
            
            # Sort by favorite status first, then by name
            sorted_courses = sorted(valid_courses, 
                                   key=lambda c: (not c.get('is_favorite', False), c.get('name', '')))
            
            # Cache the courses
            self.cache['courses'] = sorted_courses
            self.cache_time['courses'] = datetime.now()
            return sorted_courses
        except requests.RequestException as e:
            print(f"Error fetching courses: {e}")
            return []
    
    def get_assignments(self, course_id: int, params: dict | None = None) -> List[Dict]:
        """Get list of assignments for a course from Canvas API
        
        Args:
            course_id: The Canvas course ID
            
        Returns:
            List of assignment dictionaries
        """

        # Check if assignments are already cached and not expired
        cache_key = f"assignments_{course_id}"
        if cache_key in self.cache and (datetime.now() - self.cache_time.get(cache_key, datetime.min)).total_seconds() < self.cache_expiry:
            return self.cache[cache_key]

        url = f"{self.base_url}/courses/{course_id}/assignments"

        
        if params is None:
            params = {'per_page': 100} # TODO: Handle pagination if needed
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            assignments = response.json()
            
            # Filter out assignments that cannot be submitted
            valid_assignments = [a for a in assignments if a.get('submission_types') and 'online_upload' in a.get('submission_types')]
            
            # Categorize assignments by status
            now = datetime.now().isoformat()
            future_unsubmitted = []  # Not submitted, not past due
            future_submitted = []    # Submitted, not past due
            past_unsubmitted = []    # Not submitted, past due
            past_submitted = []      # Submitted, past due
            locked = []              # Locked assignments
            
            for a in valid_assignments:
                submitted = a.get('has_submitted_submissions', False)
                due_at = a.get('due_at')
                lock_at = a.get('lock_at')
                
                # Check if assignment is locked
                is_locked = (lock_at and lock_at < now)
                
                # Check if assignment is past due
                past_due = (due_at and due_at < now)
                
                # Sort into appropriate category based on due date and submission status
                if is_locked:
                    locked.append(a)
                elif not past_due and not submitted:
                    future_unsubmitted.append(a)
                elif not past_due and submitted:
                    future_submitted.append(a)
                elif past_due and not submitted:
                    past_unsubmitted.append(a)
                else:  # past_due and submitted
                    past_submitted.append(a)
            
            # Sort each category by due date
            for assignment_list in [future_unsubmitted, future_submitted, past_unsubmitted, past_submitted, locked]:
                assignment_list.sort(key=lambda a: a.get('due_at') or '9999-12-31')
            
            # Combine lists with priority order
            sorted_assignments = future_unsubmitted + future_submitted + past_unsubmitted + past_submitted + locked
            self.cache[cache_key] = sorted_assignments
            self.cache_time[cache_key] = datetime.now()
            return sorted_assignments
        except requests.RequestException as e:
            print(f"Error fetching assignments: {e}")
            return []
    
    def get_course_details(self, course_id: int, props: dict | None = None) -> Dict:
        """Get detailed information about a course
        
        Args:
            course_id: The Canvas course ID
            props: Additional properties to fetch (optional)
            
        Returns:
            Course dictionary or empty dict on error
        """
        # Check if course details are already cached and not expired
        cache_key = f"course_{course_id}"
        if cache_key in self.cache and (datetime.now() - self.cache_time.get(cache_key, datetime.min)).total_seconds() < self.cache_expiry:
            return self.cache[cache_key]

        # Default params
        if props is None:
            props = {}

        try:
            url = f"{self.base_url}/courses/{course_id}"
            response = requests.get(url, headers=self.headers, params=props)
            response.raise_for_status()
            course_details = response.json()
            
            # Cache the course details
            self.cache[cache_key] = course_details
            self.cache_time[cache_key] = datetime.now()

            return course_details
        except requests.RequestException as e:
            print(f"Error fetching course details: {e}")
            return {}
    
    def get_assignment_details(self, course_id: int, assignment_id: int, props: dict | None = None) -> Dict:
        """Get detailed information about an assignment
        
        Args:
            course_id: The Canvas course ID
            assignment_id: The Canvas assignment ID
            
        Returns:
            Assignment dictionary or empty dict on error
        """
        # Check if assignment details are already cached and not expired
        cache_key = f"assignment_{course_id}_{assignment_id}"
        if cache_key in self.cache and (datetime.now() - self.cache_time.get(cache_key, datetime.min)).total_seconds() < self.cache_expiry:
            return self.cache[cache_key]

        # Default params
        if props is None:
            props = {
                'include[]': ['submission', 'score_statistics', 'can_edit'],
            }

        try:
            url = f"{self.base_url}/courses/{course_id}/assignments/{assignment_id}"
            response = requests.get(url, headers=self.headers, params=props)
            response.raise_for_status()
            assignment_details = response.json()
            
            # Cache the assignment details
            self.cache[cache_key] = assignment_details
            self.cache_time[cache_key] = datetime.now()
            
            return assignment_details
        except requests.RequestException as e:
            print(f"Error fetching assignment details: {e}")
            return {}
    
    def get_submissions(self, course_id: int, assignment_id: int, props: dict | None = None) -> Dict:
        """Get the current user's submission for an assignment
        
        Args:
            course_id: The Canvas course ID
            assignment_id: The Canvas assignment ID
            
        Returns:
            Submission dictionary or empty dict on error
        """
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

    # POST to relevent API endpoint
    # With the name, size in bytes, content type,
    session_url = f"{base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self/files"
    session_res = requests.post(session_url, headers=Config.get_headers(), json=upload_params)
    session_res.raise_for_status()
    upload_data = session_res.json()

    # Step 2: Upload file data to the URL given in the previous response
    print("Step 2/3: Uploading file...", end=' ')

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

# Helper functions for formatting API data
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

def download_file(url: str, file_path: str, overwrite: bool = False) -> None | requests.Response:
    """Download a file from a URL

    Args:
        url: URL of the file to download
        file_path: Path to save the downloaded file
        overwrite: Flag to indicate whether to overwrite the file if it exists

    Returns:
        None
    """
    if not overwrite and os.path.exists(file_path):
        print(f"File {file_path} already exists. Overwrite? (y/N): ", end='')
        
        response = input().strip().lower()
        if response not in ['y', 'yes']:
            return

    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    return response