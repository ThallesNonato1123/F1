from collections import deque
from itertools import count

for case in count(1):
    t = int(input())
    if t == 0:
        break
    print(f"Scenario #{case}")
    f = dict()
    n_list = [deque() for _ in range(1010)]
    k = deque()
    f = {j: i for i in range(t) for j in input().split()[1:]}
    while True:
        cmd = input()
        if cmd.startswith("S"):
            break
        elif cmd.startswith("E"):
            x = cmd.split()[-1]
            d = f[x]
            if len(n_list[d]) == 0:
                k.append(d)
            n_list[d].append(x)
        else:
            b = k[0]
            print(f"{n_list[k[0]]}")
            n_list[b].popleft()
            if len(n_list[b] == 0):
                k.popleft()
        print()