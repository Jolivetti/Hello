from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("login/verify/", views.verify_otp_view, name="verify_otp"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("force-password-change/", views.force_password_change_view, name="force_password_change"),

    # Self-Service Password Recovery
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="claims/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="claims/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="claims/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="claims/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    # Portals & Dashboards
    path("portal/", views.client_portal, name="client_portal"),
    path("firm-admin/", views.firm_admin_view, name="firm_admin"),
    path("medical-portal/", views.medical_portal_view, name="medical_portal"),
    path("superadmin/", views.superadmin_dashboard_view, name="superadmin_dashboard"),

    # Intake & File Details
    path("case/new/", views.new_case, name="new_case"),
    path("case/<int:case_id>/", views.case_detail, name="case_detail"),
    path("case/<int:case_id>/delete/", views.delete_case, name="delete_case"),
    path("case/<int:case_id>/assign/", views.update_case_assignment, name="update_case_assignment"),
    path("case/<int:case_id>/document/<int:doc_id>/delete/", views.delete_document, name="delete_document"),

    # Passenger Actions
    path("case/<int:case_id>/passenger/add/", views.api_add_passenger, name="api_add_passenger"),

    # Medical Bills & Status Actions
    path("case/<int:case_id>/bill/", views.api_add_bill, name="api_add_bill"),
    path("case/<int:case_id>/bill/<int:bill_id>/edit/", views.edit_bill, name="edit_bill"),
    path("case/<int:case_id>/bill/<int:bill_id>/delete/", views.delete_bill, name="delete_bill"),
    path("case/<int:case_id>/status/", views.api_update_status, name="api_update_status"),
    path("case/<int:case_id>/note/", views.api_add_note, name="api_add_note"),
    path("case/<int:case_id>/settlement/", views.api_save_settlement, name="api_save_settlement"),

    # Message Center & Thread Test Actions
    path("messages/", views.inbox_view, name="inbox"),
    path("messages/unread-count/", views.api_unread_count, name="api_unread_count"),
    path("case/<int:case_id>/message/send/", views.send_case_message, name="send_case_message"),
    path("case/<int:case_id>/message/simulate/", views.api_simulate_incoming, name="api_simulate_incoming"),
    path("case/<int:case_id>/message/mark-unread/", views.api_mark_thread_unread, name="api_mark_thread_unread"),
    path("case/<int:case_id>/message/mark-read/", views.api_mark_thread_read, name="api_mark_thread_read"),
]