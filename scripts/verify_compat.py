import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from backend.residents.models import Resident
from backend.appointments.models import Appointment
from backend.notifications.models import EmergencyNotification
from backend.visits.models import VisitRecord

from backend.residents.services import (
    serialize_resident,
    list_residents,
    create_resident,
    update_resident,
    ResidentCRUDService,
)
from backend.appointments.services import (
    serialize_appointment,
    list_appointments,
    create_appointment,
    update_appointment,
    AppointmentCRUDService,
)
from backend.notifications.services import (
    serialize_notification,
    list_notifications,
    create_notification,
    update_notification,
    NotificationCRUDService,
)
from backend.visits.services import (
    serialize_visit,
    list_visits,
    create_visit,
    update_visit,
    VisitCRUDService,
)


def compare_dict(expected, actual, path=""):
    mismatches = []
    if list(expected.keys()) != list(actual.keys()):
        mismatches.append(f"[{path}] KEY ORDER MISMATCH:\n  expected: {list(expected.keys())}\n  actual:   {list(actual.keys())}")
    for k in expected:
        p = f"{path}.{k}" if path else k
        if k not in actual:
            mismatches.append(f"[{p}] MISSING in actual")
            continue
        ev, av = expected[k], actual[k]
        if isinstance(ev, dict) and isinstance(av, dict):
            mismatches.extend(compare_dict(ev, av, p))
        elif ev != av:
            mismatches.append(f"[{p}] VALUE MISMATCH: expected={ev!r}, actual={av!r}")
    return mismatches


def run():
    all_ok = True

    # ============ residents ============
    print("=== Checking Residents ===")
    resident = Resident.objects.first()
    compat_data = serialize_resident(resident)
    service_data = ResidentCRUDService().serialize(resident)
    mismatches = compare_dict(compat_data, service_data)
    if mismatches:
        all_ok = False
        for m in mismatches:
            print("  " + m)
    else:
        print("  serialize_resident: OK")

    compat_list = list_residents()
    service_list = ResidentCRUDService().list()
    if len(compat_list) == len(service_list):
        print(f"  list_residents count: OK ({len(compat_list)} items)")
    else:
        all_ok = False
        print(f"  list_residents count MISMATCH: compat={len(compat_list)}, service={len(service_list)}")

    # ============ notifications ============
    print("=== Checking Notifications ===")
    notif = EmergencyNotification.objects.first()
    compat_data = serialize_notification(notif)
    service_data = NotificationCRUDService().serialize(notif)
    mismatches = compare_dict(compat_data, service_data)
    if mismatches:
        all_ok = False
        for m in mismatches:
            print("  " + m)
    else:
        print("  serialize_notification: OK")

    for active in [None, True, False]:
        compat_list = list_notifications(active)
        service_list = NotificationCRUDService().list({"active": active})
        ok_flag = len(compat_list) == len(service_list)
        if ok_flag:
            print(f"  list_notifications(active={active}): OK ({len(compat_list)} items)")
        else:
            all_ok = False
            print(f"  list_notifications(active={active}) MISMATCH: compat={len(compat_list)}, service={len(service_list)}")

    # ============ appointments ============
    print("=== Checking Appointments ===")
    apt = Appointment.objects.select_related("resident").first()
    compat_data = serialize_appointment(apt)
    service_data = AppointmentCRUDService().serialize(apt)
    mismatches = compare_dict(compat_data, service_data)
    if mismatches:
        all_ok = False
        for m in mismatches:
            print("  " + m)
    else:
        print("  serialize_appointment: OK")

    for status in [None, "pending", "approved"]:
        compat_list = list_appointments(status)
        service_list = AppointmentCRUDService().list({"status": status})
        ok_flag = len(compat_list) == len(service_list)
        if ok_flag:
            print(f"  list_appointments(status={status!r}): OK ({len(compat_list)} items)")
        else:
            all_ok = False
            print(f"  list_appointments(status={status!r}) MISMATCH: compat={len(compat_list)}, service={len(service_list)}")

    # ============ visits ============
    print("=== Checking Visits ===")
    visit = VisitRecord.objects.select_related("appointment", "appointment__resident").first()
    if visit:
        compat_data = serialize_visit(visit)
        service_data = VisitCRUDService().serialize(visit)
        mismatches = compare_dict(compat_data, service_data)
        if mismatches:
            all_ok = False
            for m in mismatches:
                print("  " + m)
        else:
            print("  serialize_visit: OK")
    else:
        print("  (no visit records yet, skipping)")

    compat_list = list_visits()
    service_list = VisitCRUDService().list()
    if len(compat_list) == len(service_list):
        print(f"  list_visits count: OK ({len(compat_list)} items)")
    else:
        all_ok = False
        print(f"  list_visits count MISMATCH: compat={len(compat_list)}, service={len(service_list)}")

    # ============ create/update compatibility ============
    print("=== Checking Create/Update Build Compatibility ===")

    payload = {
        "name": "测试老人",
        "gender": "female",
        "age": 80,
        "room_number": "T-101",
        "care_level": "self_care",
        "emergency_contact": "家属A",
        "emergency_phone": "13800000000",
        "medical_notes": "无",
    }
    r1 = create_resident(payload)
    r2 = ResidentCRUDService().build_instance(payload)
    match = all(getattr(r1, f) == getattr(r2, f) for f in payload)
    if match:
        print("  create_resident payload matching: OK")
    else:
        all_ok = False
        print("  create_resident payload matching: FAILED")

    r1.name = "修改后"
    r1.room_number = "T-202"
    update_payload = {"name": "更新老人", "room_number": "T-999"}
    compat_updated = update_resident(r1, update_payload)
    r2.name = "修改后"
    r2.room_number = "T-202"
    svc = ResidentCRUDService()
    data = svc.normalize_payload(update_payload)
    for f, v in data.items():
        if f not in svc.exclude_on_update:
            setattr(r2, f, v)
    match = compat_updated.name == r2.name and compat_updated.room_number == r2.room_number
    if match:
        print("  update_resident payload matching: OK")
    else:
        all_ok = False
        print(f"  update_resident: FAILED (compat name={compat_updated.name}, service name={r2.name})")

    if all_ok:
        print("\n==> ALL CHECKS PASSED")
    else:
        print("\n==> SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    run()
