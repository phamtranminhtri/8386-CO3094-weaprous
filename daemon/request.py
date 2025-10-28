#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
import urllib.parse
import re

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        """
        Extract HTTP method, path, and version from request line.
        
        Args:
            request: Raw HTTP request string
            
        Returns:
            tuple: (method, path, version) or (None, None, None) on error
        """
        try:
            lines = request.splitlines()
            if not lines:
                print("[Request] Error: Empty request")
                return None, None, None
                
            first_line = lines[0]
            parts = first_line.split()
            
            if len(parts) != 3:
                print(f"[Request] Error: Invalid request line format: {first_line}")
                return None, None, None
                
            method, path, version = parts
            
            # Basic validation
            if not method or not path or not version:
                print(f"[Request] Error: Missing components in request line: {first_line}")
                return None, None, None
                
            return method, path, version
            
        except Exception as e:
            print(f"[Request] Error parsing request line: {e}")
            return None, None, None
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        
        # Handle malformed requests
        if self.method is None or self.path is None or self.version is None:
            print("[Request] Error: Failed to parse request line")
            return None
            
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if not routes == {}:  
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            #
            # self.hook manipulation goes here
            # ...
            #
        raw_header, raw_body = self.parse_http_request(request)
    
        print(f"[Request] DEBUG: Parsed header length: {len(raw_header)}")
        print(f"[Request] DEBUG: Parsed body: {repr(raw_body)}")

        self.headers = self.prepare_headers(raw_header)
        print(f"[Request] DEBUG: Parsed headers: {self.headers}")
        
        # Validate Content-Length before processing body
        self.prepare_content_length(raw_body)
        
        # Process body based on content type
        self.body = self.prepare_body(raw_body)
        print(f"[Request] DEBUG: Final body type: {type(self.body)}")
        print(f"[Request] DEBUG: Final body content: {repr(self.body)}")

        cookies = self.headers.get('cookie', '')
        
        if cookies:
            self.prepare_cookies(cookies)

        return
    
    def parse_http_request(self, request):
        """
        Parse HTTP request using regex for robust header/body separation.
        
        Args:
            request: Raw HTTP request string
            
        Returns:
            tuple: (header_section, body_section)
        """
        print(f"[Request] DEBUG: Parsing HTTP request ({len(request)} chars)")
        print(f"[Request] DEBUG: Request preview: {repr(request[:200])}...")
        
        # Debug: Check what separators actually exist in the request
        has_crlf_crlf = '\r\n\r\n' in request
        has_lf_lf = '\n\n' in request
        has_cr_cr = '\r\r' in request
        
        print(f"[Request] DEBUG: Separator analysis:")
        print(f"[Request] DEBUG:   \\r\\n\\r\\n exists: {has_crlf_crlf}")
        print(f"[Request] DEBUG:   \\n\\n exists: {has_lf_lf}")
        print(f"[Request] DEBUG:   \\r\\r exists: {has_cr_cr}")
        
        # More comprehensive pattern that handles mixed line endings
        separator_patterns = [
            r'\r\n\r\n',    # Standard HTTP
            r'\n\r\n\r',    # Mixed endings
            r'\r\n\r\n',    # Windows style
            r'\n\n',        # Unix style
            r'\r\r',        # Old Mac style
        ]
        
        raw_header = request
        raw_body = ""
        separator_used = None
        
        # Try each pattern until one matches
        for pattern in separator_patterns:
            match = re.search(pattern, request)
            if match:
                separator_pos = match.start()
                separator_end = match.end()
                
                raw_header = request[:separator_pos]
                raw_body = request[separator_end:]
                separator_used = pattern
                
                print(f"[Request] DEBUG: Found separator '{repr(match.group())}' using pattern '{pattern}'")
                print(f"[Request] DEBUG: Separator at position {separator_pos}-{separator_end}")
                break
        
        if not separator_used:
            print("[Request] DEBUG: No separator found with regex, trying manual search...")
            
            # Manual fallback - search for common patterns
            for sep in ['\r\n\r\n', '\n\n', '\r\r']:
                if sep in request:
                    parts = request.split(sep, 1)
                    if len(parts) == 2:
                        raw_header = parts[0]
                        raw_body = parts[1]
                        separator_used = f"manual:{sep}"
                        print(f"[Request] DEBUG: Manual split successful with '{repr(sep)}'")
                        break
        
        print(f"[Request] DEBUG: Final result:")
        print(f"[Request] DEBUG:   Header section: {len(raw_header)} chars")
        print(f"[Request] DEBUG:   Body section: {len(raw_body)} chars")
        print(f"[Request] DEBUG:   Separator used: {separator_used}")
        print(f"[Request] DEBUG:   Body preview: {repr(raw_body[:50])}")
        
        return raw_header, raw_body

    def prepare_body(self, data, files=None, json=None):
        """
        Prepares the request body based on content type.
        
        Args:
            data: Raw body data from HTTP request
            files: File data (future use)
            json: JSON data (future use)
            
        Returns:
            Processed body data appropriate for the content type
        """
        print(f"[Request] DEBUG prepare_body called with data: {repr(data)}")
        print(f"[Request] DEBUG data type: {type(data)}")
        print(f"[Request] DEBUG data length: {len(data) if data else 'None'}")
        
        if not data:
            print("[Request] DEBUG: No data provided, returning None")
            return None

        content_type = self.headers.get('content-type', '').lower()
        print(f"[Request] DEBUG Content-Type: {repr(content_type)}")
        print(f"[Request] DEBUG Available headers: {list(self.headers.keys())}")
        
        # Handle different content types
        if content_type == "application/x-www-form-urlencoded":
            # Parse URL-encoded form data into dictionary
            print("[Request] DEBUG: Processing application/x-www-form-urlencoded")
            try:
                list_of_tuples = urllib.parse.parse_qsl(data)
                result_dict = dict(list_of_tuples)
                print(f"[Request] DEBUG: Parsed tuples: {list_of_tuples}")
                print(f"[Request] DEBUG: Result dict: {result_dict}")
                return result_dict
            except Exception as e:
                print(f"[Request] Error parsing form data: {e}")
                print(f"[Request] DEBUG: Returning raw data due to parse error")
                return data
                
        elif content_type.startswith("application/json"):
            # Parse JSON data
            try:
                import json as json_module
                return json_module.loads(data)
            except Exception as e:
                print(f"[Request] Error parsing JSON: {e}")
                return data
                
        elif content_type.startswith("multipart/form-data"):
            # For now, return raw data - could be enhanced for file uploads
            print("[Request] Multipart form data detected, returning raw data")
            return data
            
        elif content_type.startswith("text/"):
            # Handle text data (plain, html, etc.)
            return data
            
        else:
            # For any other content type, return raw data
            print(f"[Request] DEBUG: Unknown content type '{content_type}', returning raw data")
            print(f"[Request] DEBUG: Raw data being returned: {repr(data)}")
            return data


    def prepare_content_length(self, body):
        """
        Validates Content-Length header against actual body size.
        Does NOT override client's Content-Length header.
        
        Args:
            body: The raw body data to validate against
        """
        if body is not None:
            actual_length = len(body)
            client_length = self.headers.get("content-length")
            
            if client_length:
                try:
                    client_length = int(client_length)
                    if client_length != actual_length:
                        print(f"[Request] Warning: Content-Length mismatch. "
                              f"Client sent {client_length}, actual is {actual_length}")
                except ValueError:
                    print(f"[Request] Warning: Invalid Content-Length header: {client_length}")
            else:
                # Only set Content-Length if client didn't provide it
                print(f"[Request] No Content-Length provided by client, setting to {actual_length}")
                self.headers["content-length"] = str(actual_length)
        else:
            # Only set to 0 if no Content-Length header exists
            if "content-length" not in self.headers:
                self.headers["content-length"] = "0"
        
        return


    def prepare_auth(self, auth, url=""):
        """Prepares the request authentication.
        
        :param auth: Tuple of (username, password) for basic auth or auth object
        :param url: The URL being requested
        """
        # if auth:
        #     if isinstance(auth, tuple) and len(auth) == 2:
        #         # Basic authentication
        #         import base64
        #         username, password = auth
        #         credentials = f"{username}:{password}"
        #         encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        #         self.headers["Authorization"] = f"Basic {encoded}"
        #     else:
        #         # Other auth types could be implemented here
        #         pass
        
        return

    def prepare_cookies(self, cookies):
        if cookies:
            self.cookies = {}
            for pair in cookies.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    self.cookies[key.strip()] = value.strip()
            self.headers["cookie-pair"] = self.cookies
