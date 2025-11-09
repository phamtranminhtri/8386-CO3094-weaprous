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
        msg = conn.recv(8192).decode()
        req.prepare(msg, routes)

        # Handle request hook
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
            hook_result = req.hook(headers=req.headers, body=req.body)
            #
            # TODO: handle for App hook here
            #
            if hook_result["auth"] == "false":
                response = resp.build_unauthorized()
                conn.sendall(response)
                conn.close()
                return
            
            new_session_id = hook_result.get("session_id", None)
            
            redirect = hook_result.get("redirect", None)
            if redirect:
                response = resp.build_redirect(redirect, req, new_session_id)
                conn.sendall(response)
                conn.close()
                return
            
            temp_redirect = hook_result.get("temp_redirect", None)
            temp_body = hook_result.get("temp_body", "")
            if temp_redirect:
                print(f"\n\n{temp_redirect}\n\n{temp_body}\n\n")
                response = resp.build_post_redirect_page(temp_redirect, temp_body)
                conn.sendall(response)
                conn.close()
                return


            content = hook_result.get("content", None)
            placeholder = hook_result.get("placeholder", None)
            if placeholder:
                response = resp.build_content_placeholder(req, content, placeholder)
                conn.sendall(response)
                conn.close()
                return


            if content:
                req.path = content
            

        # Build response
        response = resp.build_response(req)

        #print(response)
        conn.sendall(response)
        conn.close()
