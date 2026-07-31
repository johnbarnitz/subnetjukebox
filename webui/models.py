from django.db import models
from django.db.models import Exists, OuterRef, Q, Count

# Create your models here.
from django.db import models
from ipaddress import IPv4Network, IPv6Network, collapse_addresses

from treebeard.mp_tree import MP_Node
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter
from pygments import highlight
from .exceptions import NoFreeSpaceAvailable, NoCandidateFound, IPVersionInvalid

class LabelFieldType(models.TextChoices):
    # value, label
    DROPDOWN = 'DR', 'Dropdown'
    TEXTFIELD = 'TF', 'Text Field'



#Labels Do not affect the selection of a Subnet
class Label(models.Model):
    name = models.CharField(max_length=150)
    type = models.CharField(
        max_length=2,
        choices=LabelFieldType.choices,
        default= LabelFieldType.TEXTFIELD,
    )

    def __str__(self):
        return f"{self.name} - {self.type}"


class LabelValue(models.Model):
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name="values")
    value= models.CharField(max_length=150)
    def __str__(self):
        return f"{self.value} - {self.label}"
    def is_used(self):
        return self.Network_set.exists()


class Tag(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class TagValue(models.Model):
    value= models.CharField(max_length=150)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="values")
    def __str__(self):
        return f"{self.value} - {self.tag}"

class Network(MP_Node):
    name = models.CharField(max_length=30)
    tag = models.ManyToManyField(TagValue)
    label = models.ManyToManyField(LabelValue)
    _address = models.CharField(max_length=30)
    cidr_available = models.IntegerField()
    is_subnet = models.BooleanField(default=False)
    supernet = models.BooleanField(default=False)
    ip_version = models.IntegerField()

    owner = models.ForeignKey(
        "auth.User", related_name="networks", on_delete=models.CASCADE
    )
    node_order_by = ['name']

    def __str__(self):
        return 'Network: {}'.format(self.name)
    def simple_delete(self):
        super(Network, self).delete()

    def get_sibling(self):
        sibs = [x for x in self.get_siblings() if x != self]
        if sibs:
            return sibs[0]
        else:
            return None

    def delete(self):
        print(f" Deleting {self.address}")
        sibling = self.get_sibling()
        print(f"Sibling {sibling}")
        if sibling and sibling.is_leaf() and sibling.cidr_available > 0:
            self.get_parent(True).delete()
        else:
            self.cidr_available = self.address.prefixlen
            if not self.is_root():
                self.name = f"Free-{self.address}"
            self.save()
            for i in self.get_children():
                print(f" Sub Deleting {i.address}")
                i.simple_delete()
            print("Count ", self.get_children_count())


    @property
    def address(self):
        if self.ip_version == 4:
            return IPv4Network(self._address)
        elif self.ip_version == 6:
            return IPv6Network(self._address)
        raise IPVersionInvalid(f"IP version {self.ip_version} not supported", 105)
    @address.setter
    def address(self, new_value):
        self._address = str(new_value)

class SubnetAllocateHandler:
    def __init__(self, cidr_available, name, ip_version, tag = [],label = [], is_subnet=False, address=None, supernet=False, owner = None):
        print ("alloctag", tag)
        self.size = cidr_available
        self.address = IPv4Network(address) if address else None
        self.name = name
        self.cidr_available = 0
        self.is_subnet = is_subnet
        self.ip_version = int(ip_version)
        self.tags = self.get_tagvalue_from_serializer(tag)
        self.labels = label
        self.tag_count = len(self.tags) if self.tags else 0
        self.q_objects = Q( pk__in = [t.pk for t in self.tags]) if self.tags else []
        self.supernet = supernet

        self.owner = owner
    def  process(self):
        candidate = None
        print("Tags", self.tags, "supernet", self.supernet)
        if self.tags and not self.supernet:
            tagfilter = TagValue.objects.filter(Q(network=OuterRef("pk")), self.q_objects)
            nottagfilter = TagValue.objects.filter(Q(network=OuterRef("pk")), ~(self.q_objects))
            s = Network.objects.filter(cidr_available__lte=self.size, cidr_available__gt = 0,  is_subnet=False, numchild=0, ip_version = self.ip_version).order_by(
                '-cidr_available').filter(Exists(tagfilter)).annotate(tag_count=Count('tag')).filter(tag_count=self.tag_count).filter(~Exists(nottagfilter))
        else:
            s = Network.objects.filter(cidr_available__lte=self.size, cidr_available__gt = 0,  is_subnet=False, numchild=0,
                                       ip_version = self.ip_version, tag=None).order_by('-cidr_available')
        if not s:
            if self.supernet and self.address:
                pass
            else:
                raise NoCandidateFound("There is not enough free IP Space to handle this request", 101)


        if self.address:
            for item in s:
                if item.address.supernet_of(self.address) or item.address == self.address :
                    candidate = item
            if not candidate:
                if self.supernet:
                    candidate = self.add_root()
                else:
                    raise NoCandidateFound("There are no networks to allocate that subnet from", 102)
        else:
            candidate = s[0]
        print ("Candidate", candidate)
        len = candidate.address.prefixlen
        while self.size > len:
            subnet_list = list(candidate.address.subnets())
            for i in subnet_list:
                identifier = f"Free-{i}"
                child = candidate.add_child(name=identifier, address = i,ip_version = self.ip_version, cidr_available = i.prefixlen,
                                    supernet=False, owner = self.owner)
                if not self.supernet:
                    for t in self.tags:
                        child.tag.add(t)
                    child.save()

            self.size -=1
            if self.address:
                for item in candidate.get_children():
                    if item.address.supernet_of(self.address) or item.address == self.address :
                        candidate = item
            else:
                candidate = candidate.get_first_child()

        if self.address and not candidate.address == self.address:
            candidate = candidate.get_next_sibling() or candidate.get_prev_sibling
            if candidate.address != self.address:
                raise NoCandidateFound("Unable to find a subnet to match request", 103)

        candidate.name = self.name if self.name else f"Subnet-{candidate.address}"
        if self.supernet:
            candidate.supernet=True
            for t in self.tags:
                candidate.tag.add(t)
        else:
            candidate.is_subnet = True
        for l in self.labels:
            candidate.label.add(l)
        candidate.save()
        return candidate

    def add_root(self):
        n = Network.add_root(name=self.name, address = self.address,ip_version = self.ip_version,
                         cidr_available = self.size,  supernet=True,owner = self.owner)
        for t in self.tags:
            n.tag.add(t)
        n.save()
        return n

    def get_tagvalue_from_serializer(self, tv):
        array = []
        for i in tv:
            if isinstance(i, TagValue):
                array.append(i)
            else:
                t = Tag.objects.filter(name=i['tag'])
                tv = TagValue.objects.filter(tag__in=t, value=i['value'])
                array.append(tv[0])
        return array

    def add_supernet(self):
        r = Network.get_root()
        sn =r.add_child()
        sn.address = self.address
        sn.name = self.name
        sn.supernet = True
        sn.tag = self.tag
        sn.ip_version = self.ip_version
        sn.save()
        return sn
def get_annotated_list():
    return get_filtered_annotated_list_qs(Network.objects.filter(Q(supernet=True)| Q(is_subnet=True)).order_by('path'))

def get_filtered_annotated_list_qs(qs):
    """
    Efficiently generates an annotated list from a queryset.

    The queryset MUST be ordered by path, otherwise it will yield
    incorrect results. The queryset must also represent the entirety of
    a branch of a tree: excluded objects will not be fetched and will
    result in gaps in the tree.
    """
    result, info = [], {}
    start_depth, prev_depth = (None, None)
    prevnode = None
    stack = []
    depth = 0
    for node in qs:
        depth +=1
        if start_depth is None:
            start_depth = depth
        if prevnode and not node.is_descendant_of(prevnode):
            s = stack.pop() if stack else None
            while s:
                if node.is_descendant_of(s):
                    stack.append(s)
                    break
                else:
                    depth = depth - 1
                    s = stack.pop() if stack else None
        open = depth and (prev_depth is None or depth > prev_depth)
        if prev_depth is not None and depth < prev_depth:
            info["close"] = list(range(0, prev_depth - depth))
        info = {"open": open, "close": [], "level": depth - start_depth}
        result.append(
            (
                node,
                info,
            )
        )

        prevnode = node
        prev_depth = depth
        stack.append(node)

    if start_depth and start_depth > 0:
        info["close"] = list(range(0, prev_depth - start_depth + 1))
    return result


def get_annotated_list_qs(qs):
    """
    Efficiently generates an annotated list from a queryset.

    The queryset MUST be ordered by path, otherwise it will yield
    incorrect results. The queryset must also represent the entirety of
    a branch of a tree: excluded objects will not be fetched and will
    result in gaps in the tree.
    """
    result, info = [], {}
    start_depth, prev_depth = (None, None)
    for node in qs:
        depth = node.get_depth()
        if start_depth is None:
            start_depth = depth
        open = depth and (prev_depth is None or depth > prev_depth)
        if prev_depth is not None and depth < prev_depth:
            info["close"] = list(range(0, prev_depth - depth))
        info = {"open": open, "close": [], "level": depth - start_depth}
        result.append(
            (
                node,
                info,
            )
        )
        prev_depth = depth
    if start_depth and start_depth > 0:
        info["close"] = list(range(0, prev_depth - start_depth + 1))
    return result

def print_abridged_tree_to_console():
    prevnode = None
    stack = []
    depth = 0
    for node in get_annotated_list():
        depth = depth + 1
        if prevnode and not node.is_descendant_of(prevnode):
            s = stack.pop() if stack else None
            while s:
                if node.is_descendant_of(s):
                    stack.append(s)
                    break
                else:
                    depth = depth - 1
                    s = stack.pop()
        indent = '    ' * (depth - 1) if depth > 0 else ''
        print(f"{indent} - {node.name} ({node.address})")
        prevnode = node
        stack.append(node)
