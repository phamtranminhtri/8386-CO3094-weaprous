# Computer Network (CO3094) Assignment 1: Simple peer-to-peer chatting web app.

This document provides an overview of the key Python scripts and modules in this project.

## 1. How to run

### Option 1: Run server and clients on 1 computer

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