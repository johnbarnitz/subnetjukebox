from django.db import models

# Create your models here.


class User(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)


class Subnet(models.Model):
    address = models.GenericIPAddressField()
    create_date = models.DateTimeField('date created')
    network_bits = models.IntegerField()
    version = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField()
    availcount = models.IntegerField(default=0)
    intnotation = models.IntegerField()
    parent = models.ForeignKey('self',null=True,blank=True, on_delete=models.SET_NULL)
    def cidrnotation(self):
        return self.address + '/' + str(self.network_bits)
    def __str__(self):
        return self.cidrnotation()
    def hostcount(self):
        return 2 ** (32-self.network_bits)
