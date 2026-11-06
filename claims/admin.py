from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Client,
    Case,
    CaseNote,
    MedicalBill,
    Settlement,
    CaseDocument,
    Passenger,
    CaseMessage,
    DeletedCaseLog,
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone', 'must_change_password')}),
    )

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'drivers_license', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'client', 'status', 'insurance_carrier', 'assigned_attorney', 'assigned_case_manager', 'created_at')
    list_filter = ('status', 'assigned_attorney', 'assigned_case_manager')
    search_fields = ('case_number', 'police_report_number', 'client__first_name', 'client__last_name', 'insurance_carrier')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('name', 'case', 'date_of_birth', 'is_minor', 'linked_case', 'created_at')
    list_filter = ('is_minor', 'is_injured')

@admin.register(MedicalBill)
class MedicalBillAdmin(admin.ModelAdmin):
    list_display = ('case', 'provider', 'amount', 'reduced_amount', 'received', 'created_at')
    list_filter = ('received',)

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('case', 'gross_settlement', 'attorney_fee_percent', 'litigation_costs', 'final_client_net', 'updated_at')

@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ('case', 'author', 'created_at')

@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('case', 'title', 'document_type', 'uploaded_by', 'uploaded_at')

@admin.register(CaseMessage)
class CaseMessageAdmin(admin.ModelAdmin):
    list_display = ('case', 'sender', 'created_at', 'is_read')

@admin.register(DeletedCaseLog)
class DeletedCaseLogAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'client_name', 'deleted_by', 'reason', 'deleted_at')
    search_fields = ('case_number', 'client_name', 'reason')
    readonly_fields = ('case_number', 'client_name', 'deleted_by', 'reason', 'summary', 'deleted_at')