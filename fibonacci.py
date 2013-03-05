def fibonacci(num=None, max=None):
  fibs = []
  for fib in xfibonacci(num=num, max=max):
    fibs.append(fib)
  return fibs

def xfibonacci(num=None, max=None):
  for fib in xall_fibonacci():
    if max is not None and fib > max:
      break
    if num is not None:
      num -= 1
      if num < 0:
        break
    yield fib

def xall_fibonacci():
  prev = 0
  cur = 1
  while True:
    yield cur
    cur = prev + cur
    prev = cur - prev
