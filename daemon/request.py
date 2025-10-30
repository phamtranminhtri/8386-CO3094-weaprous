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
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            # if path == '/':
            #     path = '/index.html'
        except Exception:
            return None, None

        return method, path, version
             
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
        # Initialize query container
        self.query = {}
        # If there's a query string, split it off and parse into a dict
        if "?" in self.path:
            path_part, query_string = self.path.split("?", 1)
            # keep a sensible default path
            self.path = path_part or "/"
            # parse_qsl returns list of (key, value) pairs; build dict (last value wins)
            self.query = dict(urllib.parse.parse_qsl(query_string, keep_blank_values=True, encoding='utf-8', errors='replace'))

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
        self.body = self.prepare_body(raw_body)

        cookies = self.headers.get('cookie', '')
        
        if cookies:
            self.prepare_cookies(cookies)

        # Update query into self.headers
        self.headers["query"] = self.query

        return

    def prepare_body(self, data, files=None, json=None):
        body = None
        if not data:
            return body

        content_type = self.headers.get('content-type', '')
        if content_type == "application/x-www-form-urlencoded":
            try:
                list_of_tuples = urllib.parse.parse_qsl(
                    data, 
                    keep_blank_values=True, 
                    encoding='utf-8', 
                    errors='replace'
                )
                body = dict(list_of_tuples)
            except Exception as e:
                print(f"[Request] Lỗi parse body: {e}")
                body = None
        
        # if json is not None:
        #     import json as json_module
        #     body = json_module.dumps(json).encode('utf-8')
        #     self.headers['Content-Type'] = 'application/json'
        # elif data:
        #     if isinstance(data, dict):
        #         body = '&'.join([f"{k}={v}" for k, v in data.items()]).encode('utf-8')
        #         self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        #     elif isinstance(data, str):
        #         body = data.encode('utf-8')
        #     else:
        #         body = data
        # elif files:
        #     # Simple file handling - in production would use multipart/form-data
        #     body = b''
            
        # self.body = body
        self.prepare_content_length(data)
        
        return body


    def prepare_content_length(self, body):
        """Prepares the Content-Length header based on body size."""
        if body is not None:
            self.headers["Content-Length"] = str(len(body))
        else:
            self.headers["Content-Length"] = "0"
        
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
