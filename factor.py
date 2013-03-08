#!/usr/bin/env python

import sys
import primes
import fibonacci
import rpdb

def factor_fibonacci(num=None, max=None):
  factors = []
  for f in xfactor_fibonacci(num=num, max=max):
    factors.append(f)
  return factors

def xfactor_fibonacci(num=None, max=None):
  for fib in fibonacci.xfibonacci(num=num, max=max):
    yield factor(fib)

def factor(num):
  factors = []
  for factor in xfactor(num):
    factors.append(factor)
  return factors

def xfactor(num):
  for prime in primes.xprimes(max=num):
    while num % prime == 0:
      yield prime
      num /= prime

if __name__ == '__main__':
  listening = True
  if len(sys.argv) > 1:
    if sys.argv[1] == 'listening':
      listening = True
      socket_addr = ('', 59000)
    elif sys.argv[1] == 'not_listening':
      listening = False
      socket_addr = ('localhost', 57000)

  rpdb.set_trace(listening=listening, socket_addr=socket_addr)
  factor_fibonacci(num=2)
