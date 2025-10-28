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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict
from .api_handlers import APIHandlers
import json

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        msg = conn.recv(1024).decode()
        req.prepare(msg, routes)

        # Handle API routes
        if self.handle_api_routes(req, resp, conn):
            return  # API handler sent response, exit early

        # Handle authentication-specific routes
        if self.handle_authentication_routes(req, resp, conn):
            return  # Authentication handler sent response, exit early

        # Check authentication for protected routes (GET /)
        if req.method == 'GET' and req.path in ['/', '/index.html']:
            if not self.check_authentication_cookie(req):
                print("[HttpAdapter] BUILDING: Access denied - no valid auth cookie")
                self.send_unauthorized_response(conn)
                return

        # Handle request hook
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
            req.hook(headers = "bksysnet",body = "get in touch")
            #
            # TODO: handle for App hook here
            #

        # Build response
        response = resp.build_response(req)

        #print(response)
        conn.sendall(response)
        conn.close()

    def handle_authentication_routes(self, req, resp, conn):
        """Handle authentication-specific routes like /login."""
        if req.method == 'POST' and req.path == '/login':
            print("[HttpAdapter] BUILDING: Processing login request")
            
            # Parse form data from body
            form_data = req.parse_form_data(req.body)
            username = form_data.get('username', '')
            password = form_data.get('password', '')
            
            print("[HttpAdapter] BUILDING: Login attempt - username: {}".format(username))
            
            # Validate credentials
            if username == 'admin' and password == 'password':
                print("[HttpAdapter] BUILDING: Valid credentials - sending success response")
                self.send_login_success_response(conn)
            else:
                print("[HttpAdapter] BUILDING: Invalid credentials - sending unauthorized response")
                self.send_unauthorized_response(conn)
            
            return True  # Handled the request
        
        return False  # Didn't handle this request

    def check_authentication_cookie(self, req):
        """Check if the request has valid authentication cookie."""
        if hasattr(req, 'cookies') and req.cookies:
            auth_cookie = req.cookies.get('auth', '')
            return auth_cookie == 'true'
        return False

    def send_login_success_response(self, conn):
        """Send successful login response with Set-Cookie header."""
        try:
            # Read the index.html file
            with open('www/index.html', 'r') as f:
                content = f.read()
            
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n" 
                "Content-Length: {}\r\n"
                "Set-Cookie: auth=true; Path=/\r\n"
                "Connection: close\r\n"
                "\r\n"
                "{}"
            ).format(len(content), content)
            
            conn.sendall(response.encode())
            print("[HttpAdapter] BUILDING: Sent login success response with auth cookie")
        except FileNotFoundError:
            # Fallback if index.html not found
            content = "<html><body><h1>Login Successful</h1><p>Welcome, admin!</p></body></html>"
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: {}\r\n" 
                "Set-Cookie: auth=true; Path=/\r\n"
                "Connection: close\r\n"
                "\r\n"
                "{}"
            ).format(len(content), content)
            conn.sendall(response.encode())
        finally:
            conn.close()

    def send_unauthorized_response(self, conn):
        """Send 401 Unauthorized response."""
        content = (
            "<html><body>"
            "<h1>401 Unauthorized</h1>"
            "<p>Access denied. Please login first.</p>"
            "<form method='POST' action='/login'>"
            "<p>Username: <input name='username' type='text' value='admin'></p>"
            "<p>Password: <input name='password' type='password' value='password'></p>"
            "<p><input type='submit' value='Login'></p>"
            "</form>"
            "</body></html>"
        )
        
        response = (
            "HTTP/1.1 401 Unauthorized\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: {}\r\n" 
            "Connection: close\r\n"
            "\r\n"
            "{}"
        ).format(len(content), content)
        
        conn.sendall(response.encode())
        conn.close()
        print("[HttpAdapter] BUILDING: Sent 401 Unauthorized response")

    def handle_api_routes(self, req, resp, conn):
        """Handle API endpoints."""
        api_paths = ['/login/', '/submit-info/', '/add-list/', '/get-list/', 
                    '/connect-peer/', '/broadcast-peer/', '/send-peer/']
        
        if any(req.path.startswith(api_path) for api_path in api_paths):
            print("[HttpAdapter] BUILDING: Processing API request to {}".format(req.path))
            
            # Call API handler
            status_code, response_headers, response_data = APIHandlers.handle_api_request(
                req.method, req.path, req.headers, req.body, req.cookies
            )
            
            # Send JSON response
            json_response = json.dumps(response_data, indent=2)
            
            # Build headers
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(json_response)),
                "Connection": "close"
            }
            headers.update(response_headers)  # Add any additional headers
            
            # Build HTTP response
            status_text = {
                200: "OK",
                400: "Bad Request", 
                401: "Unauthorized",
                404: "Not Found",
                405: "Method Not Allowed"
            }.get(status_code, "Internal Server Error")
            
            response = "HTTP/1.1 {} {}\r\n".format(status_code, status_text)
            for key, value in headers.items():
                response += "{}: {}\r\n".format(key, value)
            response += "\r\n"
            response += json_response
            
            conn.sendall(response.encode())
            conn.close()
            print("[HttpAdapter] BUILDING: Sent API response with status {}".format(status_code))
            return True
        
        return False

    def extract_cookies(self, req, resp):
        """
        Build cookies from the :class:`Request <Request>` headers.

        :param req:(Request) The :class:`Request <Request>` object.
        :param resp: (Response) The res:class:`Response <Response>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        cookies = {}
        if hasattr(req, 'headers') and req.headers:
            cookie_header = req.headers.get('cookie', '')
            if cookie_header:
                for pair in cookie_header.split(";"):
                    if '=' in pair:
                        key, value = pair.strip().split("=", 1)
                        cookies[key] = value
        return cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set basic properties
        response.encoding = 'utf-8'  # Default encoding
        response.raw = resp
        if hasattr(resp, 'reason'):
            response.reason = resp.reason

        if hasattr(req, 'url') and req.url:
            if isinstance(req.url, bytes):
                response.url = req.url.decode("utf-8")
            else:
                response.url = req.url

        # Add new cookies from the server.
        response.cookies = self.extract_cookies(req, resp)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers