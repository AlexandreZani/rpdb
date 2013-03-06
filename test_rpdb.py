import unittest
import os
import subprocess
import factor
import rpdb
import time
import signal
import socket
import json

# Do not move
def start_prog():
  pid = os.fork()
  if pid == 0:
    rpdb.set_trace()
    factor.factor_fibonacci(num=10)

  return pid
# Do not move

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

class TestRpdb(unittest.TestCase):
  def connect_socket(self, tries_left=10):
    try:
      self.conn = socket.socket(rpdb.ADDR_FAMILY, socket.SOCK_STREAM)
      self.conn.connect(rpdb.SOCKET_ADDR)
    except Exception:
      time.sleep(1)
      if tries_left == 0:
        raise
      self.connect_socket(tries_left-1)

  def setUp(self):
    self.child = subprocess.Popen(['./factor.py'])
    tries_left = 10
    self.connect_socket()
    self.jsock = rpdb.JsonSocket(self.conn)

  def tearDown(self):
    self.child.kill()
    self.conn.close()

  def test_first_frame_sent(self):
    msg = self.jsock.recv_msg()

    self.assertEquals('current_frame', msg['type'])
    self.assertEquals(31, msg['line_no'])
    self.assertIn('factor.py', msg['file'])

  def test_step(self):
    msg = self.jsock.recv_msg()

    self.jsock.send_msg({'command': 'step'})

    msg = self.jsock.recv_msg()
    self.assertEquals('current_frame', msg['type'])
    self.assertEquals(8, msg['line_no'])
    self.assertIn('factor.py', msg['file'])

  def test_break(self):
    msg = self.jsock.recv_msg()

    self.jsock.send_msg({
      'command': 'set_breaks',
      'args': {
        'breaks': [
          {
            'file': 'primes.py',
            'line_no': 12,
          },
        ],
      }
    })

    self.jsock.send_msg({'command': 'continue'})

    msg = self.jsock.recv_msg()
    self.assertEquals('current_frame', msg['type'])
    self.assertEquals(12, msg['line_no'])
    self.assertIn('primes.py', msg['file'])

  def test_clean_breaks(self):
    msg = self.jsock.recv_msg()

    self.jsock.send_msg({
      'command': 'set_breaks',
      'args': {
        'breaks': [
          {
            'file': 'primes.py',
            'line_no': 8,
          },
          {
            'file': 'fibonacci.py',
            'line_no': 12,
          },
        ]
      }
    })

    self.jsock.send_msg({
      'command': 'clear_breaks',
      'args': {
        'breaks': [
          {
            'file': 'fibonacci.py',
            'line_no': 12,
          }
        ]
      }
    })

    self.jsock.send_msg({'command': 'continue'})

    msg = self.jsock.recv_msg()
    self.assertEquals('current_frame', msg['type'])
    self.assertEquals(8, msg['line_no'])
    self.assertIn('primes.py', msg['file'])

  def test_next(self):
    msg = self.jsock.recv_msg()

    self.jsock.send_msg({
      'command': 'set_breaks',
      'args': {
        'breaks': [
          {
            'file': 'primes.py',
            'line_no': 8,
          },
        ]
      }
    })

    self.jsock.send_msg({
      'command': 'continue'
    })
    msg = self.jsock.recv_msg()

    self.jsock.send_msg({
      'command': 'next'
    })

    msg = self.jsock.recv_msg()

    self.assertEquals('current_frame', msg['type'])
    self.assertEquals(9, msg['line_no'])
    self.assertIn('primes.py', msg['file'])
