with open('interpreter.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('content.split(",")', 'self._split_args(content)')
c = c.replace('args.split(",")', 'self._split_args(args)')
with open('interpreter.py', 'w', encoding='utf-8') as f:
    f.write(c)
