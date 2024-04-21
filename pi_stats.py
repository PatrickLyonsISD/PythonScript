"""
Pi System Stats Collection Script

This script runs on a Raspberry Pi and interfaces with Firebase to track and store the Pi device's system statistics.
It is designed to periodically gather system performance metrics such as CPU usage, memory utilization, disk usage,
and a timestamp indicating the last update. These metrics are then sent to Firebase, ensuring that device performance
can be monitored remotely in real-time.

Key Functionalities:
1. System Statistics Gathering: Utilizes the 'psutil' library to access system performance data, capturing 
   current CPU percentage, memory usage, disk usage, and the exact time of the data snapshot.
2. Firebase Integration: Initializes a connection to Firebase using the Firebase Admin SDK, where it updates the 
   'pi_stats' node with the latest system statistics.
3. Scheduled Updates: Designed to run as a recurring task, the script collects and updates the performance data at 
   regular intervals (as determined by the deployment setup), ensuring ongoing monitoring.
"""
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import psutil
from datetime import datetime
# Initialize Firebase Admin SDK
cred = credentials.Certificate('/home/salmon/Downloads/final-year-project-1.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://final-year-project-1-cbc96-default-rtdb.firebaseio.com'
})
# Function to get system stats including last seen
def get_system_stats():
    stats = {
        'cpu': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return stats

# Function to update Firebase
def update_firebase(stats):
    ref = db.reference('/pi_stats')
    ref.set(stats)

if __name__ == '__main__':
    stats = get_system_stats()
    update_firebase(stats)
    print("Updated Firebase with:", stats)
