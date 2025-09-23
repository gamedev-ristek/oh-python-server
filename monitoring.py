import time
import requests
import psutil
import os
from datetime import datetime

class SimpleMonitor:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8000"
        self.monitoring = True
    
    def get_python_process(self):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'main.py' in cmdline:
                        return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def get_server_stats(self):
        try:
            response = requests.get(f"{self.server_url}/", timeout=2)
            if response.status_code == 200:
                return {"status": "running", "response_time": response.elapsed.total_seconds()}
        except Exception as e:
            return {"status": "error", "error": str(e)}
        return {"status": "unknown"}
    
    def format_bytes(self, bytes_val):
        # format bytes -> readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} TB"
    
    def monitor_simple(self):
        print("monitoring server at", self.server_url)
        print("-" * 50)
        
        while self.monitoring:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # system stats
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                # process stats
                server_proc = self.get_python_process()
                if server_proc:
                    try:
                        proc_cpu = server_proc.cpu_percent()
                        proc_memory = server_proc.memory_info()
                        proc_status = f"CPU: {proc_cpu:.1f}% RAM: {self.format_bytes(proc_memory.rss)}"
                    except:
                        proc_status = "process unavailable"
                else:
                    proc_status = "server not found"
                
                server_stats = self.get_server_stats()
                server_status = server_stats.get("status", "unknown")
                
                print(f"{timestamp} | CPU: {cpu:5.1f}% | "f"RAM: {memory.percent:5.1f}% | "f"Server: {server_status:10} | "f"Process: {proc_status}")
                
                time.sleep(3)
                
            except KeyboardInterrupt:
                print("\nstopped")
                self.monitoring = False
                break
            except Exception as e:
                print(f"error: {e}")
                time.sleep(5)

def main():
    monitor = SimpleMonitor()
    monitor.monitor_simple()

if __name__ == "__main__":
    main()