from rest_framework import serializers
from .models import Inquiry


class InquirySerializer(serializers.ModelSerializer):
    """Used by the public contact form."""

    # Honeypot field — kept out of the visible form via CSS, so only bots
    # fill it in. Not a model field; stripped out in the view before save.
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Inquiry
        fields = ['id', 'name', 'email', 'phone', 'company', 'service', 'message', 'website']


class InquiryAdminSerializer(serializers.ModelSerializer):
    """Full serializer for admin dashboard — includes status and timestamps."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Inquiry
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
