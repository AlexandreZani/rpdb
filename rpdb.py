import bdb
import socket
import json

ADDR_FAMILY = socket.AF_INET
SOCKET_ADDR = ('localhost', 59000)
SOCKET_ADDR_LISTEN = ('', 59000)
LISTENING = True

class JsonSocket(object):
  def __init__(self, sock):
    self.sock = sock
    self.data = ''

  def recv_msg(self):
    eos = self.data.find('\r\n')
    while eos < 0:
      chunk = self.sock.recv(1024)
      if len(chunk) == 0:
        return None
      self.data += chunk
      eos = self.data.find('\r\n')
    size = int(self.data[:eos])

    self.data = self.data[eos+2:]
    while len(self.data) < size:
      chunk = self.sock.recv(1024)
      if len(chunk) == 0:
        return None
      self.data += chunk

    json_str = self.data[:size]
    self.data = self.data[size:]
    return json.loads(json_str)

  def send_msg(self, obj):
    obj_json = json.dumps(obj)
    msg_sz = len(obj_json)
    self.sock.sendall(str(msg_sz) + '\r\n' + obj_json)

  def close(self):
    self.sock.close()

def set_trace(socket_family=None, socket_addr=None, listening=None):
  if listening is None:
    listening = LISTENING
  if socket_family is None:
    socket_family = ADDR_FAMILY
  if socket_addr is None:
    if listening:
      socket_addr = SOCKET_ADDR_LISTEN
    else:
      socket_addr = SOCKET_ADDR
  Rpdb(socket_family, socket_addr, listening).set_trace()

class Rpdb(bdb.Bdb):
  def __init__(self, socket_family, socket_addr, listening, skip=None):
    bdb.Bdb.__init__(self, skip=skip)
    self.sock = None
    self.socket_family = socket_family
    self.socket_addr = socket_addr
    self.listening = listening

    if self.listening:
      self.listening_socket = socket.socket(socket_family, socket.SOCK_STREAM)
      self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.listening_socket.bind(socket_addr)
      self.listening_socket.listen(1)

      self.wait_for_client()
    else:
      sock = socket.socket(socket_family, socket.SOCK_STREAM)

  def connect(self):
    sock = socket.socket(self.socket_family, socket.SOCK_STREAM)
    sock.connect(self.socket_addr)
    self.sock = JsonSocket(sock)

  def send_msg(self, msg):
    if self.sock is None:
      if self.listening:
        self.wait_for_client()
      else:
        self.connect()
    self.sock.send_msg(msg)

  def wait_for_client(self):
    conn, addr = self.listening_socket.accept()
    self.sock = JsonSocket(conn)

  def do_step(self, frame, args):
    self.set_step()
    return True

  def do_set_breaks(self, frame, args):
    for b in args['breaks']:
      fn = b['file']
      line_no = b['line_no']

      self.set_break(fn, line_no)
    return False

  def do_clear_breaks(self, frame, args):
    for b in args['breaks']:
      fn = b['file']
      line_no = b['line_no']

      self.clear_break(fn, line_no)
    return False

  def do_continue(self, frame, args):
    self.set_continue()
    return True

  def do_unknown(self, frame, args):
    self.send_msg({'type': 'unknown_command'})
    return False

  def do_next(self, frame, args):
    self.set_next(frame)
    return True

  def get_command(self, frame):
    while True:
      msg = self.sock.recv_msg()

      command = msg['command']
      method = getattr(self, 'do_' + command, self.do_unknown)
      if method(frame, msg.get('args', {})):
        break

  def user_line(self, frame):
    msg = {
        'type': 'current_frame',
        'file': self.canonic(frame.f_code.co_filename),
        'line_no': frame.f_lineno,
        }
    self.send_msg(msg)
    self.get_command(frame)

  def user_exception(self, frame, exc_stuff):
    print('+++ exception', exc_stuff)
    self.set_continue()
