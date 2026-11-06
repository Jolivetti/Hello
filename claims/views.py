import random
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Case,
    CaseDocument,
    CaseMessage,
    CaseNote,
    Client,
    DeletedCaseLog,
    EmailTemplate,
    LawFirm,
    MedicalBill,
    MedicalProviderFacility,
    MedicalTreatmentRecord,
    Passenger,
    Settlement,
    User,
)


def login_view(request):
    """Allows signing in with email/username. Dispatches 6-digit OTP and supports modal AJAX."""
    if request.method == "POST":
        action = request.POST.get("action")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        # Handle modal OTP verification
        if action == "verify_otp":
            pre_user_id = request.session.get("pre_auth_user_id")
            correct_otp = request.session.get("otp_code")
            entered_code = request.POST.get("otp_code", "").strip()

            if pre_user_id and correct_otp and entered_code == correct_otp:
                user = get_object_or_404(User, id=pre_user_id)
                login(request, user)
                request.session.pop("pre_auth_user_id", None)
                request.session.pop("otp_code", None)

                if user.must_change_password:
                    dest_url = reverse("force_password_change")
                elif user.role == User.CLIENT:
                    dest_url = reverse("client_portal")
                elif user.role == User.MEDICAL_PROVIDER:
                    dest_url = reverse("medical_portal")
                elif user.role == User.FIRM_ADMIN:
                    dest_url = reverse("firm_admin")
                elif user.role == User.SUPERADMIN:
                    dest_url = reverse("superadmin_dashboard")
                else:
                    dest_url = reverse("index")

                if is_ajax:
                    return JsonResponse({"success": True, "redirect_url": dest_url})
                return HttpResponseRedirect(dest_url)
            else:
                err_msg = "Invalid 6-digit verification code. Please try again."
                if is_ajax:
                    return JsonResponse({"success": False, "error": err_msg})
                return render(request, "claims/login.html", {"message": err_msg})

        # Primary username/password validation
        identifier = request.POST.get("username", "").strip()
        p = request.POST.get("password", "").strip()

        matched_user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        auth_username = matched_user.username if matched_user else identifier

        user = authenticate(request, username=auth_username, password=p)

        if user is not None:
            code = f"{random.randint(100000, 999999)}"
            request.session["pre_auth_user_id"] = user.id
            request.session["otp_code"] = code

            recipient = user.email or identifier
            if recipient:
                subject = "Your LegalCRM 6-Digit Authentication Code"
                body = (
                    f"Hello {user.get_full_name() or user.username},\n\n"
                    f"Your one-time authentication code is:\n\n"
                    f"    {code}\n\n"
                    f"Enter this code to verify your device and access your file.\n\n"
                    f"LegalCRM Litigation Cloud"
                )
                try:
                    send_mail(subject, body, None, [recipient], fail_silently=True)
                except Exception as mail_err:
                    print(f"Error dispatching OTP email: {mail_err}")

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "require_otp": True,
                    "user_display": user.email or user.username
                })
            return HttpResponseRedirect(reverse("verify_otp"))
        else:
            err_msg = "Invalid email/username or password."
            if is_ajax:
                return JsonResponse({"success": False, "error": err_msg})
            return render(request, "claims/login.html", {"message": err_msg})

    return render(request, "claims/login.html")


def verify_otp_view(request):
    """Fallback standard page verification for the 6-digit OTP."""
    pre_user_id = request.session.get("pre_auth_user_id")
    correct_otp = request.session.get("otp_code")

    if not pre_user_id or not correct_otp:
        return redirect("login")

    error_message = None
    if request.method == "POST":
        entered_code = request.POST.get("otp_code", "").strip()

        if entered_code == correct_otp:
            user = get_object_or_404(User, id=pre_user_id)
            login(request, user)

            request.session.pop("pre_auth_user_id", None)
            request.session.pop("otp_code", None)

            if user.must_change_password:
                return HttpResponseRedirect(reverse("force_password_change"))
            if user.role == User.CLIENT:
                return HttpResponseRedirect(reverse("client_portal"))
            if user.role == User.MEDICAL_PROVIDER:
                return HttpResponseRedirect(reverse("medical_portal"))
            if user.role == User.FIRM_ADMIN:
                return HttpResponseRedirect(reverse("firm_admin"))
            if user.role == User.SUPERADMIN:
                return HttpResponseRedirect(reverse("superadmin_dashboard"))
            return HttpResponseRedirect(reverse("index"))
        else:
            error_message = "Invalid 6-digit verification code. Please check your email and try again."

    return render(request, "claims/verify_otp.html", {"error_message": error_message})


@login_required
def force_password_change_view(request):
    """Mandates password update for accounts flagged with must_change_password."""
    error_message = None
    if request.method == "POST":
        p1 = request.POST.get("new_password", "").strip()
        p2 = request.POST.get("confirm_password", "").strip()

        if len(p1) < 8:
            error_message = "Password must be at least 8 characters long."
        elif p1 != p2:
            error_message = "Passwords do not match."
        else:
            user = request.user
            user.set_password(p1)
            user.must_change_password = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password established successfully.")

            if user.role == User.CLIENT:
                return redirect("client_portal")
            elif user.role == User.MEDICAL_PROVIDER:
                return redirect("medical_portal")
            elif user.role == User.FIRM_ADMIN:
                return redirect("firm_admin")
            elif user.role == User.SUPERADMIN:
                return redirect("superadmin_dashboard")
            return redirect("index")

    return render(request, "claims/force_password_change.html", {"error_message": error_message})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        role = request.POST.get("role", User.CLIENT)

        if password != confirmation:
            return render(request, "claims/register.html", {"message": "Passwords must match."})

        try:
            user = User.objects.create_user(username=email, email=email, password=password)
            user.role = role
            user.save()
            login(request, user)
            if user.role == User.CLIENT:
                return HttpResponseRedirect(reverse("client_portal"))
            return HttpResponseRedirect(reverse("index"))
        except Exception as e:
            return render(request, "claims/register.html", {"message": f"Error registering user: {e}"})
    return render(request, "claims/register.html")


@login_required
@transaction.atomic
def new_case(request):
    if request.user.role == User.CLIENT:
        return redirect('client_portal')

    if request.method == "POST":
        case_number = request.POST.get("case_number", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        client_dob = request.POST.get("client_dob") or None
        client_dl = request.POST.get("client_dl", "").strip()
        client_password = request.POST.get("client_password", "ClientPass123!").strip()

        er_facility = request.POST.get("er_facility", "").strip()
        ambulance_raw = request.POST.get("ambulance_provider", "").strip()
        police_report = request.POST.get("police_report_number", "").strip()
        incident_date = request.POST.get("incident_date") or None
        accident_location = request.POST.get("accident_location", "").strip()
        accident_description = request.POST.get("accident_description", "").strip()

        carrier = request.POST.get("insurance_carrier", "").strip()
        policy = request.POST.get("policy_number", "").strip()
        claim = request.POST.get("claim_number", "").strip()

        atty_id = request.POST.get("assigned_attorney")
        cm_id = request.POST.get("assigned_case_manager")

        if not case_number:
            case_number = f"CAS-{date.today().strftime('%Y%m%d')}-{Case.objects.count() + 101}"

        client, _ = Client.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "date_of_birth": client_dob,
                "drivers_license": client_dl,
            }
        )
        if client_dob and not client.date_of_birth:
            client.date_of_birth = client_dob
            client.save(update_fields=['date_of_birth'])

        if email and not client.user:
            client_user = User.objects.filter(username=email).first()
            if not client_user:
                client_user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=client_password or "ClientPass123!",
                    first_name=first_name,
                    last_name=last_name,
                    role=User.CLIENT,
                    phone=phone,
                    must_change_password=True,
                )
            client.user = client_user
            client.save()

            login_url = request.build_absolute_uri(reverse('login'))
            subject = f"Your LegalCRM Client Portal Access - Case #{case_number}"
            message = (
                f"Hello {first_name} {last_name},\n\n"
                f"Your confidential case management file #{case_number} has been created.\n\n"
                f"Portal Link: {login_url}\n"
                f"Login Email: {email}\n"
                f"Temporary Password: {client_password}\n\n"
                f"LegalCRM Litigation Cloud"
            )
            try:
                send_mail(subject, message, None, [email], fail_silently=True)
            except Exception as mail_err:
                print(f"Error dispatching onboarding email: {mail_err}")

        primary_case = Case.objects.create(
            case_number=case_number,
            firm=request.user.firm if hasattr(request.user, 'firm') else None,
            client=client,
            police_report_number=police_report,
            incident_date=incident_date,
            accident_location=accident_location,
            accident_description=accident_description,
            er_facility=er_facility or None,
            ambulance_provider=ambulance_raw or None,
            insurance_carrier=carrier,
            policy_number=policy,
            claim_number=claim,
            assigned_attorney=User.objects.filter(id=atty_id).first() if atty_id else None,
            assigned_case_manager=User.objects.filter(id=cm_id).first() if cm_id else None,
        )

        passenger_names = request.POST.getlist("passenger_name")
        passenger_dobs = request.POST.getlist("passenger_dob")
        passenger_phones = request.POST.getlist("passenger_phone")
        passenger_emails = request.POST.getlist("passenger_email")
        passenger_injured = request.POST.getlist("passenger_injured")

        adult_cases_created = 0
        today = date.today()

        for idx, p_name in enumerate(passenger_names):
            p_name = p_name.strip()
            if not p_name:
                continue

            dob_str = passenger_dobs[idx].strip() if idx < len(passenger_dobs) else ""
            p_phone = passenger_phones[idx].strip() if idx < len(passenger_phones) else ""
            p_email = passenger_emails[idx].strip().lower() if idx < len(passenger_emails) else ""
            is_injured = (passenger_injured[idx].lower() == "true") if idx < len(passenger_injured) else False

            p_dob = None
            is_minor = False
            if dob_str:
                try:
                    p_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                    age = today.year - p_dob.year - ((today.month, today.day) < (p_dob.month, p_dob.day))
                    is_minor = (age < 18)
                except ValueError:
                    p_dob = None

            linked_case_obj = None
            if not is_minor and p_email:
                adult_cases_created += 1
                name_parts = p_name.split()
                p_first = name_parts[0]
                p_last = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Passenger"

                p_client, _ = Client.objects.get_or_create(
                    email=p_email,
                    defaults={"first_name": p_first, "last_name": p_last, "phone": p_phone, "date_of_birth": p_dob}
                )

                if not p_client.user:
                    p_user = User.objects.filter(username=p_email).first()
                    if not p_user:
                        p_user = User.objects.create_user(
                            username=p_email,
                            email=p_email,
                            password="ClientPass123!",
                            first_name=p_first,
                            last_name=p_last,
                            role=User.CLIENT,
                            phone=p_phone,
                            must_change_password=True,
                        )
                    p_client.user = p_user
                    p_client.save()

                linked_case_obj = Case.objects.create(
                    case_number=f"{case_number}-P{adult_cases_created}",
                    firm=primary_case.firm,
                    client=p_client,
                    police_report_number=police_report,
                    incident_date=incident_date,
                    accident_location=accident_location,
                    accident_description=f"Passenger claim originating from primary vehicle case #{primary_case.case_number}.\n{accident_description}",
                    insurance_carrier=carrier,
                    policy_number=policy,
                    claim_number=claim,
                    assigned_attorney=primary_case.assigned_attorney,
                    assigned_case_manager=primary_case.assigned_case_manager,
                )
                CaseNote.objects.create(
                    case=linked_case_obj,
                    author=request.user,
                    content=f"Independent passenger file created from primary driver file #{primary_case.case_number} ({client.first_name} {client.last_name})."
                )

            Passenger.objects.create(
                case=primary_case,
                name=p_name,
                date_of_birth=p_dob,
                phone=p_phone or None,
                email=p_email or None,
                is_injured=is_injured,
                is_minor=is_minor,
                linked_case=linked_case_obj
            )

        if adult_cases_created > 0:
            messages.info(
                request,
                f"Intake completed. Generated primary case #{primary_case.case_number} and {adult_cases_created} independent adult passenger case file(s)."
            )

        return redirect("case_detail", case_id=primary_case.id)

    attorneys = User.objects.filter(role=User.ATTORNEY)
    case_managers = User.objects.filter(role=User.CASE_MANAGER)
    return render(request, "claims/new_case.html", {
        "attorneys": attorneys,
        "case_managers": case_managers,
    })


@login_required
def index(request):
    if request.user.role == User.CLIENT:
        return HttpResponseRedirect(reverse("client_portal"))
    if request.user.role == User.MEDICAL_PROVIDER:
        return HttpResponseRedirect(reverse("medical_portal"))

    cases_qs = Case.objects.filter(is_archived=False).select_related('client', 'assigned_attorney', 'assigned_case_manager').order_by('-created_at')

    is_assigned = request.GET.get("my_cases") == "true"
    if is_assigned:
        if request.user.role == User.ATTORNEY:
            cases_qs = cases_qs.filter(assigned_attorney=request.user)
        elif request.user.role == User.CASE_MANAGER:
            cases_qs = cases_qs.filter(assigned_case_manager=request.user)

    current_filter = request.GET.get("status", "").strip().upper()
    if current_filter:
        cases_qs = cases_qs.filter(status=current_filter)

    total_cases = Case.objects.filter(is_archived=False).count()
    intake_count = Case.objects.filter(is_archived=False, status="INTAKE").count()
    treatment_count = Case.objects.filter(is_archived=False, status="TREATMENT").count()
    demand_count = Case.objects.filter(is_archived=False, status="DEMAND").count()
    negotiations_count = Case.objects.filter(is_archived=False, status="NEGOTIATIONS").count()
    litigation_count = Case.objects.filter(is_archived=False, status="LITIGATION").count()
    settled_count = Case.objects.filter(is_archived=False, status="SETTLED").count()

    return render(request, "claims/index.html", {
        "cases": cases_qs,
        "is_assigned": is_assigned,
        "current_filter": current_filter,
        "total_cases": total_cases,
        "intake_count": intake_count,
        "treatment_count": treatment_count,
        "demand_count": demand_count,
        "negotiations_count": negotiations_count,
        "litigation_count": litigation_count,
        "settled_count": settled_count,
    })


@login_required
def client_portal(request):
    user_cases = Case.objects.filter(Q(client__user=request.user) | Q(client__email__iexact=request.user.email)).distinct()
    
    selected_case_id = request.GET.get("case_id")
    if selected_case_id:
        active_case = user_cases.filter(id=selected_case_id).first() or user_cases.first()
    else:
        active_case = user_cases.first()

    if not active_case:
        active_case = Case.objects.first()

    cases = list(user_cases) if user_cases.exists() else ([active_case] if active_case else [])
    client = active_case.client if active_case else None
    documents = active_case.documents.all() if active_case else []
    passengers = active_case.passengers.all() if active_case else []

    if request.method == "POST" and active_case:
        action = request.POST.get("action")

        if action == "upload_doc" or request.FILES.get("document_file") or request.FILES.get("file"):
            doc_file = request.FILES.get("document_file") or request.FILES.get("file")
            title = request.POST.get("title", "").strip()
            other_title = request.POST.get("other_title", "").strip()
            final_title = other_title if title == "OTHER_UNLISTED" and other_title else (title or (doc_file.name if doc_file else "Uploaded Document"))
            doc_type = request.POST.get("document_type", "OTHER")
            notes = request.POST.get("notes", "").strip()

            if doc_file:
                doc = CaseDocument.objects.create(
                    case=active_case,
                    uploaded_by=request.user,
                    title=final_title,
                    document_type=doc_type,
                    file=doc_file
                )
                if notes:
                    CaseNote.objects.create(
                        case=active_case,
                        author=request.user,
                        content=f"[CLIENT UPLOAD] {doc.title} ({doc.get_document_type_display()}):\n{notes}"
                    )
            return redirect('client_portal')

        elif action == "treatment_complete":
            provider = request.POST.get("provider_name", "").strip()
            if provider == "OTHER_UNLISTED":
                provider = request.POST.get("other_provider_name", "Other Provider").strip()
            rating = request.POST.get("rating", "N/A")
            last_date = request.POST.get("last_appointment_date", "Unspecified")
            scope = request.POST.get("completion_scope", "")
            continuing = request.POST.get("continuing_clinic_name", "").strip()
            notes = request.POST.get("notes", "").strip()

            scope_text = "Completely done with all treatment" if scope == "ALL_DONE" else f"Finished with this clinic only (Still seeing: {continuing or 'other doctors'})"

            note_body = (
                f"[TREATMENT UPDATE FROM CLIENT]\n"
                f"Provider: {provider}\n"
                f"Discharge/Completion Date: {last_date}\n"
                f"Status: {scope_text}\n"
                f"Rating: {rating}/5 Stars\n"
            )
            if notes:
                note_body += f"Client Notes: {notes}"

            CaseNote.objects.create(
                case=active_case,
                author=request.user,
                content=note_body
            )

            if scope == "ALL_DONE" and active_case.status == "TREATMENT":
                active_case.status = "DEMAND"
                active_case.save()

            messages.success(request, "Your medical treatment update has been submitted to your legal team.")
            return redirect('client_portal')

    return render(request, "claims/client_portal.html", {
        "cases": cases,
        "case": active_case,
        "client": client,
        "documents": documents,
        "passengers": passengers,
    })


@login_required
def case_detail(request, case_id):
    if request.user.role == User.CLIENT:
        return redirect('client_portal')

    case = get_object_or_404(Case.objects.select_related('client', 'assigned_attorney', 'assigned_case_manager'), id=case_id)

    if request.method == "POST" and request.FILES.get("document_file"):
        doc_file = request.FILES.get("document_file")
        title = request.POST.get("title", "").strip()
        doc_type = request.POST.get("document_type", "OTHER")
        if doc_file:
            CaseDocument.objects.create(
                case=case,
                uploaded_by=request.user,
                title=title if title else doc_file.name,
                document_type=doc_type,
                file=doc_file
            )
        return redirect('case_detail', case_id=case_id)

    notes = case.notes.all().select_related('author').order_by('-created_at')
    bills = case.medical_bills.all().order_by('-created_at')
    documents = case.documents.all().order_by('-uploaded_at')
    passengers = case.passengers.all().select_related('linked_case')

    settlement, _ = Settlement.objects.get_or_create(case=case)
    total_medical = sum(bill.effective_amount for bill in bills) if bills.exists() else Decimal('0.00')

    attorneys = User.objects.filter(role=User.ATTORNEY)
    case_managers = User.objects.filter(role=User.CASE_MANAGER)

    return render(request, "claims/case_detail.html", {
        "case": case,
        "notes": notes,
        "bills": bills,
        "documents": documents,
        "passengers": passengers,
        "settlement": settlement,
        "total_medical": total_medical,
        "status_choices": Case.STATUS_CHOICES,
        "attorneys": attorneys,
        "case_managers": case_managers,
    })


@login_required
def api_add_passenger(request, case_id):
    """Adds a passenger directly from case detail."""
    case = get_object_or_404(Case, id=case_id)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        dob_str = request.POST.get("date_of_birth", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        is_injured = request.POST.get("is_injured") in ["on", "true", "True", True]

        p_dob = None
        is_minor = False
        if dob_str:
            try:
                p_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                today = date.today()
                age = today.year - p_dob.year - ((today.month, today.day) < (p_dob.month, p_dob.day))
                is_minor = (age < 18)
            except ValueError:
                p_dob = None

        if name:
            Passenger.objects.create(
                case=case,
                name=name,
                date_of_birth=p_dob,
                phone=phone or None,
                email=email or None,
                is_injured=is_injured,
                is_minor=is_minor
            )
            messages.success(request, f"Passenger {name} added to file.")
    return redirect('case_detail', case_id=case_id)


@login_required
def delete_document(request, case_id, doc_id):
    if request.method == "POST":
        doc = get_object_or_404(CaseDocument, id=doc_id, case_id=case_id)
        doc.delete()
        messages.success(request, "Document removed successfully.")
    return redirect('case_detail', case_id=case_id)


@login_required
def api_add_note(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(Case, id=case_id)
        content = request.POST.get("content", "").strip()
        if content:
            CaseNote.objects.create(case=case, author=request.user, content=content)
    return redirect('case_detail', case_id=case_id)


@login_required
def api_add_bill(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(Case, id=case_id)
        provider = request.POST.get("provider", "").strip()
        amount = request.POST.get("amount", "0.00")
        received = request.POST.get("received") in ["on", "true", "True", True]
        doc_file = request.FILES.get("bill_document")

        if provider:
            MedicalBill.objects.create(
                case=case,
                provider=provider,
                amount=Decimal(str(amount or 0)),
                received=received,
                bill_document=doc_file
            )
    return redirect('case_detail', case_id=case_id)


@login_required
def edit_bill(request, case_id, bill_id):
    bill = get_object_or_404(MedicalBill, id=bill_id, case_id=case_id)
    if request.method == "POST":
        bill.provider = request.POST.get("provider", bill.provider).strip()
        amount_raw = request.POST.get("amount")
        if amount_raw:
            bill.amount = Decimal(str(amount_raw))
        
        reduced_raw = request.POST.get("reduced_amount", "").strip()
        bill.reduced_amount = Decimal(str(reduced_raw)) if reduced_raw else None

        bill.received = request.POST.get("received") in ["on", "true", "True", True]

        if request.FILES.get("bill_document"):
            bill.bill_document = request.FILES.get("bill_document")

        bill.save()
        messages.success(request, f"Updated bill for {bill.provider}.")
    return redirect('case_detail', case_id=case_id)


@login_required
def delete_bill(request, case_id, bill_id):
    bill = get_object_or_404(MedicalBill, id=bill_id, case_id=case_id)
    if request.method == "POST":
        bill.delete()
    return redirect('case_detail', case_id=case_id)


@login_required
def api_update_status(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(Case, id=case_id)
        new_status = request.POST.get("status", "").strip().upper()

        if new_status and new_status in dict(Case.STATUS_CHOICES):
            if new_status != 'INTAKE' and not case.assigned_attorney:
                messages.error(
                    request,
                    f"Action Required: You cannot advance this file to '{dict(Case.STATUS_CHOICES).get(new_status)}' until a Lead Attorney is assigned."
                )
                return redirect('case_detail', case_id=case.id)

            old_name = case.get_status_display()
            case.status = new_status
            if new_status == 'SETTLED' and not case.settled_date:
                case.settled_date = date.today()
            case.save()

            CaseNote.objects.create(
                case=case,
                author=request.user,
                content=f"Stage transitioned from '{old_name}' to '{case.get_status_display()}'."
            )

            if case.client and case.client.email:
                portal_url = request.build_absolute_uri(reverse('client_portal'))
                subject = f"Case Update: File #{case.case_number} has moved to {case.get_status_display()}"
                message = (
                    f"Hello {case.client.first_name} {case.client.last_name},\n\n"
                    f"Your case #{case.case_number} has officially progressed to:\n"
                    f"Current Status: {case.get_status_display()}\n\n"
                    f"Portal Link: {portal_url}\n\n"
                    f"LegalCRM Litigation Cloud"
                )
                try:
                    send_mail(subject, message, None, [case.client.email], fail_silently=True)
                except Exception as mail_err:
                    print(f"Error dispatching status email: {mail_err}")

            messages.success(request, f"Case stage updated to {case.get_status_display()}.")

    return redirect('case_detail', case_id=case_id)


@login_required
def update_case_assignment(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(Case, id=case_id)
        atty_id = request.POST.get("assigned_attorney")
        cm_id = request.POST.get("assigned_case_manager")

        case.assigned_attorney = User.objects.filter(id=atty_id).first() if atty_id else None
        case.assigned_case_manager = User.objects.filter(id=cm_id).first() if cm_id else None
        case.insurance_carrier = request.POST.get("insurance_carrier", "").strip()
        case.policy_number = request.POST.get("policy_number", "").strip()
        case.claim_number = request.POST.get("claim_number", "").strip()
        case.save()
        messages.success(request, "Case assignments and file details saved successfully.")
    return redirect('case_detail', case_id=case_id)


@login_required
def api_save_settlement(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    settlement, _ = Settlement.objects.get_or_create(case=case)

    if request.method == "POST":
        gross = Decimal(str(request.POST.get("gross_settlement") or 0))
        fee_pct = Decimal(str(request.POST.get("attorney_fee_percent") or 33.33))
        costs = Decimal(str(request.POST.get("litigation_costs") or 0))
        total_medical = sum(bill.effective_amount for bill in case.medical_bills.all()) if case.medical_bills.exists() else Decimal('0.00')

        atty_fee = (gross * fee_pct) / Decimal('100')
        net = gross - atty_fee - costs - total_medical

        settlement.gross_settlement = gross
        settlement.attorney_fee_percent = fee_pct
        settlement.litigation_costs = costs
        settlement.final_client_net = net
        settlement.save()
        messages.success(request, "Settlement numbers updated.")

    return redirect('case_detail', case_id=case.id)


@login_required
def send_case_message(request, case_id):
    if request.method == "POST":
        case = get_object_or_404(Case, id=case_id)
        message_body = request.POST.get("body", "").strip()

        if message_body:
            case.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
            CaseMessage.objects.create(case=case, sender=request.user, body=message_body)

        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("inbox")
    return redirect("index")


@login_required
def api_unread_count(request):
    if request.user.role == User.CLIENT:
        count = CaseMessage.objects.filter(case__client__user=request.user, is_read=False).exclude(sender=request.user).count()
    else:
        count = CaseMessage.objects.filter(is_read=False).count()
    return JsonResponse({"unread": count})


@login_required
def inbox_view(request):
    is_client = (request.user.role == User.CLIENT)

    if is_client:
        active_case = Case.objects.filter(client__user=request.user).first()
        conversation_cases = [active_case] if active_case else []
        selected_case = active_case
    else:
        cases_qs = Case.objects.annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False), distinct=True),
            total_messages=Count('messages', distinct=True)
        )
        conversation_cases = cases_qs.select_related('client', 'assigned_attorney', 'assigned_case_manager').order_by(
            '-unread_count', '-total_messages', '-updated_at'
        )
        case_id_param = request.GET.get('case_id')
        selected_case = get_object_or_404(Case, id=case_id_param) if case_id_param else conversation_cases.first()

    messages_feed = selected_case.messages.select_related('sender').order_by('created_at') if selected_case else []

    return render(request, "claims/inbox.html", {
        "is_client": is_client,
        "conversation_cases": conversation_cases,
        "selected_case": selected_case,
        "messages_feed": messages_feed,
    })


@login_required
def api_simulate_incoming(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    sender = case.client.user if (case.client and case.client.user) else request.user
    CaseMessage.objects.create(
        case=case,
        sender=sender,
        body="Hello, I received a new invoice from the radiology clinic. Could you please review it?",
        is_read=False
    )
    messages.info(request, "Simulated incoming client message generated.")
    return redirect(f"{reverse('inbox')}?case_id={case.id}")


@login_required
def api_mark_thread_unread(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    latest_msg = case.messages.order_by('-created_at').first()
    if latest_msg:
        latest_msg.is_read = False
        latest_msg.save()
    return redirect(f"{reverse('inbox')}?case_id={case.id}")


@login_required
def api_mark_thread_read(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    case.messages.filter(is_read=False).update(is_read=True)
    return redirect(f"{reverse('inbox')}?case_id={case.id}")


@login_required
def delete_case(request, case_id):
    """Deletes a case file and records a mandatory audit log entry (Migration 0018)."""
    if request.user.role == User.CLIENT:
        return HttpResponseForbidden("Unauthorized: Clients cannot delete case files.")

    case = get_object_or_404(Case, id=case_id)
    if request.method == "POST":
        case_num = case.case_number
        client_name = f"{case.client.first_name} {case.client.last_name}"
        reason = request.POST.get("delete_reason", "Staff administrative deletion").strip()
        summary = f"Case #{case_num} ({case.get_status_display()}) with {case.medical_bills.count()} bills and {case.documents.count()} documents."

        DeletedCaseLog.objects.create(
            case_number=case_num,
            client_name=client_name,
            deleted_by=request.user,
            reason=reason or "Administrative deletion",
            summary=summary
        )

        case.delete()
        messages.success(request, f"Case #{case_num} was permanently deleted and logged to the audit registry.")
        return redirect("index")

    return redirect("case_detail", case_id=case_id)


# --- Portals from Migration 0019 ---

@login_required
def firm_admin_view(request):
    """Firm management dashboard for user roles, firm profile, and email templates."""
    if request.user.role not in [User.FIRM_ADMIN, User.SUPERADMIN]:
        return HttpResponseForbidden("Access restricted to Law Firm Administrators.")

    firm = request.user.firm or LawFirm.objects.first()
    staff = User.objects.filter(firm=firm) if firm else User.objects.all()
    templates = EmailTemplate.objects.filter(firm=firm) if firm else []

    return render(request, "claims/firm_admin.html", {
        "firm": firm,
        "staff": staff,
        "templates": templates,
    })


@login_required
def medical_portal_view(request):
    """Provider network portal for treatment logs and medical lien management."""
    facility = request.user.medical_facility or MedicalProviderFacility.objects.first()
    records = MedicalTreatmentRecord.objects.filter(facility=facility) if facility else MedicalTreatmentRecord.objects.all()

    return render(request, "claims/medical_portal.html", {
        "facility": facility,
        "records": records,
    })


@login_required
def superadmin_dashboard_view(request):
    """Platform SuperAdmin hub managing all tenant law firms and provider networks."""
    if request.user.role != User.SUPERADMIN and not request.user.is_superuser:
        return HttpResponseForbidden("Access restricted to Platform SuperAdmins.")

    firms = LawFirm.objects.all()
    facilities = MedicalProviderFacility.objects.all()
    audit_logs = DeletedCaseLog.objects.all()[:20]

    return render(request, "claims/superadmin_dashboard.html", {
        "firms": firms,
        "facilities": facilities,
        "audit_logs": audit_logs,
    })