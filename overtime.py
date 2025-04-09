def calculate_overtime(self):
    """Process attendance_log to find overtime"""
    overtime_data = []
    for record in self.attendance_system.attendance_log:
        if record["Check-in"] and record["Check-out"]:
            total_hours = (datetime.strptime(record["Check-out"], "%H:%M:%S") - 
                         datetime.strptime(record["Check-in"], "%H:%M:%S")).seconds/3600
            if total_hours > 8:
                overtime_data.append({
                    "Name": record["Name"],
                    "Date": record["Date"],
                    "Regular": 8,
                    "Overtime": round(total_hours - 8, 1)
                })
    return overtime_data