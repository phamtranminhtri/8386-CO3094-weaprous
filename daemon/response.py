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
        self.status_code = 200  # Default to 200 OK

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

    def set_status_code(self, code):
        """Set the HTTP status code for the response."""
        self.status_code = code
    
    def is_success(self):
        """Check if response is successful (2xx status codes)."""
        return 200 <= self.status_code < 300
    
    def is_error(self):
        """Check if response has error status (4xx or 5xx)."""
        return self.status_code >= 400

    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


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
                # handle_text_other(sub_type)
                base_dir = BASE_DIR+"static/"
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type == 'xml' or sub_type == 'zip' or sub_type == 'json':
                base_dir = BASE_DIR+"static/"
            else:
                base_dir = BASE_DIR+"apps/"
            self.headers['Content-Type']='application/{}'.format(sub_type)
        elif main_type == 'video':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='video/{}'.format(sub_type)
        elif main_type == 'audio':
            base_dir = BASE_DIR+"static/"
            self.headers['Content-Type']='audio/{}'.format(sub_type)
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
        
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
                return len(content), content
        except FileNotFoundError:
            self.set_status_code(404)
            content = b"404 Not Found"
            return len(content), content
        except Exception as e:
            print(f"[Response] Error reading file: {e}")
            self.set_status_code(500)
            content = b"500 Internal Server Error"
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

        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(self.headers['Content-Type']),
                "Content-Length": "{}".format(len(self._content)),
#                "Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
            }
        
        if request.method == "POST" and request.path == "/login":
            headers["Set-Cookie"] = "auth=true"

        # Get status message based on status code
        status_messages = {
            200: "OK",
            201: "Created", 
            302: "Found",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error"
        }
        
        status_message = status_messages.get(self.status_code, "OK")
        
        # Header text alignment with dynamic status code
        fmt_header = f"HTTP/1.1 {self.status_code} {status_message}\r\n"
        for key, value in headers.items():
            fmt_header += f"{key}: {value}\r\n"
        fmt_header += "\r\n"
        
        return str(fmt_header).encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """
        
        self.set_status_code(404)
        content = "404 Not Found"
        content_length = len(content.encode('utf-8'))
        
        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {content_length}\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{content}"
            ).encode('utf-8')


    def build_unauthorized(self):
        """
        Constructs a standard 401 Unauthorized HTTP response.

        :rtype bytes: Encoded 401 response.
        """
        
        self.set_status_code(401)
        content = "401 Unauthorized<br><a href='/login'>Login</a> or <a href='/register'>Register</a>\r\n"
        content_length = len(content.encode('utf-8'))
        
        return (
                "HTTP/1.1 401 Unauthorized\r\n"
                # "WWW-Authenticate: Basic realm=\"Access to the site\"\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {content_length}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{content}"
            ).encode('utf-8')


    def build_redirect(self, path, request, new_session_id=None):
        """
        Constructs a standard 302 Found (redirect) HTTP response.

        :params path (str): The path to redirect to (e.g., "/", "/login").

        :rtype bytes: Encoded 302 redirect response.
        """
        
        self.set_status_code(302)
        redirect_message = f"Redirecting to {path}"
        content_length = len(redirect_message)

        if request.method == "POST" and request.path in ["/login", "/register"]:
            return (
                "HTTP/1.1 302 Found\r\n"
                f"Location: {path}\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {content_length}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                f"Set-Cookie: auth=true; Path=/\r\n"
                f"Set-Cookie: session_id={new_session_id}; Path=/\r\n"
                "\r\n"
                f"{redirect_message}"
            ).encode('utf-8')

        if request.method == "POST" and request.path == "/logout":
            return (
                "HTTP/1.1 302 Found\r\n"
                f"Location: {path}\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {content_length}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                f"Set-Cookie: auth=false; Path=/\r\n"
                "\r\n"
                f"{redirect_message}"
            ).encode('utf-8')
        

        return (
                "HTTP/1.1 302 Found\r\n"
                f"Location: {path}\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {content_length}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{redirect_message}"
            ).encode('utf-8')


    def build_content_placeholder(self, req, html_content, placeholders):
        try:
            html_path = os.path.join("www", html_content)
            with open(html_path) as f:
                raw_html = f.read()
            for i, placeholder in enumerate(placeholders):
                raw_html = raw_html.replace(f"{{{{ placeholder_{i} }}}}", placeholder)

            # Convert HTML to bytes
            content = raw_html.encode('utf-8')
            content_length = len(content)
            
            # Set successful status code
            self.set_status_code(200)

            # Build response header
            response_header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {content_length}\r\n"
                f"Date: {datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
                "Cache-Control: no-cache\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8')

            return response_header + content
            
        except FileNotFoundError:
            self.set_status_code(404)
            return self.build_notfound()
        except Exception as e:
            print(f"[Response] Error in build_content_placeholder: {e}")
            self.set_status_code(500)
            content = "500 Internal Server Error"
            return (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(content)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{content}"
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

        base_dir = ""

        #If HTML, parse and serve embedded objects
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type = 'text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type = 'text/css')
        elif mime_type.startswith('image/'):
            base_dir = self.prepare_content_type(mime_type = mime_type)
        elif mime_type.startswith('video/'):
            base_dir = self.prepare_content_type(mime_type = mime_type)
        elif mime_type.startswith('audio/'):
            base_dir = self.prepare_content_type(mime_type = mime_type)
        elif mime_type in ['application/json', 'application/xml', 'application/zip']:
            base_dir = self.prepare_content_type(mime_type = mime_type)
        elif mime_type in ['text/plain', 'text/csv', 'text/xml']:
            base_dir = self.prepare_content_type(mime_type = mime_type)
        else:
            self.set_status_code(404)
            return self.build_notfound()

        c_len, self._content = self.build_content(path, base_dir)
        
        # If file not found during content loading, return 404
        if self.status_code == 404:
            return self.build_notfound()
            
        self._header = self.build_response_header(request)

        return self._header + self._content