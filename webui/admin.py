from django.contrib import admin

# Register your models here.
from django.contrib import admin


from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from webui.models import Network, Tag, TagValue

class MyAdmin(TreeAdmin):
    form = movenodeform_factory(Network)

admin.site.register(Network, MyAdmin)
admin.site.register(Tag)
admin.site.register(TagValue)
