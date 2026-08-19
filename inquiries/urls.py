from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import InquiryCreateView, InquiryListView, InquiryDetailView, InquiryStatsView

urlpatterns = [
    # Public — contact form submission
    path('contact/',          InquiryCreateView.as_view(),  name='inquiry_create'),

    # Admin — protected (requires JWT + is_staff=True)
    path('admin/token/',      TokenObtainPairView.as_view(), name='token_obtain'),
    path('admin/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/inquiries/',  InquiryListView.as_view(),    name='inquiry_list'),
    path('admin/inquiries/<int:pk>/', InquiryDetailView.as_view(), name='inquiry_detail'),
    path('admin/stats/',      InquiryStatsView.as_view(),   name='inquiry_stats'),
]
