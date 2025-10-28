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

        parts = request.split("\r\n\r\n", 1)
        raw_header = parts[0]
        raw_body = None
        if len(parts) > 1:
            raw_body = parts[1]

        self.headers = self.prepare_headers(raw_header)
        
        # Validate Content-Length before processing body
        self.prepare_content_length(raw_body)
        
        # Process body based on content type
        self.body = self.prepare_body(raw_body)

        cookies = self.headers.get('cookie', '')
        
        if cookies:
            self.prepare_cookies(cookies)

        return

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
        if not data:
            return None

        content_type = self.headers.get('content-type', '').lower()
        
        # Handle different content types
        if content_type == "application/x-www-form-urlencoded":
            # Parse URL-encoded form data into dictionary
            try:
                list_of_tuples = urllib.parse.parse_qsl(data)
                return dict(list_of_tuples)
            except Exception as e:
                print(f"[Request] Error parsing form data: {e}")
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
            print(f"[Request] Unknown content type '{content_type}', returning raw data")
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
