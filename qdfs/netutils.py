import socket


def getport(sockets, for_ip='0.0.0.0'):
    s = filter(lambda s: s.getsockname()[0] == for_ip, sockets)[0]
    return s.getsockname()[1]


def gethostname():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 53))  # connecting to a UDP address doesn't send packets
    return s.getsockname()[0]

def create_multicast_socket(addr):
    host, port = addr
    # Create the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.setblocking(False)

    # Set some options to make it multicast-friendly
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 20)
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

    s.bind(('', port))

    # Set some more multicast options
    intf = socket.gethostbyname(socket.gethostname())
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(intf))
    s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(host) + socket.inet_aton(intf))
    
    return s

