from django.forms import widgets
from rest_framework import serializers
from .models import URL

class URLSerializer(serializers.ModelSerializer):
    class Meta:
        model = URL
        fields = ('init_url', 'final_url', 'status', 'title', 'collected_date', 'snapshot_url')

    def create(self, validated_data):
        return URL.objects.create(**validated_data)