def primes(num=None, max=None):
  primes = []
  for prime in xprimes(num=num, max=max):
    primes.append(prime)
  return primes

def xprimes(num=None, max=None):
  primes = []
  candidate = 2
  while True:
    if is_not_divisible(primes, candidate):
      primes.append(candidate)
      yield candidate
    candidate += 1
    if max is not None and candidate > max:
      break
    if num is not None and num < len(primes):
      break

def is_not_divisible(primes, candidate):
  for prime in primes:
    if candidate % prime == 0:
      return False
  return True
