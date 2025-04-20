"""
API Response Recorder for Canvas CLI Tests

This script captures actual responses from Canvas API and saves them as mock data
for use in the test suite. This ensures tests use realistic data structures.
"""

import json
import os
import argparse
from pathlib import Path
from canvas_cli.api import CanvasAPI
from test_base import TEST_HOST

# Create directory for mock data if it doesn't exist
MOCK_DATA_DIR = Path(__file__).parent / "mock_data"
MOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_data(data, url=None):
    """Remove or anonymize sensitive information from API responses"""
    if isinstance(data, dict):
        # If there's user data, anonymize it
        if "name" in data and "id" in data and "email" in data:
            data["name"] = f"Test User {data['id'] % 100}"
            data["email"] = f"user{data['id']}@example.com"
        
        # Process each item in the dictionary
        for key, value in list(data.items()):
            if key in ["access_token", "api_key", "password", "token", "secure_params", "uuid", "url"]:
                data[key] = "REDACTED"
            elif isinstance(value, str):
                # Anonymize URLs if provided
                if url:
                    data[key] = value.replace(url, TEST_HOST)
            elif isinstance(value, dict):
                data[key] = sanitize_data(value)
    elif isinstance(data, list):
        # Process each item in the list
        for i, item in enumerate(data):
            data[i] = sanitize_data(item)
    
    return data

def record_api_responses(url=None):
    """Record responses from Canvas API and save them as mock data"""
    print("Connecting to Canvas API...")
    try:
        api = CanvasAPI()
        print("✅ Successfully connected to Canvas API")
    except Exception as e:
        print(f"❌ Failed to connect to Canvas API: {e}")
        return
    
    # Record courses
    print("\nFetching courses...")
    try:
        courses = api.get_courses()
        if courses:
            # Limit to a small sample for tests
            sample_courses = courses[:3]
            sanitized = sanitize_data(sample_courses, url)
            
            # Save to mock data file
            with open(MOCK_DATA_DIR / "courses.json", "w") as f:
                json.dump(sanitized, f, indent=2)
            print(f"✅ Saved {len(sample_courses)} courses to mock_data/courses.json")
        else:
            print("❌ No courses found")
    except Exception as e:
        print(f"❌ Failed to fetch courses: {e}")
    
    # Choose a course for further data collection
    if courses:
        course = courses[0]
        course_id = course['id']
        course_name = course['name']
        print(f"\nUsing course: {course_name} (ID: {course_id})")
        
        # Record course details
        print("\nFetching course details...")
        try:
            course_details = api.get_course_details(course_id)
            if course_details:
                sanitized = sanitize_data(course_details, url)
                with open(MOCK_DATA_DIR / "course_details.json", "w") as f:
                    json.dump(sanitized, f, indent=2)
                print(f"✅ Saved course details to mock_data/course_details.json")
            else:
                print("❌ No course details found")
        except Exception as e:
            print(f"❌ Failed to fetch course details: {e}")
        
        # Record assignments
        print("\nFetching assignments...")
        try:
            assignments = api.get_assignments(course_id)
            if assignments:
                # Limit to a small sample for tests
                sample_assignments = assignments[:3]
                sanitized = sanitize_data(sample_assignments, url)
                with open(MOCK_DATA_DIR / "assignments.json", "w") as f:
                    json.dump(sanitized, f, indent=2)
                print(f"✅ Saved {len(sample_assignments)} assignments to mock_data/assignments.json")
                
                # Choose one assignment for further data
                if assignments:
                    assignment = assignments[0]
                    assignment_id = assignment['id']
                    assignment_name = assignment['name']
                    print(f"\nUsing assignment: {assignment_name} (ID: {assignment_id})")
                    
                    # Record assignment details
                    print("\nFetching assignment details...")
                    try:
                        assignment_details = api.get_assignment_details(course_id, assignment_id)
                        if assignment_details:
                            sanitized = sanitize_data(assignment_details, url)
                            with open(MOCK_DATA_DIR / "assignment_details.json", "w") as f:
                                json.dump(sanitized, f, indent=2)
                            print(f"✅ Saved assignment details to mock_data/assignment_details.json")
                        else:
                            print("❌ No assignment details found")
                    except Exception as e:
                        print(f"❌ Failed to fetch assignment details: {e}")
                    
                    # Record submissions if available
                    print("\nFetching submissions...")
                    try:
                        submission_data = api.get_submissions(course_id, assignment_id)
                        if submission_data:
                            sanitized = sanitize_data(submission_data, url)
                            with open(MOCK_DATA_DIR / "submission.json", "w") as f:
                                json.dump(sanitized, f, indent=2)
                            print(f"✅ Saved submission data to mock_data/submission.json")
                        else:
                            print("❌ No submission data found")
                    except Exception as e:
                        print(f"❌ Failed to fetch submission: {e}")
            else:
                print("❌ No assignments found")
        except Exception as e:
            print(f"❌ Failed to fetch assignments: {e}")
    
    print("\nMock data collection complete. Files are saved in the mock_data directory.")
    print("You can now use this data in your test suite by updating test_base.py to load these files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record API responses for Canvas CLI tests")
    parser.add_argument("--url", type=str, help="Base URL for Canvas API (optional)")
    record_api_responses(parser.parse_args().url)
