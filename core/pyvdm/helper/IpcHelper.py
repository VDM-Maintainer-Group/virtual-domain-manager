'''
IpcHelper: useful inter-process comm. function
@author: Mark Hong
@level: debug
'''
import dbus, socket

def udpFactor(port, ipAddr='127.0.0.1', type='tx'):
    ''' IPC with local UDP socket
    type-tx: use *send()* not *sendto()*
    type-rx: use *recv()*
    '''
    ipAddr, port = str(ipAddr), int(port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if type=='tx':
        sock.connect((ipAddr, port))
    else:
        sock.bind(('', port))
    return sock