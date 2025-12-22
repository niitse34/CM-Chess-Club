def oof(s,k):
    d = {}
    for c in s:
        d[c] = d.get(c,0) + 1
        for c,t in d.items():
            if t < k:
                split = s.split(c)
                be = [s for s in split if len(s) >= k]
            ax = [len(x) for x in be]
            if not ax:
                return 0
            return max(ax)
            
print(oof("ababaaaaaaaaaaabbb",8))