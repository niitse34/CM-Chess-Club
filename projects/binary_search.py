def bs(a:list,t:int,l:int,r:int):
    if l-r == 0:
        return l
    mid = (l + r) // 2
    if a[mid] == t:
        return mid
    if a[mid] > t:
        return bs(a,t,l,mid-1)
    if a[mid] < t:
        return bs(a,t,mid+1,r)
    
print(bs([1,2,3,4,5,7],3,1,6))