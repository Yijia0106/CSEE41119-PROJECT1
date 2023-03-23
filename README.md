
Name: Yijia Wang

UNI: yw3936

# CSEE W4119 Project1


For this computer network project, I implemented a simple chat program involving one server and multiple clients with Python 3.10 and UDP socket concept. In a nutshell, in the normal mode, client can privately message each other and also has the option to create a group chat. Joining a group chat would convert the client's mode to inGroup and allows in-group communications with other members, but any private messages will be blocked temporarily untill client leaves the group chat. Any state change caused by operations such as log-on and log-off will be captured by server and broadcast to every online client.

## How to Start

To run the program, one must first start the server with the following line of code, in which the port_number must be assigned.
```http
  python3 chatApp.py -s port_number
```

Then, an arbitrary number of clients can be started to join the chat program with the following line of code, in which userName, server_ip, server_port, and port_num must be assigned and port_num need to correspond to the port number of the server.
```http
  python3 chatApp.py -c username, server_ip, server_port port_num
```

This program has an error detection mechanism to check every varaiables mentioned above are valid and in range.

## Client API

Most of the operations listed below have a block-and-wait mechanism: client would sleep for around 0.5 second and check if the previous command is acknowledged by the target. If it is, subsequent commands are permissble. Otherwise, the client would either report to the server or disconnect.

#### Send private message to online client (normal)
```
  send someone msg
```

#### Create a group chat (normal)

```
  create_group group_name
```

#### Show all the existing grou chat (normal)

```
  list_groups
```

#### Join a specific group chat (normal)

```
  join_group group_name
```

#### Unregister self from server (normal/inGroup)

```
  Dereg user_name
```

#### Send group message (inGroup)

```
  send_group msg
```

#### Show all members within the same group chat (inGroup)

```
  list_members
```

#### leave the group chat (inGroup)

```
  leave_group
```

Generally speaking, if the input format contains more arguments than required, it would not lead to an error as long as the required fields are correct. However, if the input contains less fields than required, it would display "Invalid input" message.

Similarly, if the command is not compatible with the currect mode (e.g. does leave_group when in the normal mode), "Invalid Command." warning will be displayed.

## Data Structure & Functions Used

I didn't create a class for the server and client for this project due to its simplicity. Rather, I created multiple functions and globale variables.

### Server Side
#### Global variables

```registered_table```: a dictionary, in which the key is the username and the value is a list containing the client's IP address, port number, and its status (Online or Offline). This variable is used to store the real-time information of the clients.

```group_list```: a dictionary, in which the key is the group name and the value is a list containing all clients that are in this group chat. This variable is used for list_members command and indicate which client should receive group message from server.

```ack_cand```: a dictionary, in which the key is the username and the value is either 1 or 0. This variable is used to signal that when group message is sent to multiple clients, which client has successfully responded with ack within the 0.5 second timeframe. 1 means the ack of that client is collected and 0 means otherwise.

server_socket: a socket that are used to communicate with clients.

#### Notable functions

```server(port_number)```: start the server program, bind the socket and keep listening and reacting to different messages sent from clients.

```server_counting()```: after sleep 0.5 seconds, check which client in the specific group responds with an ack and modify ack_cand dictionary according to this.

```broadcast()```: send a copy of the most up-to-date user status table registered_table to every registered online client

All other server functions are related to server's ack responding to clients' command and request. The SOP is to create a specific header with desired content, send to clients, and print a "ACK sent!" message.

### Client Side
#### Global variables

```registered_users```: a dictionary that is replicated from server side with the exact same content.

```name```: string; client username.

```mode```: string that is used to indicate whether the client is in the normal mode or inGroup mode. The default value is normal.

```group```: a string indicating which group chat the client is in currently.

```server_ip```: a string indicating server's ip address

```server_port```: an integer indicating server's port number

```waitFor```: a string that is used to check whether the ack sent from other client is the one we are expecting currently. The use case is: A sent a private message to B (waitFor = B), and the ack from B gets delayed. After timeout, A notifies the server and marks B as Offline. Then A sent a private message to C (waitFor = C), which just silently left. At this time A gets the ack from B previously and by checking with waitFor, A knows this ack is not from C and would also notify server that C is Offline as well.

```message_queue```: a list containing private messages that client received during the time in the group chat.

```is_ack_c```: a boolean variable indicating whether this client has received ack from the target clients during sleep time.

```is_ack_s```: a boolean variable indicating whether this client has received ack from the server during sleep time.

```listen_socket```: a socket that is used for listening on port.

```client_socket```: a socket that is used for sending messages by user.

#### Notable functions

```client(user_name, ip, port, client_port)```: Start the client program, initialize global variables, and register self to the server. This function also serves as a main thread that constantly process user's command.

```client_listen()```: Another thread that constantly listens to the port and respond to the incoming demands and messages.

```client_res(client_ip, client_port)```: To send ack to other clients when getting private messages from them.

```client_res_group(client_ip, client_port)```: To send ack to server when getting the group message

```notifyServer(recipient)```: To let the server know that a client(recipient) is not responding to the private message.


```retryFiveTimes(to_send, trueMsg)```: To connect to the server with the desired message for another 5 times after failure for the first time.

```releaseMessageQueue()```: To print all messages in the message_queue.

```validifyOp(op)```: To check if the user's input command is valid under the current mode and command list.

```displayMsg(msg)```: To print messages in a format that is consistent to the current mode

## Bugs and Possible Enhancement

I have fixed any sensible bug by the time I am writing this ReadMe. If there is any during your interaction with my program, please let me know!

So far, my program can perform any required functionality, but it is still a very simple one and there are many aspects that can be improved. For example, after sending a message, my program needs to sleep for 0.5 seconds before it can check the status of the ack recerived. This works fine for a small-scale use-case but it would harm the efficience when there are millions of users sending messages to each other. 
