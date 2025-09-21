# import asyncio
# import websockets
# import json
# import time
# import statistics
# from concurrent.futures import ThreadPoolExecutor
# import signal
# import sys
# from dataclasses import dataclass
# from typing import List, Dict, Any
# import random

# @dataclass
# class TestResult:
#     user_id: int
#     connection_time: float
#     execution_time: float
#     success: bool
#     error: str = ""
#     messages_sent: int = 0
#     messages_received: int = 0

# class WebSocketLoadTester:
#     def __init__(self, server_url: str = "ws://127.0.0.1:8000/ws", target_users: int = 300, test_duration: int = 60):
#         self.server_url = server_url
#         self.target_users = target_users
#         self.test_duration = test_duration
#         self.results: List[TestResult] = []
#         self.active_connections = 0
#         self.total_messages_sent = 0
#         self.total_messages_received = 0
#         self.start_time = None
#         self.running = True
        
#     async def simulate_user(self, user_id: int) -> TestResult:
#         result = TestResult(user_id=user_id, connection_time=0, execution_time=0, success=False)
        
#         try:
#             connect_start = time.time()
#             websocket = await websockets.connect(self.server_url)
            
#             try:
#                 result.connection_time = time.time() - connect_start
#                 self.active_connections += 1
                
#                 print(f"user {user_id} connected in {result.connection_time:.3f}s")
                
#                 welcome_task = asyncio.create_task(websocket.recv())
#                 welcome_msg = await asyncio.wait_for(welcome_task, timeout=5)
#                 welcome_data = json.loads(welcome_msg)
#                 result.messages_received += 1
                
#                 if welcome_data.get("type") == "connected":
#                     print(f"User {user_id} session established: {welcome_data.get('session_id')}")
                
#                 test_codes = [
#                     "player.move_up(1)",
                    
#                     """player.move_up(2)
#                     player.move_right(3)
#                     player.move_down(1)
#                     player.move_left(2)""",
                    
#                     """for i in range(3):
#                     player.move_up(1)
#                     player.move_right(1)""",
                    
#                     """steps = 3
#                     for i in range(steps):
#                         if i % 2 == 0:
#                             player.move_up(1)
#                         else:
#                             player.move_down(1)
#                     player.move_right(steps)""",
                    
#                     # error case
#                     "player.move_invalid(1)" if user_id % 50 == 0 else "player.move_up(1)"
#                 ]
                
#                 execution_count = random.randint(1, 3)
                
#                 for exec_num in range(execution_count):
#                     if not self.running:
#                         break
                        
#                     code_to_execute = random.choice(test_codes)
                    
#                     exec_start = time.time()
                    
#                     message = {
#                         "type": "execute_code",
#                         "code": code_to_execute
#                     }
                    
#                     await websocket.send(json.dumps(message))
#                     result.messages_sent += 1
#                     self.total_messages_sent += 1
                    
#                     try:
#                         response_task = asyncio.create_task(websocket.recv())
#                         response = await asyncio.wait_for(response_task, timeout=30)
#                         response_data = json.loads(response)
#                         result.messages_received += 1
#                         self.total_messages_received += 1
                        
#                         exec_time = time.time() - exec_start
#                         result.execution_time += exec_time
                        
#                         if response_data.get("type") == "execution_result":
#                             data = response_data.get("data", {})
#                             success = data.get("success", False)
                            
#                             if success:
#                                 actions = len(data.get("actions", []))
#                                 print(f"User {user_id} exec {exec_num+1}: SUCCESS "f"({exec_time:.3f}s, {actions} actions)")
#                             else:
#                                 error = data.get("error", "Unknown error")
#                                 print(f"User {user_id} exec {exec_num+1}: FAILED - {error}")
                                
#                     except asyncio.TimeoutError:
#                         print(f"User {user_id} exec {exec_num+1}: TIMEOUT")
#                         result.error += f"Timeout on execution {exec_num+1}; "
                    
#                     await asyncio.sleep(random.uniform(0.5, 2.0))
                
#                 result.success = True
                
#             finally:
#                 await websocket.close()
                
#         except Exception as e:
#             result.error = str(e)
#             result.success = False
#             print(f"User {user_id} ERROR: {e}")
            
#         finally:
#             self.active_connections -= 1
            
#         return result
    
#     async def ramp_up_test(self):
#         print(f"starting ramp-up test to {self.target_users} users")
        
#         batch_size = 10
#         ramp_delay = 3.0
        
#         tasks = []
        
#         for batch_start in range(0, self.target_users, batch_size):
#             if not self.running:
#                 break
                
#             batch_end = min(batch_start + batch_size, self.target_users)
#             batch_tasks = []
            
#             print(f"starting users {batch_start+1} to {batch_end}")
            
#             for user_id in range(batch_start, batch_end):
#                 task = asyncio.create_task(self.simulate_user(user_id))
#                 batch_tasks.append(task)
#                 tasks.append(task)
                
#                 await asyncio.sleep(0.2)
            
#             print(f"{batch_start//batch_size + 1} started. "f"active connections: {self.active_connections}")
            
#             if batch_end < self.target_users:
#                 await asyncio.sleep(ramp_delay)
        
#         print(f"all {self.target_users} users started. waiting for completion=====")
        
#         while tasks:
#             done_tasks = [task for task in tasks if task.done()]
            
#             for task in done_tasks:
#                 try:
#                     result = await task
#                     self.results.append(result)
#                 except Exception as e:
#                     print(f"task failed: {e}")
#                 tasks.remove(task)
            
#             if tasks:
#                 print(f"progress: {len(self.results)}/{self.target_users} users completed, "f"{self.active_connections} still active")
#                 await asyncio.sleep(5)
        
#         print("all users completed")
    
#     def print_results(self):
#         if not self.results:
#             print("no results")
#             return
            
#         successful_results = [r for r in self.results if r.success]
#         failed_results = [r for r in self.results if not r.success]
        
#         connection_times = [r.connection_time for r in successful_results]
#         execution_times = [r.execution_time for r in successful_results]
        
#         print("\n" + "="*80)
#         print("LOAD TEST RESULTS")
#         print("="*80)
        
#         print(f"Target Users: {self.target_users}")
#         print(f"Successful Connections: {len(successful_results)} ({len(successful_results)/self.target_users*100:.1f}%)")
#         print(f"Failed Connections: {len(failed_results)} ({len(failed_results)/self.target_users*100:.1f}%)")
        
#         if connection_times:
#             print(f"\nConnection Times:")
#             print(f"  Average: {statistics.mean(connection_times):.3f}s")
#             print(f"  Median:  {statistics.median(connection_times):.3f}s")
#             print(f"  Min:     {min(connection_times):.3f}s")
#             print(f"  Max:     {max(connection_times):.3f}s")
#             print(f"  95th percentile: {statistics.quantiles(connection_times, n=20)[18]:.3f}s")
        
#         if execution_times:
#             print(f"\nExecution Times (total per user):")
#             print(f"  Average: {statistics.mean(execution_times):.3f}s")
#             print(f"  Median:  {statistics.median(execution_times):.3f}s")
#             print(f"  Min:     {min(execution_times):.3f}s")
#             print(f"  Max:     {max(execution_times):.3f}s")
        
#         print(f"\nMessage Statistics:")
#         print(f"  Total Messages Sent: {self.total_messages_sent}")
#         print(f"  Total Messages Received: {self.total_messages_received}")
        
#         if failed_results:
#             print(f"\nFailure Analysis:")
#             error_counts = {}
#             for result in failed_results:
#                 error_key = result.error.split(':')[0] if result.error else "Unknown"
#                 error_counts[error_key] = error_counts.get(error_key, 0) + 1
            
#             for error, count in error_counts.items():
#                 print(f"  {error}: {count} occurrences")
        
#         print("="*80)
    
#     def signal_handler(self, signum, frame):
#         self.running = False

# async def main():
#     SERVER_URL = "ws://127.0.0.1:8000/ws"
#     TARGET_USERS = 300
    
#     print(f"WebSocket Load Tester")
#     print(f"Server: {SERVER_URL}")
#     print(f"Target Users: {TARGET_USERS}")
#     print("-" * 50)
    
#     tester = WebSocketLoadTester(SERVER_URL, TARGET_USERS)
    
#     signal.signal(signal.SIGINT, tester.signal_handler)
#     signal.signal(signal.SIGTERM, tester.signal_handler)
    
#     try:
#         await tester.ramp_up_test()
#         tester.print_results()
        
#     except KeyboardInterrupt:
#         tester.print_results()
#     except Exception as e:
#         print(f"test failed with error: {e}")
#         tester.print_results()

# if __name__ == "__main__":
#     required_modules = ['websockets', 'asyncio']
#     missing_modules = []
    
#     for module in required_modules:
#         try:
#             __import__(module)
#         except ImportError:
#             missing_modules.append(module)
    
#     asyncio.run(main())