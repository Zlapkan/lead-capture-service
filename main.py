# main.py (EXTREME DEBUGGING VERSION - VERY SIMPLE)
import functions_framework
import os # Keep os for potential future use, but don't call it yet

print("DEBUG: main.py - Script started, imports complete.")

@functions_framework.http
def process_quiz_submission(request):
    """
    A very simple HTTP function for debugging startup.
    """
    print("DEBUG: process_quiz_submission - Function called.")
    
    # For now, just return a simple success message.
    # We are only testing if the server can start and respond.
    cors_headers = {'Access-Control-Allow-Origin': '*'}
    
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST', # Or GET if we change the test
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        print("DEBUG: Responding to OPTIONS request.")
        return ('', 204, headers)

    print("DEBUG: Responding to main request (e.g., POST or GET).")
    return ('Simplified function is alive!', 200, cors_headers)

print("DEBUG: main.py - Script finished defining function.")

