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
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookies, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookies, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookies (CaseInsensitiveDict): response cookies.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
        "reason",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of Cookies the response headers.
        self.cookies = CaseInsensitiveDict()

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        print("[Response] BUILDING: Detecting MIME type for path: {}".format(path))
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            print("[Response] BUILDING: Exception in MIME detection, defaulting to HTML")
            return 'text/html'
        
        # If no extension or unknown MIME type, assume it's HTML (for routes like /login, /user, etc.)
        if mime_type is None:
            print("[Response] BUILDING: No MIME type detected, assuming HTML content")
            return 'text/html'
        
        print("[Response] BUILDING: Detected MIME type: {}".format(mime_type))
        return mime_type

    def validate_authentication(self, auth_header):
        """
        Validates authentication credentials from the Authorization header.
        
        :param auth_header (str): Authorization header value
        :rtype bool: True if authentication is valid, False otherwise
        """
        print("[Response] BUILDING: Validating authentication: {}".format(auth_header[:20] + "..." if len(auth_header) > 20 else auth_header))
        
        if not auth_header:
            print("[Response] BUILDING: No authentication header provided")
            return False
        
        if auth_header.startswith("Basic "):
            # Basic authentication validation
            try:
                import base64
                encoded_credentials = auth_header[6:]  # Remove "Basic "
                decoded_credentials = base64.b64decode(encoded_credentials).decode()
                username, password = decoded_credentials.split(":", 1)
                
                # Simple credential validation (you can customize this)
                valid_users = {
                    "admin": "password123",
                    "user": "userpass",
                    "test": "test123"
                }
                
                if username in valid_users and valid_users[username] == password:
                    print("[Response] BUILDING: Valid Basic authentication for user: {}".format(username))
                    return True
                else:
                    print("[Response] BUILDING: Invalid credentials for user: {}".format(username))
                    return False
            except Exception as e:
                print("[Response] BUILDING: Error validating Basic auth: {}".format(e))
                return False
        
        elif auth_header.startswith("Bearer "):
            # Bearer token validation
            token = auth_header[7:]  # Remove "Bearer "
            valid_tokens = ["abc123", "xyz789", "token456"]  # You can customize this
            
            if token in valid_tokens:
                print("[Response] BUILDING: Valid Bearer token")
                return True
            else:
                print("[Response] BUILDING: Invalid Bearer token")
                return False
        
        print("[Response] BUILDING: Unsupported authentication method")
        return False

    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """
        
        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                # IMPLEMENTED: Handle other text types - default to static directory
                print("[Response] BUILDING: Using static directory for text/{} type".format(sub_type))
                base_dir = BASE_DIR+"static/"
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            base_dir = BASE_DIR+"apps/"
            self.headers['Content-Type']='application/{}'.format(sub_type)
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] serving the object at location {}".format(filepath))
            #
            #  TODO: implement the step of fetch the object file
            #        store in the return value of content
            #
        
        # IMPLEMENTED: File content reading with error handling
        try:
            print("[Response] BUILDING: Reading file content from {}".format(filepath))
            with open(filepath, 'rb') as f:
                content = f.read()
            print("[Response] BUILDING: Successfully read {} bytes".format(len(content)))
            return len(content), content
        except FileNotFoundError:
            print("[Response] BUILDING: File not found, returning error content")
            content = b"File not found"
            return len(content), content
        except Exception as e:
            print("[Response] BUILDING: Error reading file - {}".format(e))
            content = b"Error reading file"
            return len(content), content


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        # Check authentication status
        print("[Response] BUILDING: Processing authentication headers")
        auth_header = reqhdr.get("authorization", "")
        is_authenticated = self.validate_authentication(auth_header)
        
        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
        #
        # TODO prepare the request authentication
        #
        # IMPLEMENTED: Enhanced authentication handling
        }
        
        # Add authentication headers if needed
        if auth_header:
            headers["Authorization"] = auth_header
            print("[Response] BUILDING: Added Authorization header")
        
        # Add authentication challenge if not authenticated
        if not is_authenticated and request.path in ['/login', '/admin', '/secure']:
            headers["WWW-Authenticate"] = 'Basic realm="Secure Area"'
            print("[Response] BUILDING: Added authentication challenge")
        
        # Add cookies if present
        if hasattr(request, 'cookies') and request.cookies:
            cookie_string = "; ".join([f"{k}={v}" for k, v in request.cookies.items()])
            headers["Set-Cookie"] = cookie_string
            print("[Response] BUILDING: Added cookies to response")
        
        # Add additional headers
        headers.update({
            "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
            "Max-Forward": "10", 
            "Pragma": "no-cache",
            "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
            "Warning": "199 Miscellaneous warning",
            "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
        })

        # Header text alignment
            #
            #  TODO: implement the header building to create formated
            #        header from the provied headers
            #
        
        # IMPLEMENTED: HTTP header formatting
        print("[Response] BUILDING: Formatting HTTP response headers")
        fmt_header = "HTTP/1.1 {} {}\r\n".format(self.status_code, self.reason)
        print("[Response] BUILDING: Status line - HTTP/1.1 {} {}".format(self.status_code, self.reason))
        
        for key, value in headers.items():
            fmt_header += "{}: {}\r\n".format(key, value)
            print("[Response] BUILDING: Header - {}: {}".format(key, value))
        
        fmt_header += "\r\n"  # Empty line to separate headers from body
        print("[Response] BUILDING: Complete header formatted ({} bytes)".format(len(fmt_header)))
        
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')


    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """

        path = request.path

        mime_type = self.get_mime_type(path)
        print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        # IMPLEMENTED: Initialize response status
        print("[Response] BUILDING: Setting default response status 200 OK")
        self.status_code = 200
        self.reason = "OK"
        
        base_dir = ""

        #If HTML, parse and serve embedded objects
        print("[Response] BUILDING: Determining content type and base directory")
        if path.endswith('.html') or mime_type == 'text/html':
            print("[Response] BUILDING: Processing HTML content")
            # Handle paths without .html extension by adding it
            if not path.endswith('.html') and not path.endswith('/'):
                path = path + '.html'
                print("[Response] BUILDING: Adjusted path to: {}".format(path))
            base_dir = self.prepare_content_type(mime_type = 'text/html')
        elif mime_type == 'text/css':
            print("[Response] BUILDING: Processing CSS content")
            base_dir = self.prepare_content_type(mime_type = 'text/css')
        elif mime_type.startswith('image/'):
            print("[Response] BUILDING: Processing image content")
            base_dir = self.prepare_content_type(mime_type = mime_type)
        #
        # TODO: add support for other objects
        #
        else:
            print("[Response] BUILDING: Unsupported MIME type, returning 404")
            return self.build_notfound()

        print("[Response] BUILDING: Loading content from base directory: {}".format(base_dir))
        c_len, self._content = self.build_content(path, base_dir)
        
        # IMPLEMENTED: File not found handling
        if c_len == 0 or self._content == b"File not found":
            print("[Response] BUILDING: File not accessible, returning 404")
            return self.build_notfound()
            
        print("[Response] BUILDING: Building response headers")
        self._header = self.build_response_header(request)

        print("[Response] BUILDING: Combining headers ({} bytes) and content ({} bytes)".format(len(self._header), len(self._content)))
        return self._header + self._content