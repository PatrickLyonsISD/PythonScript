import firebase_admin
from firebase_admin import credentials, db
import datetime
import subprocess
import time
import sys

# Initialize Firebase Admin SDK
cred = credentials.Certificate('/home/patrick/Downloads/final-year-project-1-cbc96-firebase-adminsdk-qjyom-79a3c97e91.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://final-year-project-1-cbc96-default-rtdb.firebaseio.com'
})

def get_connected_devices():
    connected_devices = []
    result = subprocess.run(["bluetoothctl", "paired-devices"], capture_output=True, text=True)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if "Device" in line:
                parts = line.split(' ', 2)
                if len(parts) > 2:
                    device_name = parts[2]
                    connected_devices.append(device_name)
    print("Connected devices:", connected_devices)
    return connected_devices

device_connection_times = {}

def update_device_connection_times(connected_devices):
    global device_connection_times
    now = datetime.datetime.now()
    for device_name in connected_devices:
        if device_name not in device_connection_times:
            device_connection_times[device_name] = now
    connected_set = set(connected_devices)
    device_connection_times = {name: time for name, time in device_connection_times.items() if name in connected_set}
    print("Device connection times updated:", device_connection_times)

def fetch_student_device_names():
    ref = db.reference("/students")
    students_data = ref.get()
    student_devices = {info['deviceName']: uuid for uuid, info in students_data.items() if 'deviceName' in info}
    print("Student devices fetched:", student_devices)
    return student_devices

def get_current_class_and_end_time(student_year):
    now = datetime.datetime.now()
    day_name = now.strftime("%A")
    ref = db.reference(f"/modules")
    modules_data = ref.get()
    for module_id, module_info in modules_data.items():
        if module_info.get('year') != student_year:
            continue
        schedule = module_info.get('schedule', {})
        if day_name in schedule:
            times = schedule.get(day_name, {})
            if 'startTime' in times and 'endTime' in times:
                start_time = datetime.datetime.strptime(times['startTime'], "%H:%M").time()
                end_time = datetime.datetime.strptime(times['endTime'], "%H:%M").time()
                if start_time <= now.time() <= end_time:
                    attendance_time = int(times.get('attendanceTime', 0))
                    # Return module_id here instead of module_info['name']
                    return module_id, attendance_time, end_time
    return None, 0, None


def mark_student_present(uuid, module_id):
    today_date = datetime.date.today().isoformat()
    # Ensure this fetches the correct module ID
    module_ref = db.reference(f"/modules/{module_id}")
    module_info = module_ref.get()
    if module_info:
        module_name = module_info.get("name", "Unknown Module")
        # Mark attendance with module name for readability
        attendance_ref = db.reference(f"/students/{uuid}/attendance/{today_date}")
        attendance_ref.set({module_id: f"{module_name}: present"})  # Changed to set for clarity
        print(f"Marked student {uuid} as present for {module_name} ({module_id}) on {today_date}")
    else:
        print(f"Module ID {module_id} not found.")



def calculate_and_update_total_students_present(today_date):
    modules_ref = db.reference("/modules")
    all_modules = modules_ref.get()
    # Mapping module names to IDs for the update operation
    name_to_id = {info.get("name"): mid for mid, info in all_modules.items()}
    total_present_per_name = {info.get("name"): 0 for mid, info in all_modules.items()}

    students_ref = db.reference("/students")
    all_students = students_ref.get()
    for uuid, student_info in all_students.items():
        attendance = student_info.get("attendance", {})
        attendance_record = attendance.get(today_date)

        # Check if attendance_record is a dictionary (new format)
        if isinstance(attendance_record, dict):
            for module_id, status_str in attendance_record.items():
                module_name, status = status_str.split(": ")
                if status.strip() == "present" and module_name in total_present_per_name:
                    total_present_per_name[module_name] += 1
        # Handle the string format (old format)
        elif isinstance(attendance_record, str):
            module_name, status = attendance_record.split(": ")
            if status.strip() == "present" and module_name in total_present_per_name:
                total_present_per_name[module_name] += 1

    # Update the totalStudentsPresent for each module by ID
    for module_name, total_present in total_present_per_name.items():
        module_id = name_to_id.get(module_name)
        if module_id:
            module_date_ref = db.reference(f"/modules/{module_id}/{today_date}")
            module_date_ref.update({"totalStudentsPresent": total_present})
            print(f"Updated {module_name} ({module_id}) with totalStudentsPresent: {total_present} on {today_date}")




def get_total_students_per_year():
    students_ref = db.reference("/students")
    all_students_data = students_ref.get()
    total_students_per_year = {}
    for _, student_info in all_students_data.items():
        if student_info:
            year = student_info.get('courseYear')
            if year:
                total_students_per_year[year] = total_students_per_year.get(year, 0) + 1
    return total_students_per_year

def update_module_student_totals(today_date):
    total_students_per_year = get_total_students_per_year()
    modules_ref = db.reference("/modules")
    all_modules_data = modules_ref.get()

    for module_id, module_info in all_modules_data.items():
        module_year = module_info.get('year')
        if module_year:
            total_students = total_students_per_year.get(module_year, 0)
            module_date_ref = db.reference(f"/modules/{module_id}/{today_date}")
            module_date_ref.update({"totalStudents": total_students})
            print(f"Updated {module_id} with total students: {total_students}")

def check_and_mark_attendance():
    now = datetime.datetime.now()
    student_devices = fetch_student_device_names()
    for device_name, connected_since in device_connection_times.items():
        if device_name in student_devices:
            uuid = student_devices[device_name]
            student_ref = db.reference(f"/students/{uuid}")
            student_info = student_ref.get()
            student_year = student_info.get('courseYear')
            module_id, attendance_time, class_end_time = get_current_class_and_end_time(student_year)  # Adjusted variable name
            if module_id:  # Adjusted condition
                min_duration = datetime.timedelta(minutes=attendance_time)
                if now - connected_since >= min_duration:
                    mark_student_present(uuid, module_id)  # Correct usage of module_id
                    device_connection_times[device_name] = now


def main():
    today_date = datetime.date.today().isoformat()
    while True:
        connected_devices = get_connected_devices()
        update_device_connection_times(connected_devices)
        check_and_mark_attendance()
        calculate_and_update_total_students_present(today_date)
        update_module_student_totals(today_date)
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
