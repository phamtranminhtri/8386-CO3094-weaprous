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
import urllib
import socket
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
        self.connaddr = addr
        req = self.request
        resp = self.response

        # ========================================
        # BƯỚC 1: ĐỌC HEADER VỚI TIMEOUT
        # ========================================
        try:
            # ✅ SỬA: Tăng timeout lên 30s cho Safari
            conn.settimeout(30.0)
            
            raw_request = b''
            max_header_size = 8192
            
            while b'\r\n\r\n' not in raw_request:
                chunk = conn.recv(1024)
                
                if not chunk:
                    print(f"[HttpAdapter] Client {addr} closed connection early")
                    conn.close()
                    return
                
                raw_request += chunk
                
                if len(raw_request) > max_header_size:
                    print(f"[HttpAdapter] Header too large from {addr}")
                    conn.close()
                    return
            
        except socket.timeout:
            print(f"[HttpAdapter] Timeout reading header from {addr}")
            conn.close()
            return
        except Exception as e:
            print(f"[HttpAdapter] Error reading request: {e}")
            conn.close()
            return

        # ========================================
        # BƯỚC 2: TÁCH HEADER VÀ BODY
        # ========================================
        try:
            header_bytes, body_bytes = raw_request.split(b'\r\n\r\n', 1)
            header_str = header_bytes.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[HttpAdapter] Error parsing request: {e}")
            conn.close()
            return

        # ========================================
        # BƯỚC 3: PHÂN TÍCH REQUEST LINE
        # ========================================
        req.method, req.path, req.version = req.extract_request_line(header_str)
        if not req.method:
            print("[HttpAdapter] Invalid request line")
            conn.close()
            return

        # ========================================
        # BƯỚC 4: PHÂN TÍCH HEADERS
        # ========================================
        req.headers = req.prepare_headers(header_str)
        if 'expect' in req.headers and req.headers['expect'].lower() == '100-continue':
            print(f"[HttpAdapter] Sending 100 Continue to {addr}")
            try:
                conn.sendall(b'HTTP/1.1 100 Continue\r\n\r\n')
            except Exception as e:
                print(f"[HttpAdapter] Error sending 100 Continue: {e}")
                conn.close()
                return
        # ========================================
        # BƯỚC 5: ĐỌC BODY (nếu có Content-Length)
        # ========================================
        raw_body_str = None
        if 'content-length' in req.headers:
            try:
                content_length = int(req.headers['content-length'])
                
                max_body_size = 1024 * 1024  # 1MB
                if content_length > max_body_size:
                    print(f"[HttpAdapter] Body too large: {content_length} bytes")
                    conn.close()
                    return
                
                bytes_needed = content_length - len(body_bytes)
                
                # ✅ SỬA: Tăng timeout cho việc đọc body
                conn.settimeout(30.0)
                
                # Đọc thêm nếu chưa đủ
                retry_count = 0
                max_retries = 3
                
                while bytes_needed > 0 and retry_count < max_retries:
                    try:
                        chunk = conn.recv(min(bytes_needed, 4096))
                        if not chunk:
                            print(f"[HttpAdapter] Connection closed while reading body")
                            retry_count += 1
                            continue
                        body_bytes += chunk
                        bytes_needed -= len(chunk)
                        retry_count = 0  # Reset counter on success
                    except socket.timeout:
                        print(f"[HttpAdapter] Timeout reading body chunk, retry {retry_count + 1}/{max_retries}")
                        retry_count += 1
                        if retry_count >= max_retries:
                            print(f"[HttpAdapter] Max retries reached for {addr}")
                            conn.close()
                            return
                
                raw_body_str = body_bytes.decode('utf-8', errors='replace')
                
            except (ValueError, UnicodeDecodeError) as e:
                print(f"[HttpAdapter] Error reading body: {e}")
                raw_body_str = None
        elif body_bytes:
            raw_body_str = body_bytes.decode('utf-8', errors='replace')

        # ========================================
        # BƯỚC 6: PARSE QUERY STRING
        # ========================================
        req.query = {}
        if "?" in req.path:
            try:
                path_part, query_string = req.path.split("?", 1)
                req.path = path_part or "/"
                req.query = dict(urllib.parse.parse_qsl(
                    query_string, 
                    keep_blank_values=True, 
                    encoding='utf-8', 
                    errors='replace'
                ))
            except Exception as e:
                print(f"[HttpAdapter] Error parsing query: {e}")
                req.query = {}

        # ========================================
        # BƯỚC 7: GẮN ROUTES VÀ HOOK
        # ========================================
        if routes:
            req.routes = routes
            req.hook = routes.get((req.method, req.path))

        # ========================================
        # BƯỚC 8: PARSE BODY
        # ========================================
        req.body = req.prepare_body(raw_body_str)

        # ========================================
        # BƯỚC 9: PARSE COOKIES
        # ========================================
        cookies = req.headers.get('cookie', '')
        if cookies:
            req.prepare_cookies(cookies)

        # ========================================
        # BƯỚC 10: CẬP NHẬT QUERY VÀO HEADERS
        # ========================================
        req.headers["query"] = req.query

        # ========================================
        # BƯỚC 11: XỬ LÝ HOOK
        # ========================================
        if req.hook:
            print(f"[HttpAdapter] hook in route-path METHOD {req.hook._route_methods} PATH {req.hook._route_path}")
            
            try:
                hook_result = req.hook(headers=req.headers, body=req.body)
                print(f"[HttpAdapter] Hook result: {hook_result}")  # ✅ THÊM LOG ĐỂ DEBUG
            except Exception as e:
                print(f"[HttpAdapter] Error in hook: {e}")
                response = resp.build_notfound()
                conn.sendall(response)
                conn.close()
                return
            
            # ✅ SỬA: Kiểm tra auth TRƯỚC redirect
            if hook_result.get("auth") == "false":
                print(f"[HttpAdapter] Auth failed, sending 401")
                response = resp.build_unauthorized()
                conn.sendall(response)
                conn.close()
                return
            
            # ✅ SỬA: Xử lý redirect
            redirect = hook_result.get("redirect")
            if redirect:
                new_session_id = hook_result.get("session_id")
                print(f"[HttpAdapter] Redirecting to {redirect} with session_id={new_session_id}")
                response = resp.build_redirect(redirect, req, new_session_id)
                conn.sendall(response)
                conn.close()
                return

            # ✅ SỬA: Xử lý content placeholder
            content = hook_result.get("content")
            placeholder = hook_result.get("placeholder")
            
            if placeholder:
                print(f"[HttpAdapter] Building content with placeholder")
                response = resp.build_content_placeholder(req, content, placeholder)
                conn.sendall(response)
                conn.close()
                return

            if content:
                print(f"[HttpAdapter] Setting req.path to {content}")
                req.path = content

        # ========================================
        # BƯỚC 12: BUILD VÀ GỬI RESPONSE
        # ========================================
        print(f"[HttpAdapter] Building response for {req.method} {req.path}")
        response = resp.build_response(req)
        conn.sendall(response)
        conn.close()

    # @property
    # def extract_cookies(self, req, resp):
    #     """
    #     Build cookies from the :class:`Request <Request>` headers.

    #     :param req:(Request) The :class:`Request <Request>` object.
    #     :param resp: (Response) The res:class:`Response <Response>` object.
    #     :rtype: cookies - A dictionary of cookie key-value pairs.
    #     """
    #     cookies = {}
    #     for header in headers:
    #         if header.startswith("Cookie:"):
    #             cookie_str = header.split(":", 1)[1].strip()
    #             for pair in cookie_str.split(";"):
    #                 key, value = pair.strip().split("=")
    #                 cookies[key] = value
    #     return cookies

    # def build_response(self, req, resp):
    #     """Builds a :class:`Response <Response>` object 

    #     :param req: The :class:`Request <Request>` used to generate the response.
    #     :param resp: The  response object.
    #     :rtype: Response
    #     """
    #     response = Response()

    #     # Set encoding.
    #     response.encoding = get_encoding_from_headers(response.headers)
    #     response.raw = resp
    #     response.reason = response.raw.reason

    #     if isinstance(req.url, bytes):
    #         response.url = req.url.decode("utf-8")
    #     else:
    #         response.url = req.url

    #     # Add new cookies from the server.
    #     response.cookies = extract_cookies(req)

    #     # Give the Response some context.
    #     response.request = req
    #     response.connection = self

    #     return response

    # # def get_connection(self, url, proxies=None):
    #     # """Returns a url connection for the given URL. 

    #     # :param url: The URL to connect to.
    #     # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
    #     # :rtype: int
    #     # """

    #     # proxy = select_proxy(url, proxies)

    #     # if proxy:
    #         # proxy = prepend_scheme_if_needed(proxy, "http")
    #         # proxy_url = parse_url(proxy)
    #         # if not proxy_url.host:
    #             # raise InvalidProxyURL(
    #                 # "Please check proxy URL. It is malformed "
    #                 # "and could be missing the host."
    #             # )
    #         # proxy_manager = self.proxy_manager_for(proxy)
    #         # conn = proxy_manager.connection_from_url(url)
    #     # else:
    #         # # Only scheme should be lower case
    #         # parsed = urlparse(url)
    #         # url = parsed.geturl()
    #         # conn = self.poolmanager.connection_from_url(url)

    #     # return conn


    # def add_headers(self, request):
    #     """
    #     Add headers to the request.

    #     This method is intended to be overridden by subclasses to inject
    #     custom headers. It does nothing by default.

        
    #     :param request: :class:`Request <Request>` to add headers to.
    #     """
    #     pass

    # def build_proxy_headers(self, proxy):
    #     """Returns a dictionary of the headers to add to any request sent
    #     through a proxy. 

    #     :class:`HttpAdapter <HttpAdapter>`.

    #     :param proxy: The url of the proxy being used for this request.
    #     :rtype: dict
    #     """
    #     headers = {}
    #     #
    #     # TODO: build your authentication here
    #     #       username, password =...
    #     # we provide dummy auth here
    #     #
    #     username, password = ("user1", "password")

    #     if username:
    #         headers["Proxy-Authorization"] = (username, password)

    #     return headers