def checkPort(port):
    if port < 1024 or port > 65535:
        return False;
    return True


def checkIp(ip):
    if ip == "localhost":
        return True

    if len(ip.split(".")) != 3:
        return False

    for x in ip.split("."):
        if not x.isnumeric():
            return False

    return True
