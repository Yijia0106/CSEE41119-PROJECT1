import os
import threading
import time
from socket import *
import json

registered_table = dict()  # name, ip, port, status
server_socket = socket(AF_INET, SOCK_DGRAM)
group_list = dict()
ack_cand = dict()


def server(port_num):
    global ack_cand, group_list, registered_table
    print(">>> [Server is online...]")
    server_socket.bind(('localhost', port_num))

    while True:
        try:
            buffer, client_address = server_socket.recvfrom(4096)
            buffer = buffer.decode()
        except KeyboardInterrupt:
            server_socket.close()
            os._exit(1)
        lines = buffer.splitlines()
        header = lines[1]
        client_port = int(lines[3])
        client_name = lines[5]
        value = lines[7]

        # when receive new user connection request
        if header == "connect":
            state = True
            if client_name in registered_table.keys():
                if registered_table[client_name][2] == "Offline":
                    registered_table[client_name][2] = "Online"
                else:
                    state = False
            if state:
                temp = [client_address[0], client_port, "Online"]
                registered_table[client_name] = temp
                print(">>> [Client table updated.]")
                register(state, client_address[0], client_port)
            else:
                print(">>> [Duplicate login detected.]")
                register(state, client_address[0], client_port)
        # when a client reports a disconnection of another client
        elif header == "notify":
            registered_table[value][2] = "Offline"
            print(">>> [Client table updated.]")
            broadcast()
        # when a client wants to disconnect
        elif header == "dereg":
            registered_table[client_name][2] = "Offline"
            print(">>> [Client table updated.]")
            broadcast()
            server_res_dereg(client_address[0], client_port)
        # when a client wants to create a new chat group
        elif header == "create_group":
            if value in group_list:
                server_res_create_group(client_address[0], client_port, value, False)
                print(f">>> [Client {client_name} creating group {value} failed, group already exists.]")
            else:
                server_res_create_group(client_address[0], client_port, value, True)
                group_list[value] = list()
                print(f">>> [Client {client_name} created group {value} successfully.]")
        elif header == "list_groups":
            print(f">>> [Client {client_name} requested listing groups, current groups:]")
            group_names = []
            for key in group_list.keys():
                print(f">>> {key}")
                group_names.append(key)
            server_res_list_groups(client_address[0], client_port, group_names)
        elif header == "join_group":
            if value in group_list:
                server_res_join_group(client_address[0], client_port, value, True)
                temp = group_list[value]
                temp.append(client_name)
                group_list[value] = temp
                print(f">>> [Client {client_name} joined group {value}.]")
                print(f">>> [The current group chats info are: {group_list}")
            else:
                server_res_join_group(client_address[0], client_port, value, False)
                print(f">>> [Client {client_name} joining group {value} failed, group does not exist.]")
        elif header == "send_group":
            msg = lines[9]
            broadcast_group(client_name, msg, value)
            print(f">>> [Client {client_name} sent group message: {msg}]")

            counting = threading.Thread(target=server_counting, args=())
            counting.start()
        elif header == "ack-group":
            ack_cand[client_name] = 1
        elif header == "list_members":
            print(f">>> [Client {client_name} requested listing members of group {value}:]")
            members = []
            for member in group_list[value]:
                print(f">>> {member}")
                members.append(member)
            server_res_list_members(client_address[0], client_port, members)
        elif header == "leave_group":
            temp = group_list[value]
            temp.remove(client_name)
            group_list[value] = temp
            print(f">>> [Client {client_name} left group {value}]")
            print(f">>> [The current group chats info are: {group_list}")
            server_res_leave_group(client_address[0], client_port)
        elif header == "leave":
            registered_table[client_name][2] = "Offline"
            print(">>> [Client table updated.]")
            broadcast()
        else:
            pass


def server_counting():
    global ack_cand
    time.sleep(0.5)
    for key, value in ack_cand.items():
        if value == 0:
            group_list[value].remove(key)
            print(f">>> [Client {key} not responsive, removed from group {value}.]")
    ack_cand = dict()


def server_res_dereg(client_ip, client_port):
    ack = f"header:\nack-dereg\nMessage:\nThis is an ACK from server"
    server_socket.sendto(ack.encode(), (client_ip, client_port))
    print(">>> [ACK Sent!]")


def register(state, ip, port):
    server_socket.sendto(f"header:\nregister\nstate\n{state}".encode(), (ip, port))
    time.sleep(0.3)
    if state:
        broadcast()


def broadcast():
    for user in registered_table.keys():
        if registered_table[user][2] == "Online":
            server_socket.sendto((f"header:\nupdate\nContent:\n" + json.dumps(registered_table)).encode(),
                                 (registered_table[user][0], registered_table[user][1]))


def server_res_create_group(client_ip, client_port, group_name, passed):
    if passed:
        ack = f"header:\nack-create-group\nValue:\napprove\ngroup:\n" + group_name
    else:
        ack = f"header:\nack-create-group\nValue:\ndeny\ngroup:\n" + group_name
    server_socket.sendto(ack.encode(), (client_ip, client_port))
    print(">>> [ACK Sent!]")


def server_res_list_groups(client_ip, client_port, group_names):
    server_socket.sendto((f"header:\nack-groups-result\nContent:\n" + json.dumps(group_names)).encode(),
                         (client_ip, client_port))
    print(">>> [ACK Sent!]")


def server_res_join_group(client_ip, client_port, group_name, passed):
    if passed:
        ack = f"header:\nack-join-group\nValue:\napprove\ngroup:\n" + group_name
    else:
        ack = f"header:\nack-join-group\nValue:\ndeny\ngroup:\n" + group_name
    server_socket.sendto(ack.encode(), (client_ip, client_port))
    print(">>> [ACK Sent!]")


def broadcast_group(sender_name, message, group_name):
    global ack_cand
    ack = f"header:\nack-group\nsender:\n{sender_name}\nmessage:\n" + message
    for client in group_list[group_name]:
        if registered_table[client][2] == "Online":
            server_socket.sendto(ack.encode(), (registered_table[client][0], registered_table[client][1]))
            if client != sender_name:
                ack_cand[client] = 0


def server_res_list_members(client_ip, client_port, members):
    server_socket.sendto((f"header:\nmember-result\nContent:\n" + json.dumps(members)).encode(),
                         (client_ip, client_port))
    print(">>> [ACK Sent!]")


def server_res_leave_group(client_ip, client_port):
    ack = f"header:\nack-leave-group\nMessage:\nThis is an ACK from server"
    server_socket.sendto(ack.encode(), (client_ip, client_port))
    print(">>> [ACK Sent!]")
