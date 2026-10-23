from random import choices

from django.contrib.auth.forms import AuthenticationForm,  UsernameField

from sentry_sdk.utils import Auth

from django import forms
from django.forms import ModelForm, formset_factory

from .models import Tag
from .models import TagValue, Label, LabelFieldType, LabelValue

class SubnetEditForm(forms.Form):
    template_name= "webui/subnet-edit-form.html"
    def __init__(self, *args, **kwargs):
        self.labels = kwargs.pop('extra_labels')
        self.subnet_labels = kwargs.pop('extra_subnet_labels')

        super(SubnetEditForm, self).__init__(*args, **kwargs)

        for l,values in self.labels.items():
            default_value =  self.subnet_labels[l.name] if l.name in self.subnet_labels else None
            if l.type == "TF":
                self.fields[f"label_TF_{l.name}"] = forms.CharField(max_length=128, required=False, label=l.name,
                                    widget=forms.TextInput(attrs={"class": "input"}), initial = default_value)
            elif l.type == "DR":
                values.insert(0, ("x", "--- Remove ---"))
                self.fields[f"label_DR_{l.name}"] = forms.ChoiceField(choices=values,required=False, label=l.name,
                                                                          initial=default_value)

class SubnetForm(forms.Form):
    template_name = "webui/subnet-form2.html"
    value = (("4","4"), ("6","6"))
    def __init__(self, *args, **kwargs):
        """ Grants access to the request object so that only members of the current user
        are given as options"""

        self.tags = kwargs.pop('extra_tags')
        self.labels = kwargs.pop('extra_labels')
        super(SubnetForm, self).__init__(*args, **kwargs)
        print(self.tags)
        for t,values in self.tags.items():
            values.insert(0,("x", "--- Select ---"))
#            self.fields[f"tag_{t.name}"] = forms.ChoiceField(choices=values,required=False, label=t.name)
            tag =  forms.ChoiceField(choices=values,required=False, label=t.name)
            tag.group = "tag"
            self.fields[f"tag_{t.name}"] = tag

        for l,values in self.labels.items():
            if l.type == "TF":
#                self.fields[f"label_TF_{l.name}"] = forms.CharField(max_length=128, required=False, label=l.name,  widget=forms.TextInput(attrs={"class": "input"}))
                label = forms.CharField(max_length=128, required=False, label=l.name,  widget=forms.TextInput(attrs={"class": "input"}))
                label.group = "label"
                self.fields[f"label_TF_{l.name}"] = label
            elif l.type == "DR":
                values.insert(0, ("x", "--- Select ---"))
#                self.fields[f"label_DR_{l.name}"] = forms.ChoiceField(choices=values,required=False, label=l.name)
                label = forms.ChoiceField(choices=values,required=False, label=l.name)
                label.group= "label"
                self.fields[f"label_DR_{l.name}"] = label
        print(self.fields)
#        self.fields['members'].queryset = Member.objects.filter(
#            user=self.request.user)
    def subnet_group(self):
        return self.group("subnet")
    def tag_group(self):
        return self.group("tag")
    def label_group(self):
        return self.group("label")
    def group(self, groupname):
        return filter(lambda x: x.group == groupname, self.fields.values())
    def form_valid(self):
        self.send_message()

        # send a meessage


    subnet_your_size = forms.IntegerField(label="Subnet Size", max_value=32, widget=forms.NumberInput(attrs={"class": "input"}))
    subnet_your_size.group = "subnet"
    subnet_ip_version = forms.ChoiceField(label="IP Version", choices= value,widget=forms.Select(attrs={'class': "select select-primary"}))
    subnet_ip_version.group = "subnet"
    subnet_your_network = forms.GenericIPAddressField(label="(Optional) Request a specific Subnet",  required=False,
                                                      widget=forms.TextInput(attrs={"class": "input"}))
    subnet_your_network.group = "subnet"
    subnet_your_name = forms.CharField(label="(Optional) Give the subnet a friendly name", max_length=128, required=False,
                                       widget=forms.TextInput(attrs={"class": "input"}))
    subnet_your_name.group = "subnet"
    subnet_supernet = forms.BooleanField(label="Create a supernet from which subnets are allocated from.", required=False,
                                         widget=forms.CheckboxInput(attrs={"class": "checkbox checkbox-primary" }))
    subnet_supernet.group = "subnet"

#    tv = TagValue.objects.all()
#    value =  ((f"{i.id}", f"{i.tag}-{i.value}") for i in tv)
#    tag = forms.ChoiceField(label="Tags to filter search", choices= value)



#class TagPickerForm(forms.Form):
#    t = Tag.objects.all()
#    v = TagValue.objects.all()

#    if t and v:
#        choices = {"0": "-------",}
#        choices |= zip([y.id for y in t], [y.name for y in t])
#        tag = forms.ChoiceField(choices=choices)
#        choices = {"0": "-------",}
#        choices |= zip([y.id for y in v], [y.value for y in v])
#        value = forms.ChoiceField(choices=choices)

class TagForm(forms.Form):
    name = forms.CharField(label="Name of the tag", max_length=120,  widget=forms.TextInput(attrs={"class": "input"}))

class TagEditForm(forms.Form):
    name = forms.CharField(label="Name of the Tag", max_length=120, required=False,
                           widget=forms.TextInput(attrs={"class": "input myInput", "disabled":"disabled"}))

class TagValueForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=Tag.objects.all(), empty_label="(Nothing)", widget=forms.Select(attrs={'class': "select select-primary"}))
    value = forms.CharField(label="Add a Value to the tag", max_length=128, widget=forms.TextInput(attrs={"class": "input"}))

class TagValueEditForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=Tag.objects.all(), empty_label="(Nothing)", widget = forms.HiddenInput())
    value = forms.CharField(label="Add a Value to the tag", max_length=128, widget=forms.TextInput(attrs={"class": "input"}))

class TagValueAddForm(forms.Form):
    value = forms.CharField(label="Add a Value to the tag", required=False, max_length=128, widget=forms.TextInput(attrs={"class": "input"}))

class LabelValueAddForm(forms.Form):
    value = forms.CharField(label="Add a Value to the label", required=False, max_length=128, widget=forms.TextInput(attrs={"class": "input"}))

class LabelEditForm(forms.Form):
    name = forms.CharField(label="Name of the Label", max_length=120, required=False,
                           widget=forms.TextInput(attrs={"class": "input myInput w-5/6", "disabled":"disabled"}))



TagValueFormSet = formset_factory(TagValueEditForm, extra=1)

#class TagValueForm(forms.Form):
#    t = Tag.objects.all()
#    if t:
#        choices = zip([y.name.lower() for y in t], [y.name for y in t])
#        tag = forms.ChoiceField(choices=choices)
#    else:
#        Tag = forms.ChoiceField(choices=(("0", "None"),))
#    value = forms.CharField(label="Add a Value to the tag", max_length=128)



#class LabelForm(forms.Form):
#    name = forms.CharField(label="Name of the tag", max_length=120)
#    type = forms.ChoiceField(choices=LabelFieldType.choices)


#class LabelValueForm(forms.Form):
#    label = forms.ModelChoiceField(queryset=Label.objects.all())
 #   value = forms.CharField(label="Add a Value to the tag", max_length=128)

class LabelForm(ModelForm):
    class Meta:
        model = Label
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'type': forms.Select(attrs={'class': "select select-primary"})
        }

class LabelValueForm(ModelForm):
    class Meta:
        model = LabelValue
        fields = "__all__"
        widgets = {
            'label': forms.Select(attrs={'class': "select select-primary"}),
            'value': forms.TextInput(attrs={'class': 'input'})
        }

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'input input-primary', 'placeholder': '', 'id': 'hello'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'input input-primary',
            'placeholder': '',
            'id': 'hi',
        }
))

#    t = Label.objects.all()
 #   if t:
  #      choices = zip([y.name.lower() for y in t], [y.name for y in t])
#        tag = forms.ChoiceField(choices=choices)
#    else:
#        Tag = forms.ChoiceField(choices=(("0", "None"),))
#    value = forms.CharField(label="Add a Value to the tag", max_length=128)
