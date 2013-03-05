import bdb
import socket
import json

ADDR_FAMILY = socket.AF_INET
SOCKET_ADDR = ('localhost', 58000)
SOCKET_ADDR_LISTEN = ('', 58000)

class JsonSocket(object):
  def __init__(self, sock):
    self.sock = sock
    self.data = ''

  def recv_msg(self):
    eos = self.data.find('\r\n')
    while eos < 0:
      self.data += self.sock.recv(1024)
      eos = self.data.find('\r\n')
    size = int(self.data[:eos])

    self.data = self.data[eos+2:]
    while len(self.data) < size:
      self.data += self.sock.recv(1024)

    json_str = self.data[:size]
    self.data = self.data[size:]
    return json.loads(json_str)

  def send_msg(self, obj):
    obj_json = json.dumps(obj)
    msg_sz = len(obj_json)
    self.sock.sendall(str(msg_sz) + '\r\n' + obj_json)

  def close(self):
    self.sock.close()

def set_trace():
  Rpdb().set_trace()

class Rpdb(bdb.Bdb):
  def __init__(self, skip=None):
    bdb.Bdb.__init__(self, skip=skip)

    self.listening_socket = socket.socket(ADDR_FAMILY, socket.SOCK_STREAM)
    self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.listening_socket.bind(SOCKET_ADDR_LISTEN)
    self.listening_socket.listen(1)

    self.sock = None
    self.wait_for_client()

  def __del__(self):
    if self.sock is not None:
      self.sock.close()
    self.listening_socket.close()

  def wait_for_client(self):
    conn, addr = self.listening_socket.accept()
    self.sock = JsonSocket(conn)
    print addr

  def get_command(self):
    msg = self.sock.recv_msg()

  def user_line(self, frame):
    msg = {
        'type': 'current_frame'
        }
    self.sock.send_msg(msg)
    return
    import linecache
    name = frame.f_code.co_name
    if not name: name = '???'
    fn = self.canonic(frame.f_code.co_filename)
    line = linecache.getline(fn, frame.f_lineno, frame.f_globals)
    self.conn.sendall('line,' + fn + ',' + str(frame.f_lineno) + '\r\n')
    self.get_command()
    print('+++', fn, frame.f_lineno, name, ':', line.strip())

  def user_exception(self, frame, exc_stuff):
    print('+++ exception', exc_stuff)
    self.set_continue()
