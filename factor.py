import primes
import fibonacci

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
