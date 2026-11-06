# LegalCRM — Personal Injury Case Management Platform & Client Portal

## Distinctiveness and Complexity

### Distinctiveness
LegalCRM is a specialized, multi-role legal workflow and practice management system tailored specifically for personal injury law practices. It is distinct from standard course projects (such as e-commerce stores, social media feeds, or basic wikis):
- **Specialized Domain Architecture:** Instead of generic blog posts or product listings, the application models personal injury litigation lifecycles—intake, emergency medical tracking, insurance and at-fault driver identification, passenger/witness tracking, medical provider billing and lien reductions, itemized settlement statement calculations, and document vaults.
- **Role-Based Architecture:** The system implements strict separation of concerns across user roles (`ATTORNEY`, `CASE_MANAGER`, and `CLIENT`). Staff members access administrative dashboards, case management pipelines, and financial ledger calculations, while clients access a dedicated, secure Client Portal to view status milestones, track treatment discharge dates, rate medical clinics, and upload crash documentation or medical invoices.

### Complexity
- **Relational Data Modeling:** Built across seven interconnected Django models (`User`, `Client`, `Case`, `Passenger`, `CaseNote`, `MedicalBill`, `Settlement`, and `CaseDocument`) featuring cascades, optional foreign key assignments, file storage handling, and custom model properties (e.g., dynamic effective lien amounts).
- **Dynamic Front-End & Conditional UI:** The intake interface features dynamic DOM expansion and collapse—such as optional ambulance provider capture and scalable, repeatable passenger/witness input cards that enable and disable input fields dynamically to prevent empty payload pollution.
- **Real-Time Client Payout Engine:** Client settlement math dynamically evaluates gross settlement recoveries against attorney contingency fees (e.g., 33.33%), firm litigation expenses, and outstanding medical liens. As bills or negotiated reductions change, client net proceeds update in real time.
- **Asynchronous Interactions & Dual Access Portals:** Provides seamless inline editing of case parameters, file uploads via multipart forms, dynamic status transitions with automated internal note generation, and secure client-facing submission handling.

---

## File Structure & Documentation

### Root Files
- **`manage.py`**: Standard Django project runner for administrative commands and database migrations.
- **`requirements.txt`**: Complete Python package manifest including Django and dependencies.
- **`README.md`**: Project documentation, architecture overview, and deployment guide.

### Backend (`claims/` application)
- **`claims/models.py`**:
  - `User`: Custom abstract user model supporting three permission roles (`ATTORNEY`, `CASE_MANAGER`, `CLIENT`).
  - `Client`: Stores client contact information, driver's license details, and one-to-one portal authentication links.
  - `Case`: Core entity managing claim identifiers, police reports, accident particulars, ER/hospital records, ambulance dispatch flags, at-fault driver info, insurance data, policy limits, and staff assignments.
  - `Passenger`: Tracks occupants present in the vehicle, recording contact information, address, and injury status for co-claimant or witness discovery.
  - `MedicalBill`: Tracks medical providers, gross billed amounts, negotiated lien balances, and attached invoice files.
  - `Settlement`: Financial model calculating gross settlements, contingency fee percentages, litigation costs, and final client net proceeds.
  - `CaseDocument`: File management model cataloging accident photos, police reports, and medical records.
  - `CaseNote`: Chronological timeline log tracking attorney notes, client uploads, and status transitions.
- **`claims/views.py`**:
  - `index`: Staff dashboard rendering case counts across the six workflow stages and assigned case filters.
  - `new_case`: Multi-section intake view handling client profile creation, conditional passenger processing, ambulance logging, and initial case notes.
  - `case_detail`: Master workspace for staff to review evidence, manage bills, calculate settlements, and edit case metadata.
  - `client_portal`: Dedicated interface for clients to review their case stage, submit evidence, and report medical status.
  - `api_add_bill`, `edit_bill`, `delete_bill`: Endpoints handling provider additions, lien reductions, and file attachments.
  - `api_save_settlement`: Endpoint validating and saving itemized settlement statements.
  - `api_update_status`, `api_assign_staff`, `update_case_field`: Endpoints managing operational assignment and stage updates.
- **`claims/urls.py`**: URL routing configuration binding endpoints to view controllers.

### Front-End Templates (`claims/templates/claims/`)
- **`layout.html`**: Master base template containing the navigation header, Bootstrap 5 framework, and responsive container structure.
- **`index.html`**: Primary staff dashboard featuring KPI cards for intake, treatment, demand, negotiations, litigation, and settlement stages, alongside a filterable case table.
- **`new_case.html`**: Four-stage intake form with styled checkbox frames, dynamic passenger row insertion/removal, and staff assignment fields.
- **`case_detail.html`**: Case detail view with inline metadata editing, document uploads, medical bill ledger, and live settlement calculator.
- **`client_portal.html`**: Client-facing portal with milestone timeline progress, direct document upload dropzones, and treatment completion notifications.
- **`login.html` & `register.html`**: Authentication forms for user onboarding and session management.

---

## Installation & Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd legalcrm