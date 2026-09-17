from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from .models import Inquiry
from .serializers import InquirySerializer, InquiryAdminSerializer


def healthz(request):
    """Trivial liveness endpoint — used by the keep-alive ping to stop the
    free-tier instance from idling out and cold-starting on real visitors."""
    return JsonResponse({'status': 'ok'})


class InquiryCreateView(generics.CreateAPIView):
    """Public endpoint — clients submit inquiries here."""
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [AllowAny]
    throttle_scope = 'contact'

    def perform_create(self, serializer):
        # Honeypot: a real browser never fills this hidden field in, so any
        # non-empty value means a bot filled the form out. Pretend to
        # succeed (so the bot doesn't adapt) but don't save or email.
        if serializer.validated_data.pop('website', ''):
            self._honeypot_tripped = True
            return
        self._honeypot_tripped = False
        inquiry = serializer.save()
        self._send_notification_email(inquiry)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if getattr(self, '_honeypot_tripped', False):
            # Report success without leaking that it was silently dropped.
            return Response({'id': None}, status=status.HTTP_201_CREATED)
        return response

    def _send_notification_email(self, inquiry):
        subject = f"🔔 New Inquiry: {inquiry.name} — {inquiry.service or 'General'}"
        message = (
            f"NEW CLIENT INQUIRY — Praitunova Infotech\n"
            f"{'='*55}\n"
            f"Name    : {inquiry.name}\n"
            f"Email   : {inquiry.email}\n"
            f"Phone   : {inquiry.phone or 'Not provided'}\n"
            f"Company : {inquiry.company or 'Not provided'}\n"
            f"Service : {inquiry.service or 'Not specified'}\n"
            f"Status  : {inquiry.get_status_display()}\n"
            f"{'='*55}\n\n"
            f"Message:\n{inquiry.message}\n\n"
            f"{'='*55}\n"
            f"Submitted: {inquiry.created_at.strftime('%d %b %Y, %I:%M %p UTC')}\n"
            f"Admin: {settings.SITE_URL}/admin/inquiries/inquiry/{inquiry.id}/change/\n"
        )
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Email send failed: {e}")


class InquiryListView(generics.ListAPIView):
    """Protected admin endpoint — lists all inquiries (paginated)."""
    queryset = Inquiry.objects.all().order_by('-created_at')
    serializer_class = InquiryAdminSerializer
    permission_classes = [IsAdminUser]


class InquiryDetailView(generics.RetrieveUpdateAPIView):
    """Protected admin endpoint — retrieve or update an inquiry status."""
    queryset = Inquiry.objects.all()
    serializer_class = InquiryAdminSerializer
    permission_classes = [IsAdminUser]


class InquiryStatsView(generics.GenericAPIView):
    """Protected admin endpoint — dashboard stats."""
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        qs = Inquiry.objects.all()
        stats = {
            'total': qs.count(),
            'new': qs.filter(status='NEW').count(),
            'contacted': qs.filter(status='CONTACTED').count(),
            'resolved': qs.filter(status='RESOLVED').count(),
            'by_service': list(
                qs.values('service').annotate(count=Count('id')).order_by('-count')[:8]
            ),
        }
        return Response(stats)
