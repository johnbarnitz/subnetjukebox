from django.shortcuts import render
from .models import Subnet, User
from django.utils import timezone
from django.views import generic
from anytree import Node, RenderTree

# Create your views here.

from django.http import HttpResponse
from ipaddress import IPv4Network, IPv6Network

output=[]


def index(request):
    subnet_list = Subnet.object.order_by('address')
    context =  {
            'subnet_list': subnet_list
    }
    return render(request,'sj/index.html', context)

class IndexView(generic.ListView):
    template_name='sj/index.html'
    context_object_name = 'subnet_list'

    def get_queryset(self):

        return Subnet.objects.all().order_by('address')
class SubnetDetailView(generic.DetailView):
    model = Subnet
    template_name = 'sj/detail.html'

class SubnetTreeView(generic.ListView):
    template_name='sj/treeview.html'
    context_object_name='sitemap'

    def get_queryset(self):
        s = Subnet.objects.all()
        n = []
        for x in s:
            n0 = Node(x)
            n.append(n0)
        for n1 in n:
            for x in s:
                if n1.name == x:
                    for n2 in n:
                        if n2.name == x.parent:
                            n1.parent=n2
        s = []
        for n3 in n:
            if n3.is_root:
                s.append(n3)
        return s[3]

def cidrit(netw, wantlen):
    collect = []
    first=False
    for i in netw.subnets(1):
        if (i.prefixlen<wantlen) and (first==False):
            print("Create CIDR for ", i)
            c = cidrit(i, wantlen)
            for cl in c:
                collect.append(cl)
            first=True
        if (i.prefixlen==wantlen) and (first==False):
            collect.append([i, "Used"])
            first=True
        else:
            collect.append([i, "Unused"])
            print(i)
    return collect

def cidrit2(netw, wantlen):
    print(netw)
    collect = []
    first = False
    subnetobj = Subnet.objects.filter(network_bits=netw.prefixlen, address=str(netw.network_address), status=1)
    if netw.prefixlen==wantlen:
      print(subnetobj, len(subnetobj))
      if len(subnetobj) > 0:
         return None
      else:
         return netw
    for i in netw.subnets(1):
       n = cidrit2(i,wantlen)
       if n:
          print(netw)
          return n, netw
    return None

def removeNestings(l):
   for i in l:
      if type(i) == tuple:
         removeNestings(i)
      else:
         output.append(i)
def flatten(S):
    if S == ():
        return S
    if isinstance(S[0], tuple):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def requestsubnet(request, wantlen, wantvers):
   u = User.objects.all()[0]
   s = Subnet.objects.filter(network_bits=wantlen,version=wantvers, status=0)
   if len(s) > 0:
      text = "<h1>{}</h1>".format(s[0].cidrnotation())
   else:
      s = Subnet.objects.filter(network_bits__lt=wantlen, version=wantvers, status=0)
      if len(s) == 0:
         text = "<h1>No free subnets</h1>"
      else:
         if wantvers == 4:

            netw = IPv4Network(s[0].cidrnotation())

         subnetlist = cidrit2(netw, wantlen)
#         removeNestings(subnetlist)
#         flatsubnetlist=output
         flatsubnetlist = flatten(subnetlist)
         text = "<h1>Subnet is {}</h1>".format(flatsubnetlist[0])
         hostcount = flatsubnetlist[0].num_addresses 
         prevsubnetobj = None

         for  sl in reversed(flatsubnetlist):
#            subnetobj = Subnet(address=str(sl.network_address), create_date=timezone.now(),network_bits=sl.prefixlen, version=4, created_by=u, status=status)   
            status = 0
            try:
                subnetobj = Subnet.objects.get(address=str(sl.network_address), network_bits=sl.prefixlen, version=4, created_by=u, status=status)   
            except Subnet.DoesNotExist:
                ipa = int.from_bytes(sl.network_address.packed, "big")
                subnetobj = Subnet(address=str(sl.network_address), create_date=timezone.now(),network_bits=sl.prefixlen, version=4, created_by=u, status=status,parent=prevparent, intnotation=ipa)
                subnetobj.save()
            prevparent=subnetobj
            subnetobj.availcount = subnetobj.availcount + hostcount 
            if subnetobj.availcount == subnetobj.hostcount():
                subnetobj.status=1
            subnetobj.save()
   return HttpResponse(text)

def hello(request):
   text = """<h1>welcome to my app !</h1>"""
   return HttpResponse(text)
