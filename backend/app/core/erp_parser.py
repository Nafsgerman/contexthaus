import csv
import io
from datetime import date

ERP_SCHEMA_MAP = {
    "Eigentümer": "owner",
    "MietEig": "owner",
    "Eigentuemer": "owner",
    "Kontakt": "owner_contact",
    "MietEig_Kontakt": "owner_contact",
    "Eigentümer_Email": "owner_email",
    "Eigentümer_Tel": "owner_phone",
    "Eigentuemer_Email": "owner_email",
    "Strasse": "address_street",
    "PLZ": "address_plz",
    "Ort": "address_city",
    "Objekt_ID": "erp_id",
    "Heizung_Typ": "heating_system",
    "Heizung_Wartung": "heating_contractor",
    "Offene_Tickets": "open_issues",
    "Letzter_Beschluss": "last_decision",
    "Beschluss_Datum": "last_assembly_date",
    "Hausmeister": "caretaker",
    "Hausmeister_Tel": "caretaker_phone",
}


def parse_erp_csv(content: str, target_address: str = "") -> str:
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return ""

    row = rows[0]
    if target_address and len(rows) > 1:
        for r in rows:
            street = r.get("Strasse", "")
            if street and street.lower() in target_address.lower():
                row = r
                break

    normalized = {}
    for raw_key, value in row.items():
        if not value or not value.strip():
            continue
        normalized_key = ERP_SCHEMA_MAP.get(raw_key, raw_key.lower())
        normalized[normalized_key] = value.strip()

    street = normalized.get("address_street", "")
    plz = normalized.get("address_plz", "")
    city = normalized.get("address_city", "")
    full_address = f"{street}, {plz} {city}".strip(", ")

    owner = normalized.get("owner", "")
    owner_contact = normalized.get("owner_contact", "")
    owner_email = normalized.get("owner_email", "")
    owner_phone = normalized.get("owner_phone", "")
    contact_parts = [p for p in [owner_contact, owner_email, owner_phone] if p]

    today = date.today().isoformat()

    md = f"""## Meta
- address: {full_address}
- erp_id: {normalized.get('erp_id', '')}
- created: {today}
- last_updated: {today}

## Ownership
- owner: {owner}
- owner_contact: {', '.join(contact_parts)}

## Building
- heating_system: {normalized.get('heating_system', '')}
- heating_contractor: {normalized.get('heating_contractor', '')}

## Open Issues
- {normalized.get('open_issues', 'None')}

## Recent Decisions
- {normalized.get('last_decision', '')} ({normalized.get('last_assembly_date', '')})

## Contractors & Contacts
- Caretaker: {normalized.get('caretaker', '')} ({normalized.get('caretaker_phone', '')})
- Heating: {normalized.get('heating_contractor', '')}

---
*Sources: ERP Export (schema-resolved: Eigentümer→owner, MietEig→owner_contact)*"""
    return md.strip()
