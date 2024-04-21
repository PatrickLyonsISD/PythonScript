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