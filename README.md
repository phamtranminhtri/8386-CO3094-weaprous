# Computer Network (CO3094) Assignment 1: Simple peer-to-peer chatting web app.

This document provides an overview of the key Python scripts and modules in this project.

## How to Run

To start the web app, open 2 terminals and run:
```bash
python start_app.py --server-ip 127.0.0.1 --server-port 8000
```
```bash
python start_proxy.py --server-ip 127.0.0.1 --server-port 8000
```
Then open a browser and access `http://127.0.0.1:8000/`. 

> Note: The application runs 2 backend servers on port 8001 and 8002, and the proxy listens on port 8000. The proxy forwards requests to the application based on the configuration in `config/proxy.conf`.

## Codebase Description

### 1. Entry Points: `start_app.py` and `start_proxy.py`

These two scripts are the main entry points for running the application and the proxy server.

*   **`start_app.py`**: This script launches the main web application.
    *   It uses a custom micro-framework defined in `daemon/weaprous.py`.
    *   It defines several routes to handle user authentication, registration, and the core logic of the peer-to-peer chat application.
    *   **Routes include**:
        *   `/login` (GET and POST): Handles user login.
        *   `/register` (GET and POST): Manages new user registration.
        *   `/logout` (POST): Clears user session data.
        *   `/` (GET): The main index page, which is only accessible after authentication.
        *   `/submit-info` (GET and POST): Allows users to submit their IP address and port for chatting.
        *   `/get-list` (GET): Displays a list of active users and their addresses.
    *   It maintains in-memory dictionaries to store user accounts, session information, and the mapping of accounts to network addresses.

*   **`start_proxy.py`**: This script starts a reverse proxy server.
    *   It reads a configuration file (`config/proxy.conf`) to determine how to route incoming requests.
    *   The configuration file defines "virtual hosts" and specifies where to forward requests for each host (using `proxy_pass`).
    *   It uses the `create_proxy` function from `daemon/proxy.py` to initialize and run the proxy server.

### 2. Core Server Logic: `daemon/proxy.py` and `daemon/backend.py`

These modules contain the fundamental logic for the proxy and backend servers.

*   **`daemon/proxy.py`**: This module implements the reverse proxy.
    *   It listens for incoming client connections and forwards them to the appropriate backend server based on the `Host` header of the HTTP request.
    *   It supports load balancing policies, such as **round-robin**, when multiple backend servers are defined for a single virtual host.
    *   The `parse_virtual_hosts` function reads the `proxy.conf` file and builds a routing table.
    *   Each client connection is handled in a separate thread to allow for concurrent request processing.

*   **`daemon/backend.py`**: This module provides a simple backend server framework.
    *   It is responsible for accepting incoming connections and delegating the handling of each request to an `HttpAdapter` instance.
    *   Like the proxy, it uses multi-threading to handle multiple clients at the same time.
    *   The `create_backend` function is the main entry point for starting a backend server on a given IP and port.

### 3. HTTP Handling: `httpadapter.py`, `request.py`, and `response.py`

This trio of modules forms the core of the HTTP processing pipeline.

*   **`daemon/request.py`**: Defines the `Request` class.
    *   This class is responsible for parsing raw HTTP requests received from a client.
    *   It extracts the method (e.g., GET, POST), path, headers, and body from the request string.
    *   It also handles URL-encoded form data and cookies.

*   **`daemon/response.py`**: Defines the `Response` class.
    *   This class is used to construct HTTP responses to be sent back to the client.
    *   It can build various types of responses:
        *   **File-based content**: It determines the MIME type of a file and serves it with the correct `Content-Type` header.
        *   **Redirects**: It can generate `302 Found` responses to redirect the client to a different URL.
        *   **Error pages**: It can create `404 Not Found` and `401 Unauthorized` responses.
        *   **Dynamic content**: It can inject data into HTML templates by replacing placeholders (e.g., `{{ placeholder_0 }}`).

*   **`daemon/httpadapter.py`**: Defines the `HttpAdapter` class, which connects the `Request` and `Response` objects.
    *   It receives a raw request from the backend server.
    *   It uses the `Request` class to parse the request.
    *   It checks if the requested path matches any of the application's defined routes (hooks).
    *   If a route matches, it executes the corresponding handler function from `start_app.py`.
    *   Based on the result from the route handler, it uses the `Response` class to build and send the final HTTP response to the client.

### 4. HTML Files

The `www/` directory contains the HTML files that make up the user interface of the web application.

*   **`index.html`**: The main dashboard for logged-in users. It displays a welcome message and provides links to submit connection info or view the list of peers.
*   **`login.html`**: A simple form for users to enter their username and password to log in.
*   **`register.html`**: A form for new users to create an account.
*   **`submit-info.html`**: A form where users can submit their IP address and port to be listed as an active peer for chatting.
*   **`get-list.html`**: A page that dynamically displays the list of all active peers and their submitted network addresses. The content is populated by the `Response` class using a placeholder.
