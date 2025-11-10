# Computer Network (CO3094) Assignment 1: Simple peer-to-peer chatting web app.

This document provides an overview of the key Python scripts and modules in this project.

## Table of Contents

- [1. How to run](#1-how-to-run)
  - [Option 1: Run server and clients on 1 computer](#option-1-run-server-and-clients-on-1-computer)
  - [Option 2: Run server on 1 computer and each client on a computer](#option-2-run-server-on-1-computer-and-each-client-on-a-computer)
- [2. Usage](#2-usage)
  - [Chat between 2 peer](#chat-between-2-peer)
  - [Chat in a channel (group of multiple peers)](#chat-in-a-channel-group-of-multiple-peers)
- [3. Main flow](#3-main-flow)
- [4. Implementation logic](#4-implementation-logic)
  - [`daemon/request.py`](#daemonrequestpy)
  - [`daemon/response.py`](#daemonresponsepy)
  - [`daemon/httpadapter.py`](#daemonhttpadapterpy)
  - [`start_app.py`](#start_apppy)
  - [`start_p2p.py`](#start_p2ppy)



## 1. How to run

###  Option 1: Run server and clients on 1 computer

To start the server, open 2 terminals and run:
```bash
python start_app.py --server-ip 127.0.0.1 --server-port 8000
```
```bash
python start_proxy.py --server-ip 127.0.0.1 --server-port 8000
```
In this specific configuration, the application runs 2 backend servers on port 8001 and 8002, and the proxy listens on port 8000. The proxy forwards requests to the application based on the configuration in `config/proxy.conf`.

Open 2 more terminals that act as 2 clients:
```bash
python start_p2p.py --chat-ip 127.0.0.1 --chat-port 12000 --server-port 10000
```
```bash
python start_p2p.py --chat-ip 127.0.0.1 --chat-port 12001 --server-port 10001
```

Then open private/incognito window on 2 different browser and access `http://127.0.0.1:8000/`.

![Find private IP](/static/images/same_computer.png)

After login/register successfully, each client need to submit 3 information before chatting:
- **Chat IP**: The IP address of client that other client will use to send messages to. It is the value of argument `--chat-ip` when client run `start_p2p.py`. Specifically, in this example it is `127.0.0.1` (the same for both 2 client as we only use 1 computer).
- **Chat port**: The port of client that other client will use to send messages to. It is the value of argument `--chat-port` when client run `start_p2p.py`. Specifically, in this example it is `12000` for client 1 and `12001` for client 2. 
- **Local port**: The port of the peer-to-peer localhost server of client that serve as the UI on the browser for chatting. It is the value of argument `--server-port` when client run `start_p2p.py`. Specifically, in this example it is `10000` for client 1 and `10001` for client 2. 

![Submit info](/static/images/submit.png)

> **Note**: Because we are only using 1 computer, we need to make sure the port used for each client are different from each other and from server's.

### Option 2: Run server on 1 computer and each client on a computer

Suppose there are 3 computer (A, B, C), computer A acts as server, and computer B and C are clients. The server and clients all need to be on the same LAN.

On each computer, find its own private IP address (temporarial address assigned by LAN):

![Find private IP](/static/images/ipv4.png)

For example, suppose the IP address of each computer is:
- Computer A: `192.168.1.6`
- Computer B: `192.168.1.11`
- Computer C: `192.168.1.27`

Before starting server, the computer running server (computer A) need to add to its `config/proxy.conf` a new proxy configuration if not existed for its current IP address. For this example, computer A need to add a new configuration like below if it want the proxy to listen on port 8000 and 2 backend server to listen on port 8001 and 8002:

```conf
host "192.168.1.6:8000" {
    proxy_pass http://192.168.1.6:8001;
    proxy_pass http://192.168.1.6:8002;
}
```

To start the server, computer A open 2 terminals and run:
```bash
python start_app.py --server-ip 192.168.1.6 --server-port 8000
```
```bash
python start_proxy.py --server-ip 192.168.1.6 --server-port 8000
```
Computer B run:
```bash
python start_p2p.py --chat-ip 192.168.1.11 --chat-port 12000 --server-port 10000
```
Computer C run:
```bash
python start_p2p.py --chat-ip 192.168.1.27 --chat-port 12000 --server-port 10000
```

Then computer B and computer C each can access `http://192.168.1.6:8000` to join. Each client then need to submit their respective Chat IP - Chat port - Local port before chatting.

> **Note**: Because we are using 1 computer for server and each client, the ports for them don't have to be different.



## 2. Usage

###  Chat between 2 peer

At index page, select "_2. Get list of active peer address_". A page with a list of peer address will appear. Click on "_Chat_" button next to a peer to chat to them.

There is also a button "_Broadcast_" at the end to send message to every peer on the list.

###  Chat in a channel (group of multiple peers)

At index page, select "_3. View channels_". A page with a list of channel will appear.
You can create a new channel, or join any existing channels.

- To create a new channel, input channel name and password and click "_Create_"

- To join an existing channel, input the channel's password in the box next to that channel name, then click "_Join_".

After you have created or joined a channel, it will appear on the "Joined" list. Click on the "_Chat_" button next to a channel name to begin chatting.

## 3. Main flow

1. The server run `start_app.py`, and each user (client/peer) run `start_p2p.py` on their computer.
2. When a user register/login, they are given cookie with `auth=true` and a random number `session_id`. This session id is also stored on server for authentication. When a user logout, the server remove that session id from memory.
3. After login, user has to sumbit their chatting IP and port. This address will be used by other users (peer) to send message to.
4. User also need to submit their "local" port, which is the port where the script `start_p2p.py` listen to. This script will open a local server on `127.0.0.1:<local_port>` that allow user to chat peer to peer from their browser UI.
5. After submitting the address, user can start chatting peer to peer. There are 2 options:
   - Chatting between 2 peers: Messages are sent using TCP protocol between 2 peer.
   - Chatting in channel (group chat): Message from one peer are sent to every peer in the channel.

## 4. Implementation logic

### `daemon/request.py`

This module is responsible for parsing raw HTTP requests received from a client into a structured `Request` object that is easier to work with.


-   **`extract_request_line(self, request)`**: Parses the first line of the HTTP request string (e.g., `"GET /index.html HTTP/1.1"`) to extract the HTTP method, path, and protocol version.
-   **`prepare_headers(self, request)`**: Parses the block of HTTP headers from the raw request string into a dictionary of key-value pairs. Header keys are converted to lowercase for case-insensitive access.
-   **`prepare_body(self, data, ...)`**: Parses the body of the request. It specifically handles `application/x-www-form-urlencoded` content by parsing it into a dictionary.
-   **`prepare_cookies(self, cookies)`**: Parses the `Cookie` header string into a dictionary, making individual cookie values easily accessible.
-   **`prepare(self, request, routes=None)`**: This is the main method that orchestrates the entire parsing process. It takes the full raw HTTP request string and:
    1.  Calls `extract_request_line` to get the method and path.
    2.  Parses any query parameters from the path (e.g., `?key=value`).
    3.  Identifies if the requested path matches a predefined application route (`hook`).
    4.  Calls `prepare_headers` to parse the headers.
    5.  Calls `prepare_body` to parse the body.
    6.  Calls `prepare_cookies` to parse cookies.
    7.  Stores all parsed information in the `Request` object's attributes.

---

### `daemon/response.py`

This module handles the creation of HTTP responses that will be sent back to the client. It constructs everything from the status line and headers to the response body.

-   **`get_mime_type(self, path)`**: Determines the MIME type of a file based on its extension (e.g., `.html` -> `text/html`). This is crucial for the browser to correctly interpret the content.
-   **`prepare_content_type(self, mime_type)`**: Sets the `Content-Type` header and determines the correct base directory (`www/`, `static/`, etc.) from which to serve the file based on its MIME type.
-   **`build_content(self, path, base_dir)`**: Reads the actual file content from the filesystem given a path and base directory.
-   **`build_response_header(self, request)`**: Assembles the complete block of HTTP response headers, including dynamic values like `Date`, `Content-Length`, and `Content-Type`.
-   **`build_notfound(self)`**: Constructs a standard `404 Not Found` HTTP response.
-   **`build_unauthorized(self)`**: Constructs a standard `401 Unauthorized` HTTP response.
-   **`build_redirect(self, path, ...)`**: Constructs a `302 Found` response to redirect the browser to a new URL. It can also include a `Set-Cookie` header for session management.
-   **`build_post_redirect_page(self, path, body_dict)`**: A clever utility that generates an HTML page with a self-submitting form. This is used to "redirect" a client to a new page using the `POST` method, carrying over data in the form's hidden fields.
-   **`build_content_placeholder(self, req, html_content, placeholders)`**: A simple templating function that replaces placeholder values in an HTML file with dynamic data provided by the application logic.
-   **`build_response(self, request)`**: The main method that constructs the final, complete HTTP response. It determines the MIME type of the requested resource, reads its content, builds the headers, and combines them into a single byte string ready to be sent over the socket.

---

### `daemon/httpadapter.py`

The `HttpAdapter` acts as the orchestrator for a single client-server interaction. It uses the `Request` and `Response` modules to process an incoming request and send back a reply.

#### `HttpAdapter` Class


-   **`handle_client(self, conn, addr, routes)`**: This is the core method of the server. For each new client connection, it does the following:
    1.  Receives the raw HTTP request data from the client's socket.
    2.  Uses the `request.prepare()` method to parse the raw data into a structured `Request` object.
    3.  Checks if the request's method and path correspond to a registered application route (a "hook").
    4.  **If a hook exists**: It calls the associated function from `start_app.py` or `start_p2p.py`. The return value from this function (a dictionary) dictates the response. It can specify:
        -   `"auth": "false"`: Send a `401 Unauthorized` response.
        -   `"redirect": "/path"`: Send a `302 Redirect` response.
        -   `"temp_redirect": "http://..."`: Use the `build_post_redirect_page` to perform a POST redirect.
        -   `"content": "file.html"`: Serve a static file, potentially with dynamic data via the `"placeholder"` key.
    5.  **If no hook exists**: It defaults to treating the request as a request for a static file (e.g., an image, CSS file, or HTML page) and uses `response.build_response()` to serve it.
    6.  Sends the final composed HTTP response back to the client.
    7.  Closes the connection.

---

### `start_app.py`

This script is the **central coordination server**. It does not handle any peer-to-peer communication itself but acts as a registry and authentication authority for all peers. It manages user accounts, sessions, and channel information.

#### Application Logic

-   **State Management**: It uses global dictionaries (`accounts`, `session_to_account`, `account_to_address`, `channels`) to store all application state in memory. This includes usernames, hashed passwords, session IDs, the network addresses of peers, and chat channel details.
-   **Authentication**: The `authenticate` function checks for a `session_id` in the request's cookies and verifies if it's a valid, active session.
-   **Routing**: It defines several API endpoints using the `@app.route` decorator.

#### Key Endpoints

-   **/login, /register**: Handle user authentication and new account creation. On success, they create a new session ID and send it back to the client as a cookie in a redirect response.
-   **/logout**: Clears a user's session and removes their registered address from the server.
-   **/submit-info**: Allows a logged-in user to register their P2P listening address (IP and port) with the server. This is a crucial step before they can chat with others.
-   **/get-list**: Returns a list of all other active users and their registered P2P addresses. It also provides a form to initiate a broadcast to all peers.
-   **/channel, /create-channel, /join-channel**: Endpoints for managing chat channels. Users can create new channels, view existing ones, and get the necessary information to join them.
-   **/connect-channel**: This endpoint is particularly interesting. When a user wants to join a channel, this route returns a `temp_redirect` response. This triggers the `HttpAdapter` to use the `build_post_redirect_page` method, which sends a POST request to the user's *own* P2P client, telling it to connect to the other peers in that channel.

---

### `start_p2p.py`

This script is the **peer-to-peer (P2P) client**. Each user runs an instance of this application. It has two main components: a web server for a user interface and a P2P networking component for direct communication with other peers.

#### P2P Networking Logic

-   **`start_server(host, port)`**: Starts a TCP socket server in a background thread. This server continuously listens for incoming messages from other peers.
-   **`handle_incoming_connection(connection)`**: When another peer connects, this function reads the message, decodes it, and processes it.
-   **`send_message(target_ip, target_port, content)`**: Connects to another peer's listening socket to send them a message directly.
-   **`run(my_ip, my_port)`**: The main loop for the P2P functionality. It starts the listening server and includes logic for handling user input from the command line (though the primary UI is web-based).
-   **`send_queue`**: A `queue.Queue` is used to safely send messages from the web server thread to the P2P networking thread, preventing race conditions.

#### Web Interface Logic

This script also runs a `WeApRous` web application that serves as the user interface for the chat client.

-   **/connect-peer**: Takes an IP and port from a form and redirects the user to the chat interface for that peer.
-   **/chat**: The main chat interface.
    -   `GET`: Displays the chat history with a specific peer.
    -   `POST`: Takes a message from the user, puts it into the `send_queue` to be sent by the P2P networking thread, and then redirects back to the chat page to refresh the view.
-   **/broadcast, /broadcast0**: Handles sending a message to all peers in the `peer_list`.
-   **/channel, /connect-channel**: Handles the UI for group chats. When a user joins a channel, the `/connect-channel` endpoint receives a POST request (from the central server's `temp_redirect`) containing the list of peers in that channel. It then sends a "has joined" message to all of them.
