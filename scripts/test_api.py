import os
import sys
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8003/api"


def request(method, path, data=None):
    url = BASE + path
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def check(label, status, body, expected_status=200, body_check=None):
    ok = (status == expected_status)
    if body_check is not None:
        ok = body_check(body) and ok
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] {label} -> HTTP {status}")
    if not ok:
        print(f"     body: {json.dumps(body, ensure_ascii=False)[:200]}")
    return ok, body


all_passed = True

# ============= residents =============
print("\n--- Residents API ---")
status, body = request("GET", "/residents/")
ok, body = check("GET /residents/", status, body, body_check=lambda b: "results" in b)
all_passed &= ok
resident_id = body["results"][0]["id"] if body.get("results") else None

status, body = request("GET", f"/residents/{resident_id}/")
ok, _ = check(f"GET /residents/{resident_id}/", status, body,
              body_check=lambda b: "id" in b and "name" in b)
all_passed &= ok

new_resident = {
    "name": "API测试老人",
    "gender": "male",
    "age": 75,
    "room_number": "A-API-01",
    "care_level": "assisted",
    "emergency_contact": "测试家属",
    "emergency_phone": "13900000000",
    "medical_notes": "高血压",
}
status, body = request("POST", "/residents/", new_resident)
ok, body = check("POST /residents/", status, body, expected_status=201,
                 body_check=lambda b: "id" in b and b["name"] == "API测试老人")
all_passed &= ok
new_id = body["id"]

status, body = request("PUT", f"/residents/{new_id}/", {"name": "Modified老人", "room_number": "B-999"})
ok, body = check(f"PUT /residents/{new_id}/", status, body,
                 body_check=lambda b: b.get("name") == "Modified老人" and b.get("room_number") == "B-999")
all_passed &= ok

status, body = request("DELETE", f"/residents/{new_id}/")
ok, _ = check(f"DELETE /residents/{new_id}/", status, body,
              body_check=lambda b: b.get("deleted") is True)
all_passed &= ok

# ============= notifications =============
print("\n--- Notifications API ---")
status, body = request("GET", "/notifications/")
ok, body = check("GET /notifications/", status, body, body_check=lambda b: "results" in b)
all_passed &= ok
notif_id = body["results"][0]["id"] if body.get("results") else None

status, body = request("GET", f"/notifications/{notif_id}/")
ok, _ = check(f"GET /notifications/{notif_id}/", status, body,
              body_check=lambda b: "title" in b)
all_passed &= ok

new_notif = {"title": "API发布的通知", "content": "通知内容测试", "level": "info", "target_group": "all"}
status, body = request("POST", "/notifications/", new_notif)
ok, body = check("POST /notifications/", status, body, expected_status=201,
                 body_check=lambda b: b.get("title") == "API发布的通知")
all_passed &= ok
new_notif_id = body["id"]

status, body = request("DELETE", f"/notifications/{new_notif_id}/")
ok, _ = check(f"DELETE /notifications/{new_notif_id}/", status, body,
              body_check=lambda b: b.get("deleted") is True)
all_passed &= ok

# Filter test
status, body = request("GET", "/notifications/?active=true")
ok, _ = check("GET /notifications/?active=true", status, body,
              body_check=lambda b: all(n["is_active"] for n in b["results"]))
all_passed &= ok

# ============= appointments =============
print("\n--- Appointments API ---")
status, body = request("GET", "/appointments/")
ok, body = check("GET /appointments/", status, body, body_check=lambda b: "results" in b)
all_passed &= ok
apt_id = body["results"][0]["id"] if body.get("results") else None

status, body = request("GET", f"/appointments/{apt_id}/")
ok, body = check(f"GET /appointments/{apt_id}/", status, body,
                 body_check=lambda b: "resident" in b and isinstance(b["resident"], dict))
all_passed &= ok
print(f"  -> resident name = {body.get('resident', {}).get('name')!r}")

# Filter test
status, body = request("GET", "/appointments/?status=approved")
ok, _ = check("GET /appointments/?status=approved", status, body,
              body_check=lambda b: all(a["status"] == "approved" for a in b["results"]))
all_passed &= ok

# Create appointment
new_apt = {
    "resident": resident_id,
    "family_name": "API家属",
    "family_phone": "18600000000",
    "relationship": "子女",
    "visit_time": "2026-07-01T10:00:00",
    "visitor_count": 2,
    "notes": "API测试预约",
}
status, body = request("POST", "/appointments/", new_apt)
ok, body = check("POST /appointments/", status, body, expected_status=201,
                 body_check=lambda b: b.get("family_name") == "API家属")
all_passed &= ok
new_apt_id = body["id"]

status, body = request("PUT", f"/appointments/{new_apt_id}/", {"status": "cancelled"})
ok, body = check(f"PUT /appointments/{new_apt_id}/ status=cancelled", status, body,
                 body_check=lambda b: b.get("status") == "cancelled")
all_passed &= ok
print(f"  -> status updated to: {body.get('status')!r}")

status, body = request("DELETE", f"/appointments/{new_apt_id}/")
ok, _ = check(f"DELETE /appointments/{new_apt_id}/", status, body,
              body_check=lambda b: b.get("deleted") is True)
all_passed &= ok

# ============= visits =============
print("\n--- Visits API ---")
status, body = request("GET", "/visits/")
ok, body = check("GET /visits/", status, body, body_check=lambda b: "results" in b)
all_passed &= ok

if body.get("results"):
    visit_id = body["results"][0]["id"]
    status, body = request("GET", f"/visits/{visit_id}/")
    ok, body = check(f"GET /visits/{visit_id}/", status, body,
                     body_check=lambda b: "appointment" in b and isinstance(b["appointment"], dict))
    all_passed &= ok
    print(f"  -> appointment status = {body.get('appointment', {}).get('status')!r}")
    print(f"  -> visitor_temperature = {body.get('visitor_temperature')!r}")
    print(f"  -> check_out_time = {body.get('check_out_time')!r}")

# Create a pending appointment for visit test
status, pending_apt = request("POST", "/appointments/", {
    "resident": resident_id,
    "family_name": "VisitTest家属",
    "family_phone": "18700000000",
    "relationship": "配偶",
    "visit_time": "2026-07-02T14:00:00",
    "visitor_count": 1,
})
target_apt_id = pending_apt["id"]
print(f"  Created pending appointment {target_apt_id} for visit test")

new_visit = {
    "appointment": target_apt_id,
    "check_in_time": "2026-07-02T14:05:00",
    "check_out_time": "",
    "visitor_temperature": "36.5",
    "staff_name": "API员工",
    "summary": "API测试探视",
}
status, body = request("POST", "/visits/", new_visit)
ok, body = check("POST /visits/ (auto mark apt completed)", status, body, expected_status=201,
                 body_check=lambda b: b.get("staff_name") == "API员工")
all_passed &= ok
new_visit_id = body["id"]
print(f"  -> visitor_temperature in response: {body.get('visitor_temperature')!r}")
print(f"  -> check_out_time in response: {body.get('check_out_time')!r}")

# Verify side-effect: appointment should be marked as completed
status, apt_body = request("GET", f"/appointments/{target_apt_id}/")
marker = "PASS" if apt_body.get("status") == "completed" else "FAIL"
all_passed &= apt_body.get("status") == "completed"
print(f"[{marker}] Side-effect: appointment status = {apt_body.get('status')!r}")

status, body = request("DELETE", f"/visits/{new_visit_id}/")
ok, _ = check(f"DELETE /visits/{new_visit_id}/", status, body,
              body_check=lambda b: b.get("deleted") is True)
all_passed &= ok

print("\n" + ("=" * 50))
if all_passed:
    print("ALL API TESTS PASSED")
else:
    print("SOME API TESTS FAILED")
    sys.exit(1)
