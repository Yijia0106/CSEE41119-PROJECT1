import json
import os
import sys
import threading
import time
from socket import *

registered_users = dict()
client_socket = socket(AF_INET, SOCK_DGRAM)
listen_socket = socket(AF_INET, SOCK_DGRAM)
name = ""
is_ack_c = False
waitFor = ""
is_ack_s = False
mode = "normal"
group = ""
server_ip = ""
server_port = 0
message_queue = []


def client(user_name, ip, port, client_port):
    # initialization
    # semaphore = threading.Semaphore(1)
    global name, is_ack_c, is_ack_s, mode, group, server_port, server_ip, waitFor
    name = user_name
    server_ip = ip
    server_port = port
    # register client to the server
    init_msg = "header:\n" + "connect" + "\n" + "port:\n" + str(client_port) + "\nname\n" + user_name + "\nmessage\n" + " "
    client_socket.sendto(init_msg.encode(), (server_ip, server_port))
    # start listening process
    listen_socket.bind(('', client_port))
    listen = threading.Thread(target=client_listen, args=())
    listen.start()
    time.sleep(0.5)

    # keep sending commands

    while True:
        try:
            input_list = []
            try:
                if mode == "normal":
                    temp = input(">>> ")
                    input_list = temp.split()
                else:
                    temp = input(f">>> ({group}) ")
                    input_list = temp.split()
            except KeyboardInterrupt:
                silentLeave()
            if len(input_list) == 0:
                break
            header = input_list[0]
            # validify command
            if not validifyOp(header):
                continue
            # send message to other online clients. send a xxx
            if header == "send":
                recipient = input_list[1]
                if recipient in registered_users:
                    # check if the target client is online
                    if registered_users[recipient][2] != "Online":
                        displayMsg("[This client is not available at this point.]")
                        continue
                    msg = ""
                    for i in range(2, len(input_list)):
                        msg = msg + input_list[i] + " "
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\nmessage\n" + msg
                    # set the target name as a global variable
                    waitFor = recipient
                    client_socket.sendto(to_send.encode(), (registered_users[recipient][0], registered_users[recipient][1]))
                    displayMsg("[Message sent!]")
                    time.sleep(0.5)
                    if is_ack_c:
                        displayMsg(f"[Message received by {recipient}.]")
                        is_ack_c = False
                    else:
                        displayMsg(f"[No ACK from {recipient}, message not delivered.]")
                        notifyServer(recipient)
                else:
                    displayMsg("[User could not be found.]")

            # command to deregister self from server. dereg self
            elif header == "dereg":
                if input_list[1] == name:
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\nmessage\n" + " "
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                        displayMsg(f"[You are Offline. Bye.]")
                        os._exit(1)
                    else:
                        if not retryFiveTimes(to_send, server_ip):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg("[Incorrect username.]")
            # command to create a group. create_group xx
            elif header == "create_group":
                if mode == "normal":
                    group_name = input_list[1]
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\nname:\n" + group_name
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                    else:
                        if not retryFiveTimes(to_send, server_ip):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg("[You are already in a group chat room.]")
            # command to list all existing groups
            elif header == "list_groups":
                if mode == "normal":
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\nmessage\n" + " "
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if not is_ack_s:
                        is_ack_s = False
                        if not retryFiveTimes(to_send, server_ip):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg("[You cannot view all groups while in a group.]")
            # command to join a specific group
            elif header == "join_group":
                if mode == "normal":
                    group_name = input_list[1]
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\nname:\n" + group_name
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                    else:
                        if not retryFiveTimes(to_send, server_ip):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg(f"[You are already in a group.]")
            # command to send message within a group
            elif header == "send_group":
                if mode == "inGroup":
                    msg = ""
                    for i in range(1, len(input_list)):
                        msg = msg + input_list[i] + " "
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\ngroup:\n" + group + "\nmessage:\n" + msg
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                        displayMsg(f"[Message received by Server.]")
                    else:
                        if not retryFiveTimes(to_send, server_ip):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg(f"[You are not in a group.]")
            # command to list all members within the group
            elif header == "list_members":
                if mode == "inGroup":
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\ngroup:\n" + group
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                    else:
                        if not retryFiveTimes(to_send, ""):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg(f"[You can only list members when in a group.]")
            # command to leave group
            elif header == "leave_group":
                if mode == "inGroup":
                    group = ""
                    to_send = "header:\n" + header + "\n" + "port:\n" + str(
                        client_port) + "\nsource:\n" + name + "\ngroup:\n" + group
                    client_socket.sendto(to_send.encode(), (server_ip, server_port))
                    time.sleep(0.5)
                    if is_ack_s:
                        is_ack_s = False
                        releaseMessageQueue()
                    else:
                        if not retryFiveTimes(to_send, ""):
                            loseConnectionMsg()
                            os._exit(1)
                else:
                    displayMsg(f"[You are not in a group mode.]")
            else:
                displayMsg("[Invalid input!]")
        except:
            displayMsg("[Invalid input!]")


def client_listen():
    global mode, group, message_queue
    while True:
        buffer, sender_address = listen_socket.recvfrom(4096)
        buffer = buffer.decode()
        lines = buffer.splitlines()
        header = lines[1]

        # when server updates the registered clients tablex
        if header == "update":
            msg = lines[3]
            global registered_users, is_ack_s, is_ack_c
            registered_users = json.loads(msg)
            displayMsg("[Client table updated.]")
            print(registered_users)
        # when receive successfully registered message from server
        elif header == "register":
            state = lines[3]
            if state == "True":
                displayMsg("[Welcome, You are registered.]")
                # displayMsg(f"[client {name} is online...]")
                # displayMsg("[client is now listening...]")
            else:
                displayMsg("[You have already login somewhere else.]")
                os._exit(1)

        # when receive messages from other clients
        elif header == "send":
            source_port = int(lines[3])
            msg = lines[7]
            source_name = lines[5]
            if mode == "normal":
                displayMsg(f'[The header is {header}.]')
                displayMsg(f"{source_name}: " + msg)
                client_res(sender_address[0], source_port)
                displayMsg("[ACK Sent!]")
            else:
                message_queue.append(f"{source_name}: " + msg)
                client_res(sender_address[0], source_port)
        # when receive ack from other clients
        elif header == "ack":
            source_name = lines[5]
            if source_name == waitFor:
                displayMsg(f'[The header is {header}.]')
                msg = lines[7]
                is_ack_c = True
                displayMsg(f"[message: {msg}]")
        # when receive ack for creating new group
        elif header == "ack-create-group":
            is_ack_s = True
            displayMsg(f'[The header is {header}.]')
            value = lines[3]
            group_name = lines[5]
            if value == "approve":
                displayMsg(f"[Group {group_name} created by Server.]")
            else:
                displayMsg(f"[Group {group_name} already exists.]")
        # when receive ack for listing all group names
        elif header == "ack-groups-result":
            is_ack_s = True
            displayMsg(f'[The header is {header}.]')
            group_names = json.loads(lines[3])
            displayMsg("[Available group chats:]")
            for group_name in group_names:
                displayMsg(f"{group_name}")
        # when receive ack for joining a specific group
        elif header == "ack-join-group":
            is_ack_s = True
            displayMsg(f'[The header is {header}.]')
            value = lines[3]
            group_name = lines[5]
            if value == "approve":
                displayMsg(f"[Entered group {group_name} successfully.]")
                mode = "inGroup"
                group = group_name
            else:
                displayMsg(f"[{group_name} does not exists.]")
        # when receive ack for sending group messages from server
        elif header == "ack-group":
            sender_name = lines[3]
            displayMsg(f'[The header is {header}.]')
            msg = lines[5]
            if sender_name == name:
                is_ack_s = True
            else:
                global server_ip, server_port
                client_res_group(server_ip, server_port)
                displayMsg(f"Group_Message {sender_name}: {msg}")
        # when receive ack for list all members within the group
        elif header == "member-result":
            is_ack_s = True
            displayMsg(f'[The header is {header}.]')
            members = json.loads(lines[3])
            displayMsg(f"[Members in the group {group}:]")
            for member in members:
                displayMsg(f"{member}")
        # when receive ack for leaving a group
        elif header == "ack-leave-group":
            is_ack_s = True
            mode = "normal"
            displayMsg(f"[Leave group chat {group}.]")
        # when receive ack for unregistering self
        elif header == "ack-dereg":
            is_ack_s = True
            displayMsg(f'[The header is {header}.]')
        else:
            displayMsg("[Unknown header.]")


# ack format
def client_res(client_ip, client_port):
    ack = "header:\n" + "ack" + "\n" + "port:\n" + str(
        server_port) + "\nsource:\n" + name + "\nMessage:\nThis is an ACK from client"
    client_socket.sendto(ack.encode(), (client_ip, client_port))


# let the server know someone is offline
def notifyServer(recipient):
    msg = "header:\n" + "notify" + "\n" + "port:\n" + str(
                    server_port) + "\nsource:\n" + name + "\ntarget:\n" + recipient
    client_socket.sendto(msg.encode(), (server_ip, server_port))


# try to connect to server for 5 times
def retryFiveTimes(to_send, trueMsg):
    global is_ack_s, server_ip, server_port
    for i in range(5):
        client_socket.sendto(to_send.encode(), (server_ip, server_port))
        displayMsg(f"[Message sent! {i + 1} time(s) retrying...]")
        time.sleep(0.5)
        if is_ack_s:
            if len(trueMsg) > 0:
                displayMsg(trueMsg)
            is_ack_s = False
            return True
    return False


# release all stored messages when in the group mode
def releaseMessageQueue():
    for msg in message_queue:
        displayMsg(msg)


# check if the operation command fulfills the current mode
def validifyOp(op):
    global mode, group
    if mode == "normal":
        if op in ["send", "dereg", "create_group", "list_groups", "join_group"]:
            return True
    else:
        if op in ["send_group", "list_members", "leave_group", "dereg"]:
            return True
    displayMsg("[Invalid Command.]")
    return False


def displayMsg(msg):
    if mode == "normal":
        print(">>> "+msg)
    else:
        print(f">>> ({group}) "+msg)


def loseConnectionMsg():
    displayMsg(f"[Server not responding.]")
    displayMsg(f"[Exiting...]")


def silentLeave():
    os._exit(1)


def client_res_group(client_ip, client_port):
    ack = "header:\n" + "ack-group" + "\n" + "port:\n" + str(
        server_port) + "\nsource:\n" + name + "\nMessage:\nThis is an ACK from client"
    client_socket.sendto(ack.encode(), (client_ip, client_port))

# def waitForAck(semaphore):
#     global is_ack
#     while True:
#         buffer, sender_address = listen_socket.recvfrom(4096)
#         buffer = buffer.decode()
#         lines = buffer.splitlines()
#         header = lines[1]
#         if header == "ack":
#             print(f'>>> The header is {header}')
#             msg = lines[3]
#             is_ack = True
#             print(">>> message: " + msg)

