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
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            # Don't automatically convert / to /index.html for login handling
            # if path == '/':
            #     path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version

    def extract_body(self, request):
        """Extract the request body from HTTP request."""
        try:
            # Split headers and body by double CRLF
            if '\r\n\r\n' in request:
                header_part, body_part = request.split('\r\n\r\n', 1)
                return body_part.strip()
            elif '\n\n' in request:
                header_part, body_part = request.split('\n\n', 1)
                return body_part.strip()
            else:
                return ""
        except Exception as e:
            print("[Request] Error extracting body: {}".format(e))
            return ""

    def parse_form_data(self, body):
        """Parse application/x-www-form-urlencoded data."""
        if not body:
            return {}
        
        form_data = {}
        pairs = body.split('&')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                # URL decode the values
                import urllib.parse
                key = urllib.parse.unquote_plus(key)
                value = urllib.parse.unquote_plus(value)
                form_data[key] = value
        return form_data
             
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
        print("[Request] BUILDING: Extracting request line from HTTP request")
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        print("[Request] BUILDING: Processing routes and webapp hooks")
        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            print("[Request] BUILDING: Route hook found: {}".format(self.hook))
            #
            # self.hook manipulation goes here
            # ...
            #
        else:
            print("[Request] BUILDING: No routes configured, using default behavior")

        print("[Request] BUILDING: Parsing HTTP headers")
        self.headers = self.prepare_headers(request)
        print("[Request] BUILDING: Found {} headers".format(len(self.headers)))
        
        cookies = self.headers.get('cookie', '')
        print("[Request] BUILDING: Processing cookies: {}".format(cookies if cookies else "None"))
        #
        # TODO: implement the cookie function here
        #       by parsing the header
        #
        # IMPLEMENTED: Parse cookies from header
        if cookies:
            self.cookies = {}
            cookie_pairs = cookies.split(';')
            for pair in cookie_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    self.cookies[key.strip()] = value.strip()
            print("[Request] BUILDING: Parsed {} cookies".format(len(self.cookies)))
        else:
            self.cookies = {}
            print("[Request] BUILDING: No cookies found")

        # Parse request body for POST requests
        print("[Request] BUILDING: Parsing request body")
        self.body = self.extract_body(request)
        if self.body:
            print("[Request] BUILDING: Found body with {} chars".format(len(self.body)))
        else:
            print("[Request] BUILDING: No body found")

        return

    def prepare_body(self, data, files, json=None):
        # IMPLEMENTED: Initialize body before setting content length
        print("[Request] BUILDING: Preparing request body")
        if data:
            self.body = data
        elif json:
            import json as json_module
            self.body = json_module.dumps(json)
        else:
            self.body = ""
        
        self.prepare_content_length(self.body)
        # Note: body is already set above, no need to reassign
        print("[Request] BUILDING: Body prepared with length: {}".format(len(str(self.body))))
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_content_length(self, body):
        # IMPLEMENTED: Calculate actual content length
        print("[Request] BUILDING: Calculating content length")
        if body:
            content_length = len(str(body))
        else:
            content_length = 0
        
        self.headers["Content-Length"] = str(content_length)
        print("[Request] BUILDING: Set Content-Length to {}".format(content_length))
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
        # IMPLEMENTED: Basic authentication support
        print("[Request] BUILDING: Preparing authentication")
        
        if auth:
            if isinstance(auth, tuple) and len(auth) == 2:
                # Basic authentication with username/password
                import base64
                username, password = auth
                credentials = f"{username}:{password}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                self.auth = f"Basic {encoded_credentials}"
                self.headers["Authorization"] = self.auth
                print("[Request] BUILDING: Set Basic authentication for user: {}".format(username))
            elif isinstance(auth, str):
                # Bearer token or custom auth string
                self.auth = auth
                if auth.startswith("Bearer ") or auth.startswith("Basic "):
                    self.headers["Authorization"] = auth
                else:
                    self.headers["Authorization"] = f"Bearer {auth}"
                print("[Request] BUILDING: Set token authentication")
            else:
                print("[Request] BUILDING: Invalid authentication format")
                self.auth = None
        else:
            self.auth = None
            print("[Request] BUILDING: No authentication provided")
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
