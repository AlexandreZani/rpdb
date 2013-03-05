import unittest
import os
import factor
import rpdb
import signal
import socket
import json

class FakeSocket(object):
  def __init__(self, recv_data=None):
    self.recv_data = recv_data or []
    self.sent = []

  def recv(self, _):
    if not self.recv_data:
      return None

    return self.recv_data.pop(0)

  def sendall(self, data):
    self.sent.append(data)

class TestJsonSocket(unittest.TestCase):
  def test_simple(self):
    expected = {
        'a': 1,
        'hello': 2,
        'foo': 'bar'
        }
    exp_s = json.dumps(expected)
    sock = FakeSocket([str(len(exp_s)) + '\r\n' + exp_s])
    jsock = rpdb.JsonSocket(sock)

    self.assertEquals(expected, jsock.recv_msg())

  def test_split_size(self):
    expected = {
        'a': 1,
        'hello': 2,
        'foo': 'bar'
        }
    exp_s = json.dumps(expected)
    msg_sz = str(len(exp_s))
    sock = FakeSocket([msg_sz[0], msg_sz[1:] + '\r\n' + exp_s])
    jsock = rpdb.JsonSocket(sock)

    self.assertEquals(expected, jsock.recv_msg())

  def test_split_msg(self):
    expected = {
        'a': 1,
        'hello': 2,
        'foo': 'bar'
        }
    exp_s = json.dumps(expected)
    msg_sz = str(len(exp_s))
    sock = FakeSocket([msg_sz + '\r\n' + exp_s[:10], exp_s[10:]])
    jsock = rpdb.JsonSocket(sock)

    self.assertEquals(expected, jsock.recv_msg())

  def test_second_msg(self):
    expected1 = {
        'a': 1,
        'hello': 2,
        'foo': 'bar'
        }
    exp_s1 = json.dumps(expected1)
    msg_sz1 = str(len(exp_s1))

    expected2 = {
        'kajhsd': 87,
        'khjahs': 'kasd'
        }
    exp_s2 = json.dumps(expected2)
    msg_sz2 = str(len(exp_s2))

    sock = FakeSocket([
      msg_sz1 + '\r\n' + exp_s1[:10],
      exp_s1[10:] + msg_sz2 + '\r\n' + exp_s2[:10],
      exp_s2[10:]
      ])
    jsock = rpdb.JsonSocket(sock)

    self.assertEquals(expected1, jsock.recv_msg())
    self.assertEquals(expected2, jsock.recv_msg())

  def test_send_msg(self):
    obj = {
        'a': 1,
        'hello': 2,
        'foo': 'bar'
        }
    exp_s = json.dumps(obj)
    msg_sz = str(len(exp_s))

    expected = msg_sz + '\r\n' + exp_s

    sock = FakeSocket()
    jsock = rpdb.JsonSocket(sock)
    jsock.send_msg(obj)

    self.assertEquals(expected, sock.sent[0])


def start_prog():
  pid = os.fork()
  if pid == 0:
    rpdb.set_trace()
    factor.factor_fibonacci(num=10)

  return pid

class TestRpdb(unittest.TestCase):

  def setUp(self):
    self.child_pid = start_prog()

  def tearDown(self):
    os.kill(self.child_pid, signal.SIGKILL)

  def test_setup_works(self):
    conn = socket.socket(rpdb.ADDR_FAMILY, socket.SOCK_STREAM)
    conn.connect(rpdb.SOCKET_ADDR)

    conn.close()

  def test_frame_on_first_connect(self):
    conn = socket.socket(rpdb.ADDR_FAMILY, socket.SOCK_STREAM)
    conn.connect(rpdb.SOCKET_ADDR)
    sock = rpdb.JsonSocket(conn)

    msg = sock.recv_msg()

    self.assertEquals('current_frame', msg['type'])
