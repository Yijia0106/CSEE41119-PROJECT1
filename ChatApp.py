import sys
from ServerSide import *
from ClientSide import *
from HelperMethods import *

if __name__ == "__main__":
    mode = sys.argv[1]

    if mode == '-s':
        try:
            server_port = int(sys.argv[2])
            if checkPort(server_port):
                server(server_port)
            else:
                print(">>> Invalid port range!")
        except:
            print(">>> Invalid port number!")


    elif mode == '-c':
        user_name = sys.argv[2]
        server_ip = sys.argv[3]
        if checkIp(server_ip):
            try:
                server_port = int(sys.argv[4])
                client_port = int(sys.argv[5])
                if checkPort(server_port) and checkPort(client_port):
                    client(user_name, server_ip, server_port, client_port)
                else:
                    print(">>> Invalid port range!")
            except:
                print(">>> Invalid port number!")
        else:
            print(">>> Invalid IP address")
