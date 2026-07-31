from collections import defaultdict
from ipaddress import collapse_addresses
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as django_auth_views

from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView, TemplateView, FormView, ListView, DeleteView
from rest_framework.parsers import JSONParser


from .models import Network, SubnetAllocateHandler, TagValue, Tag, get_annotated_list, Label, LabelValue, LabelFieldType
from django.http import Http404, HttpResponseBadRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import NetworkSerializer, UserSerializer, LabelValueSerializer
from django.forms import formset_factory
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from rest_framework.generics import ListAPIView, RetrieveAPIView

# Create your views here.

from .permissions import IsOwnerOrReadOnly
from django.http import HttpResponse, HttpResponseRedirect
from .forms import SubnetForm, TagForm, TagValueForm, LabelValueForm, LabelForm, SubnetEditForm, TagValueFormSet, \
    TagValueAddForm, LabelValueAddForm, LabelEditForm, TagEditForm, UserLoginForm
from .exceptions import IPVersionInvalid, RestIPVersionInvalid, RestNoFreeSpaceAvailable, RestIPAddressInvalid, \
    NoFreeSpaceAvailable, NoFreeSpaceAvailable, NoCandidateFound, RestGenericAPIException
from django.db.models import Q, ProtectedError, Model
from django.contrib.auth import authenticate, login

@login_required
def index(request):
    return HttpResponse("Hello, world. You're at the SubnetJukebox index.")

class HomeView( TemplateView):
    template_name = 'webui/home.html'

class LoginView(django_auth_views.LoginView):
    template_name = 'webui/login.html'
    authentication_form = UserLoginForm
    extra_context = None
    redirect_authenticated_user = True


@login_required
def tree(request):
    annotated_list = Network.get_annotated_list()
    template_name = 'webui/index.html'
    context = {
        'annotated_list': annotated_list
    }
    return render(request, template_name,context)

@login_required
def filtered_tree(request):
    annotated_list = get_annotated_list()
    template_name = 'webui/index.html'
    context = {
        'annotated_list': annotated_list
    }
    return render(request, template_name,context)

def find_a_new_subnet(size, address, ip_version, name, tvqueryset, lvqueryset, user):
    if not name:
        name =  str(address) #form.cleaned_data['your_name']
    print("TagValue", tvqueryset)
    print("LabelValue", lvqueryset)

    try:
        s = SubnetAllocateHandler(size[0], name, ip_version, tvqueryset,lvqueryset, address =  address, owner=user).process()
    except  NoFreeSpaceAvailable as i:
        raise RestNoFreeSpaceAvailable()
    except   NoCandidateFound as i:
        raise RestNoFreeSpaceAvailable()
    except IPVersionInvalid as i:
        raise RestIPVersionInvalid()
    if s:
        return s.address
    else:
        return None
@login_required
def success_view(request):
    # Get the referring URL, with a default fallback (e.g., '/') if not present
    referer_url = request.META.get('HTTP_REFERER', '/')

    # Your view logic goes here
    # ...

    return render(request, 'webui/generic-success.html', {'referer': referer_url})

def mark_used(node, name="Used"):
    node.name = name
    node.cidr_available = 0
    node.save()

def process_labels(labels):
    id_values = []
    for label in labels:
        if label.cleaned_data.get('label').type == "TF":
            saved = label.save()
            idval = saved.id
        else:
            idval  = int(label.cleaned_data["value"])
        id_values.append(idval)

    return id_values

def add_label_from_text(labels):
    ids = []
    for l, v in labels.items():
        l = l.replace("label_TF_", "")
        lbl = Label.objects.filter(name=l)
        lv = LabelValue(label=lbl[0], value=v)
        lv.save()
        ids.append(lv.pk)
    return ids

class SubnetListView(LoginRequiredMixin, ListView):
     template_name = "webui/subnet-list.html"
     context_object_name = 'object_list'

     def get_queryset(self):
         criterion1 = Q(is_subnet=True)
         criterion2 = Q(supernet=True)
         return Network.objects.filter(criterion1 | criterion2)


class SubnetDeleteView(LoginRequiredMixin, DeleteView):
    # specify the model you want to use
    model = Network

    # can specify success url
    # url to redirect after successfully
    # deleting object
    success_url = "webui/success.html/"

    template_name = "webui/subnet_confirm_delete.html"

def test(request):
    return render(request, "webui/test.html")


@login_required
def get_subnet(request):
    # if this is a POST request we need to process the form data
    labels_dict = defaultdict(list)
    tags_dict = defaultdict(list)
    for i in Label.objects.all():
        if i.type == "TF":
            labels_dict[i].append((0, "TextField"))
    for i in LabelValue.objects.all():
        m = model_to_dict(i)
        l = Label.objects.get(id=m['label'])
        if l.type == "DR":
            labels_dict[l].append((m['id'], m['value']))

    for i in TagValue.objects.all():
        m = model_to_dict(i)
        tags_dict[Tag.objects.get(id=m['tag'])].append((m['id'], m['value']))


    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        print ("POST ", request.POST, " END POST ")
        form = SubnetForm(request.POST, prefix="subnet",extra_tags=tags_dict, extra_labels=labels_dict)
        print(form)
        # check whether it's valid:
        print( f"{form.is_valid()}")
        if form.is_valid() :
            print (form.cleaned_data)
            size = form.cleaned_data['subnet_your_size'],
            name = form.cleaned_data.get('subnet_your_name'),
            address = form.cleaned_data.get('subnet_your_network')
            ip_version = form.cleaned_data['subnet_ip_version']
            label_values = [form.cleaned_data[f] for f in form.cleaned_data.keys() if f.startswith("label_DR") and form.cleaned_data[f] != 'x' ]
            label_input = {f:form.cleaned_data[f] for f in form.cleaned_data.keys() if f.startswith("label_TF") and form.cleaned_data[f]}
            label_values.extend(add_label_from_text(label_input))

            tag_values = [form.cleaned_data[f] for f in form.cleaned_data.keys() if f.startswith("tag") and form.cleaned_data[f] != 'x']
            print ("LV", label_values)
            print ("TV", tag_values)
            tvqueryset = []
            lvqueryset = []
            if label_values:
                lvqueryset = LabelValue.objects.filter(pk__in=label_values)
            if tag_values:
                tvqueryset = TagValue.objects.filter(pk__in=tag_values)
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            print("Formset ", form, "End Formset")
            print("User ", request.user)
            try:
                allocated = find_a_new_subnet(size, address, ip_version, name, tvqueryset, lvqueryset, request.user)
            except Exception as e:
                return render(request, "webui/no-success.html", {"size":size, "tags": tvqueryset, "error": e})

            if allocated:
                return render(request, "webui/success.html", {"subnet": allocated})
            else:
                return render(request, "webui/no-success.html", {"size":size, "tags": tvqueryset, "error": "No Network Allocated"})
    # if a GET (or any other method) we'll create a blank form


    form = SubnetForm( prefix='subnet', extra_tags=tags_dict, extra_labels=labels_dict)
    return render(request, "webui/subnet2.html", {"form": form})

@login_required
def edit_subnet(request, pk):
    try:
        s = Network.objects.get(id=pk)
    except Network.DoesNotExist:
        raise Http404("Subnet does not exist")
    labels_subnet = {x.label.name: x.value for x in s.label.all()}
    labels_dict = defaultdict(list)
    for i in LabelValue.objects.all():
        m = model_to_dict(i)
        labels_dict[Label.objects.get(id=m['label'])].append((m['id'], m['value']))

    if request.method == "POST":
        form = SubnetEditForm(request.POST, extra_labels=labels_dict, extra_subnet_labels=labels_subnet)
        print(form.errors, form.is_valid())
        if form.is_valid() :
            print (form.cleaned_data)
            s = edit_subnet_post(form.cleaned_data, s)

    labels_subnet = {x.label.name: x.value for x in s.label.all()}
    form = SubnetEditForm(extra_labels=labels_dict, extra_subnet_labels=labels_subnet)
    return render(request, "webui/subnet-detail.html", {"item": s, "form":form})

def add_one_label_from_text(k, v):
    k = k.replace("label_TF_", "")
    lbl = Label.objects.filter(name=k)
    lv = LabelValue(label=lbl[0], value=v)
    lv.save()
    return lv.pk

def edit_subnet_post(post, n):
    for k, v in post.items():
        match= re.search(r"label_(..)_", k)
        type = match.group(1)
        key = re.sub(r"label_.._","", k)
        found = False
        for i in n.label.all():
            if key == i.label.name:
                if  v != i.value:
                    if v == '' or ( type == "DR" and v == 'x'):
                        n.label.remove(i)
                        n.save()
                    else:
                        i.value = v
                        i.save()
                found=True
        if not found:
            if type == "TF" and v:
                newlabel = add_one_label_from_text(k,v)
                n.label.add(newlabel)
                n.save()
            elif type == "DR" and v  != 'x' :
                lvitem = LabelValue.objects.get(pk = int(v))
                print (lvitem)

                n.label.add(lvitem)
                n.save()
    return n


class TagFormView(FormView):
    template_name = "webui/tag_form.html"
    form_class = TagForm
    success_url = "/webui/success"

class TagListView(ListView):
    template_name = "webui/tag-list.html"
    context_object_name = 'object_list'
    model = Tag

class LabelListView(ListView):
    template_name = "webui/label-list.html"
    context_object_name = 'object_list'
    model = Label

class LabelValueListView(ListView):
    template_name = "webui/labelvalue-list.html"
    context_object_name = 'object_list'
    model = LabelValue


@login_required
def tag_delete(request, pk):
    t =  get_object_or_404(Tag, pk=pk)
    if Network.objects.filter(tag__in=t.values.all()).exists():
        return  HttpResponseBadRequest("Cannot delete: Tag has associated networks")
    t.delete()
    return render(request, 'webui/generic-success.html')

@login_required
def label_delete(request, pk):
    l = get_object_or_404(Label, pk=pk)
    if Network.objects.filter(label__in=l.values.all()).exists():
        return HttpResponseBadRequest("Cannot delete: Label has associated networks")
    l.delete()
    return render(request, 'webui/generic-success.html')

@login_required
def tag_value_delete(request, pk):
    t =  get_object_or_404(TagValue, pk=pk)
    if Network.objects.filter(tag=t).exists():
        return  HttpResponseBadRequest("Cannot delete: Tag Value has associated networks")
    t.delete()
    return render(request, 'success.html')

@login_required
def label_value_delete(request, pk):
    l = get_object_or_404(LabelValue, pk=pk)
    if Network.objects.filter(label=l).exists():
        return HttpResponseBadRequest("Cannot delete: Label Value has associated networks")
    l.delete()
    return render(request, 'success.html')

# todo/views.py

@login_required
def tag_value_edit(request, pk):
    try:
        t = Tag.objects.get(id=pk)
    except Tag.DoesNotExist:
        raise Http404("Tag does not exist")

    tag_initial = [ {'value': x.value} for x in TagValue.objects.filter(tag=t)]

    extra = 1 if not tag_initial else 0
    TagValueEditFormSet = formset_factory(TagValueAddForm, extra=extra)
    if request.method == 'POST':
        formset = TagValueEditFormSet( request.POST, initial= tag_initial)
        form = TagForm(  request.POST, prefix='tag')
        print(formset)
        print(formset.is_valid())
        if formset.is_valid() :
            print(formset.cleaned_data)
            alltv = [tg.pk for tg in TagValue.objects.filter(tag=t)]
            for form in formset.cleaned_data:
                print("form", form)
                tagobjects = TagValue.objects.filter(tag=t, value=form['value'])
                if not tagobjects:
                    tv = TagValue(tag=t, value=form['value'])
                    tv.save()
                else:
                    [alltv.remove(p.id) for p in TagValue.objects.filter(tag=t, value=form['value'])]
            for i in alltv:
                tv = TagValue.objects.get(pk=i)
                tv.delete()
    else:
         formset = TagValueEditFormSet( initial=tag_initial)
         form = TagEditForm(request.POST, prefix='tag')
            # if form doesnt exists:
            #    add it
            # else:
            #     mark it
            # if there are any unmarked:
            #     removed them
    return render(request, 'webui/tag_value_edit.html', context={'formset': formset, 'tag_name': t, 'tag_form':form})

@login_required
def tag_value_add(request):
    TagValueAddFormSet = formset_factory(TagValueAddForm, extra=1)
    if request.method == 'POST':
        formset = TagValueAddFormSet(request.POST, prefix='formset_prefix')
        form = TagForm(request.POST,  prefix='tag')

        if formset.is_valid() and form.is_valid():
            tag = Tag(name=form.cleaned_data['name'])
            tag.save()
            # Handle formset data
            for form in formset.cleaned_data:
                if 'value' in form:
                    t = TagValue(tag=tag, value=form['value'])
                    t.save()
            return render(request, "webui/success.html", {"subnet": tag})
    else:
        formset = TagValueAddFormSet( prefix='formset_prefix')
        form = TagForm( prefix='tag')

    return render(request, 'webui/tag_value_create.html', {'formset': formset, 'tagform': form})

@login_required
def label_value_edit(request, pk):
    try:
        t = Label.objects.get(id=pk)
    except Label.DoesNotExist:
        raise Http404("Label does not exist")
    type= None

    label_initial = [ {'value': x.value} for x in LabelValue.objects.filter(label=t)]

    extra = 1 if not label_initial else 0
    LabelValueEditFormSet = formset_factory(LabelValueAddForm, extra=extra)
    if request.method == 'POST':
        formset = LabelValueEditFormSet( request.POST,prefix='formset_prefix', initial= label_initial)
        labelform = LabelEditForm(request.POST, prefix='label'  )
        print(formset)
        print(formset.is_valid())
        if formset.is_valid() and labelform.is_valid():
            print(formset.cleaned_data)
            if 'name' in labelform.cleaned_data  and labelform.cleaned_data['name'] and  t.name != labelform.cleaned_data['name']:
                t.name= labelform.cleaned_data['name']
                t.save()
            alltv = [tg.pk for tg in LabelValue.objects.filter(label=t)]
            for form in formset.cleaned_data:
                print("form", form)
                labelobjects = LabelValue.objects.filter(label=t, value=form['value'])
                if not labelobjects:
                    tv = LabelValue(label=t, value=form['value'])
                    tv.save()
                else:
                    [alltv.remove(p.id) for p in LabelValue.objects.filter(label=t, value=form['value'])]
            for i in alltv:
                tv = LabelValue.objects.get(pk=i)
                tv.delete()
    else:
        labelform = LabelEditForm( prefix='label', initial={"name": t.name})
        formset = LabelValueEditFormSet( prefix='formset_prefix',  initial=label_initial)

            # if form doesnt exists:
            #    add it
            # else:
            #     mark it
            # if there are any unmarked:
            #     removed them
    for i in LabelFieldType.choices:
        if i[0] == t.type:
            type = i[1]
    if t.type == "TF":
        formset = None

    return render(request, 'webui/label_value_edit.html', context={'formset': formset, 'label_form': labelform, 'label_type': type})

@login_required
def label_value_add(request):
    LabelValueAddFormSet = formset_factory(LabelValueAddForm, extra=1)
    if request.method == 'POST':
        formset = LabelValueAddFormSet(request.POST, prefix='formset_prefix')
        form = LabelForm(request.POST,  prefix='label')

        if formset.is_valid() and form.is_valid():
            label = Label(name=form.cleaned_data['name'], type = form.cleaned_data['type'])
            label.save()
            # Handle formset data
            for form in formset.cleaned_data:
                if 'value' in form:
                    t = LabelValue(label=label, value=form['value'])
                    t.save()
            return render(request, "webui/success.html", {"subnet": label})
    else:
        formset = LabelValueAddFormSet( prefix='formset_prefix')
        form = LabelForm( prefix='label')

    return render(request, 'webui/label_value_create.html', {'formset': formset, 'labelform': form})

class RootNode(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def post(self, request, format=None):

        request_serializer = NetworkSerializer(data=request.data)
        if request_serializer.is_valid():

            print("Serializer", request_serializer.validated_data)
            n = SubnetAllocateHandler( owner=self.request.user, **request_serializer.data).add_root()
            serializer = NetworkSerializer(n)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class NetworkList(APIView):
    parser_classes = [JSONParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get(self, request, format=None):
        network = Network.objects.all()
        serializer = NetworkSerializer(network, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        request_serializer = NetworkSerializer(data=request.data)
        if request_serializer.is_valid():
            print ("Validated", request_serializer.validated_data)
            try:
                n = SubnetAllocateHandler(owner=self.request.user,**request.data).process()
            except  NoFreeSpaceAvailable as i:
                raise RestNoFreeSpaceAvailable()
            except   NoCandidateFound as i:
                raise RestNoFreeSpaceAvailable()
            except IPVersionInvalid as i:
                raise RestIPVersionInvalid()
            except  Exception as e:
                raise RestGenericAPIException(e, 500)

            serializer = NetworkSerializer(n)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class NetworkDetail(APIView):
    """
    Retrieve, update or delete a Network instance
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_object(self,pk):
        try:
            return Network.objects.get(id=pk)
        except Network.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        network = self.get_object(pk)
        serializer = NetworkSerializer(network)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        network = self.get_object(pk)
        serializer = NetworkSerializer(network, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        network = self.get_object(pk)
        network.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TagDetail(APIView):
    """
    Retrieve, update or delete a tag instance.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tag = self.get_object(pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        tag = self.get_object(pk)
        serializer = TagSerializer(tag, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        tag = self.get_object(pk)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagValueDetail(APIView):
    """
    Retrieve, update or delete a tagvalue instance.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_object(self, pk):
        try:
            return TagValue.objects.get(pk=pk)
        except TagValue.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tagvalue = self.get_object(pk)
        serializer = TagValueSerializer(tagvalue)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = TagValueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        tagvalue = self.get_object(pk)
        serializer = TagValueSerializer(tagvalue, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        tagvalue = self.get_object(pk)
        tagvalue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LabelDetail(APIView):
    """
    Retrieve, update or delete a label instance.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_object(self, pk):
        try:
            return Label.objects.get(pk=pk)
        except Label.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        lebel = self.get_object(pk)
        serializer = LabelSerializer(label)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = LabelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        label = self.get_object(pk)
        serializer = LabelSerializer(label, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        label = self.get_object(pk)
        label.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    class LabelValueDetail(APIView):
        """
        Retrieve, update or delete a LabelValue instance.
        """
        permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

        def get_object(self, pk):
            try:
                return LabelValue.objects.get(pk=pk)
            except LabelValue.DoesNotExist:
                raise Http404

        def get(self, request, pk, format=None):
            labelvalue = self.get_object(pk)
            serializer = LabelValueSerializer(labelvalue)
            return Response(serializer.data)

        def post(self, request, format=None):
            serializer = LabelValueSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        def put(self, request, pk, format=None):
            labelvalue = self.get_object(pk)
            serializer = LabelValueSerializer(labelvalue, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        def delete(self, request, pk, format=None):
            labelvalue = self.get_object(pk)
            labelvalue.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


def load_tags(request):
    tag_id = request.GET.get('tag')
    if tag_id:
        tags = TagValue.objects.filter(tag__id=tag_id).order_by('tag')
    else:
        tags = Tag.objects.all().order_by('name')
    return render(request, 'webui/tag_dropdown_list_options.html', {'tags': tags})

def print_tree_to_console():
    for node in Network.objects.order_by('path'):
            indent = '    ' * (node.depth -1) if node.depth > 0 else ''
            print(f"{indent} - {node.name} ({node.address})")

def print_tree_to_console():
    for node in Network.objects.order_by('path'):
            indent = '    ' * (node.depth -1) if node.depth > 0 else ''
            print(f"{indent} - {node.name} ({node.address})")

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


class UserList(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer