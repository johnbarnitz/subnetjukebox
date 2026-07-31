from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Network, SubnetAllocateHandler, TagValue, Tag, LabelValue, Label


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class TagValueSerializer(serializers.ModelSerializer):
    tag = serializers.CharField(source="tag.name")
    class Meta:
        model = TagValue
        fields = ['tag', 'value']

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['name']

class LabelValueSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="label.name")
    class Meta:
        model = LabelValue
        fields = ['label', 'value']


class NetworkSerializer(serializers.ModelSerializer):
    tag = TagValueSerializer(read_only=False, many=True, required=False)
    address = serializers.CharField(source="_address", required=False)
    owner = serializers.ReadOnlyField(source="owner.username")
    class Meta:
        model = Network
        fields = [ "name" , "tag" , "address" , "cidr_available" , "is_subnet" , "supernet" , "ip_version", "owner"]

    def create(self,validated_data):
        """
        Create and return a new 'Network' instance given the validated data
        """
        pass

    def update(self, instance, validated_data):
        """
        Update and return and existing "Network" instance, given the validaed data

        address, cidr, and is_subnet are not modifiable

        """
        instance.name = validated_data.get("name", instance.name)
        instance.tag = validated_data.get("tag", instance.tag)
        instance.save()
        return instance

class UserSerializer(serializers.ModelSerializer):
    networks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Network.objects.all()
    )

    class Meta:
        model = User
        fields = ["id", "username", "networks"]