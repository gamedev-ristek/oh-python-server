import asyncio
import websockets
import json
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any
import random
import signal
import sys

@dataclass
class UserResult:
    user_id: int
    connected: bool = False
    connection_time: float = 0.0
    execution_success: bool = False
    execution_time: float = 0.0
    error_message: str = ""
    websocket: Any = None
    session_id: str = ""
    actions_count: int = 0

class ConcurrentLoadTester:
    def __init__(self, server_url: str = "ws://127.0.0.1:8000/ws", target_users: int = 501):
        self.server_url = server_url
        self.target_users = target_users
        self.users: Dict[int, UserResult] = {}
        self.running = True
        
        self.complex_codes = [
            """
start_x, start_y = 0, 0
target_x, target_y = 10, 10
current_x, current_y = start_x, start_y

for step in range(50):
    if current_x < target_x:
        player.move_right(1)
        current_x += 1
    elif current_x > target_x:
        player.move_left(1)
        current_x -= 1
    
    if current_y < target_y:
        player.move_down(1)
        current_y += 1
    elif current_y > target_y:
        player.move_up(1)
        current_y -= 1
    
    if current_x == target_x and current_y == target_y:
        break

for i in range(5):
    player.move_up(1)
    player.move_right(1)
    player.move_down(1)
    player.move_left(1)
""",
            """
fib_sequence = [1, 1]
for i in range(2, 20):
    fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])

for i, fib_num in enumerate(fib_sequence):
    direction = i % 4
    steps = min(fib_num, 10)
    
    if direction == 0:
        for _ in range(steps):
            player.move_right(1)
    elif direction == 1:
        for _ in range(steps):
            player.move_down(1)
    elif direction == 2:
        for _ in range(steps):
            player.move_left(1)
    elif direction == 3:
        for _ in range(steps):
            player.move_up(1)

amplitude = 5
frequency = 0.5
for x in range(30):
    y = int(amplitude * (x * frequency) % 10)
    
    if y > 0:
        for _ in range(abs(y)):
            player.move_up(1)
    elif y < 0:
        for _ in range(abs(y)):
            player.move_down(1)
    
    player.move_right(1)

for outer in range(5):
    for middle in range(3):
        for inner in range(2):
            move_count = (outer * middle * inner) % 5 + 1
            direction_choice = (outer + middle + inner) % 4
            
            if direction_choice == 0:
                player.move_up(move_count)
            elif direction_choice == 1:
                player.move_right(move_count)
            elif direction_choice == 2:
                player.move_down(move_count)
            else:
                player.move_left(move_count)

for angle in range(0, 360, 30):
    radius = 3
    x_offset = int(radius * (angle / 180))
    y_offset = int(radius * (angle / 90))
    
    if x_offset > 0:
        player.move_right(abs(x_offset) % 10)
    elif x_offset < 0:
        player.move_left(abs(x_offset) % 10)
    
    if y_offset > 0:
        player.move_down(abs(y_offset) % 10)
    elif y_offset < 0:
        player.move_up(abs(y_offset) % 10)
""",
            """
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

prime_count = 0
for num in range(2, 100):
    if is_prime(num):
        prime_count += 1
        if num % 4 == 1:
            player.move_up(1)
        elif num % 4 == 3:
            player.move_right(1)
        elif num % 6 == 1:
            player.move_down(1)
        else:
            player.move_left(1)

matrix_size = 10
matrix_a = []
matrix_b = []

for i in range(matrix_size):
    row_a = []
    row_b = []
    for j in range(matrix_size):
        row_a.append((i + j) % 10)
        row_b.append((i * j) % 10)
    matrix_a.append(row_a)
    matrix_b.append(row_b)

result_matrix = []
for i in range(matrix_size):
    row = []
    for j in range(matrix_size):
        cell_sum = 0
        for k in range(matrix_size):
            cell_sum += matrix_a[i][k] * matrix_b[k][j]
        row.append(cell_sum)
        
        if cell_sum % 4 == 0:
            player.move_up(1)
        elif cell_sum % 4 == 1:
            player.move_right(1)
        elif cell_sum % 4 == 2:
            player.move_down(1)
        else:
            player.move_left(1)
    
    result_matrix.append(row)

numbers = list(range(50, 0, -1))

for i in range(len(numbers)):
    for j in range(0, len(numbers) - i - 1):
        if numbers[j] > numbers[j + 1]:
            numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]
            player.move_right(1)
        else:
            player.move_up(1)

factorial_sum = 0
for i in range(1, 10):
    factorial = 1
    for j in range(1, i + 1):
        factorial *= j
    factorial_sum += factorial
    
    moves = factorial % 20
    direction = i % 4
    
    for _ in range(moves):
        if direction == 0:
            player.move_up(1)
        elif direction == 1:
            player.move_right(1)
        elif direction == 2:
            player.move_down(1)
        else:
            player.move_left(1)
"""
        ]

    async def connect_user(self, user_id: int) -> UserResult:
        user = UserResult(user_id=user_id)
        
        try:
            connect_start = time.time()
            
            websocket = await websockets.connect(self.server_url)
            user.websocket = websocket
            user.connection_time = time.time() - connect_start
            
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=10)
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get("type") == "connected":
                user.connected = True
                user.session_id = welcome_data.get("session_id", "")
                print(f"✓ User {user_id} connected ({user.connection_time:.3f}s) - Session: {user.session_id}")
            else:
                user.error_message = "Invalid welcome message"
                
        except Exception as e:
            user.error_message = str(e)
            print(f"✗ User {user_id} connection failed: {e}")
            if hasattr(user, 'websocket') and user.websocket:
                await user.websocket.close()
                user.websocket = None
        
        return user

    async def execute_code_for_user(self, user: UserResult) -> None:
        if not user.connected or not user.websocket:
            user.error_message = "User not connected"
            return
        
        try:
            # randomize code choice
            code_to_execute = random.choice(self.complex_codes)
            exec_start = time.time()
            
            message = {
                "type": "execute_code",
                "code": code_to_execute
            }
            
            await user.websocket.send(json.dumps(message))
            
            response = await asyncio.wait_for(user.websocket.recv(), timeout=60)
            response_data = json.loads(response)
            
            user.execution_time = time.time() - exec_start
            
            if response_data.get("type") == "execution_result":
                data = response_data.get("data", {})
                user.execution_success = data.get("success", False)
                user.actions_count = len(data.get("actions", []))
                
                if user.execution_success:
                    print(f"✓ User {user.user_id} execution SUCCESS ({user.execution_time:.3f}s, {user.actions_count} actions)")
                else:
                    user.error_message = data.get("error", "Unknown execution error")
                    print(f"✗ User {user.user_id} execution FAILED: {user.error_message}")
            else:
                user.error_message = "Invalid response type"
                
        except asyncio.TimeoutError:
            user.error_message = "Execution timeout"
            print(f"✗ User {user.user_id} execution TIMEOUT")
        except Exception as e:
            user.error_message = str(e)
            print(f"✗ User {user.user_id} execution ERROR: {e}")

    async def cleanup_user(self, user: UserResult):
        if user.websocket:
            try:
                await user.websocket.close()
            except:
                pass

    async def execute_stage_for_all_users(self, connected_users: List[UserResult], stage_num: int) -> float:
        print(f"\n⚡ Stage {stage_num}: Executing code for {len(connected_users)} users simultaneously...")
        
        for user in connected_users:
            user.execution_success = False
            user.execution_time = 0.0
            user.actions_count = 0
            user.error_message = ""
        
        stage_start = time.time()
        
        execution_tasks = []
        for user in connected_users:
            task = asyncio.create_task(self.execute_code_for_user(user))
            execution_tasks.append(task)
        
        
        await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        stage_time = time.time() - stage_start
        
        



        successful = [u for u in connected_users if u.execution_success]
        failed = [u for u in connected_users if not u.execution_success]
        
        print(f"   ✓ Stage {stage_num} completed in {stage_time:.3f}s")
        print(f"   ✓ Successful: {len(successful)}/{len(connected_users)} ({len(successful)/len(connected_users)*100:.1f}%)")
        print(f"   ✗ Failed: {len(failed)}")
        
        if successful:
            avg_exec_time = statistics.mean([u.execution_time for u in successful])
            total_actions = sum([u.actions_count for u in successful])
            print(f"   📊 Avg execution time: {avg_exec_time:.3f}s")
            print(f"   📊 Total actions: {total_actions}")
        
        return stage_time

    async def run_concurrent_test(self):
        print(f"\n🚀 Starting 3-Stage Concurrent Load Test")
        print(f"Server: {self.server_url}")
        print(f"Target Users: {self.target_users}")
        print("="*60)
        
        print(f"\n📡 Phase 1: Connecting {self.target_users} users concurrently...")
        connect_start = time.time()
        
        connection_tasks = []
        for user_id in range(1, self.target_users + 1):
            task = asyncio.create_task(self.connect_user(user_id))
            connection_tasks.append(task)
        
        connection_results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        for i, result in enumerate(connection_results):
            if isinstance(result, Exception):
                user = UserResult(user_id=i+1)
                user.error_message = str(result)
                self.users[i+1] = user
            else:
                self.users[result.user_id] = result
        
        connect_time = time.time() - connect_start
        connected_users = [u for u in self.users.values() if u.connected]
        
        print(f"\n📊 Connection Results:")
        print(f"   Total Users: {self.target_users}")
        print(f"   Successfully Connected: {len(connected_users)} ({len(connected_users)/self.target_users*100:.1f}%)")
        print(f"   Connection Time: {connect_time:.3f}s")
        if connected_users:
            print(f"   Average Connection Time: {statistics.mean([u.connection_time for u in connected_users]):.3f}s")
        
        if len(connected_users) == 0:
            print("❌ No users connected successfully. Test aborted.")
            return
        
        print(f"\n⏳ Waiting 3 seconds for server stabilization...")
        await asyncio.sleep(3)
        
        print(f"\n🎯 Phase 2: 3-Stage Concurrent Execution")
        print(f"   Each stage: {len(connected_users)} users execute simultaneously")
        
        stage_times = []
        all_stage_results = []
        
        # 1
        stage1_time = await self.execute_stage_for_all_users(connected_users, 1)
        stage_times.append(stage1_time)
        stage1_results = [(u.user_id, u.execution_success, u.execution_time, u.actions_count) for u in connected_users]
        all_stage_results.append(stage1_results)
        
        print(f"\n⏳ Waiting 3 seconds before Stage 2...")
        await asyncio.sleep(3)
        
        # 2
        stage2_time = await self.execute_stage_for_all_users(connected_users, 2)
        stage_times.append(stage2_time)
        stage2_results = [(u.user_id, u.execution_success, u.execution_time, u.actions_count) for u in connected_users]
        all_stage_results.append(stage2_results)
        
        print(f"\n⏳ Waiting 3 seconds before Stage 3...")
        await asyncio.sleep(3)
        
        # 3
        stage3_time = await self.execute_stage_for_all_users(connected_users, 3)
        stage_times.append(stage3_time)
        stage3_results = [(u.user_id, u.execution_success, u.execution_time, u.actions_count) for u in connected_users]
        all_stage_results.append(stage3_results)
        
        print(f"\n⏳ Waiting 10 seconds before cleanup...")
        await asyncio.sleep(10)

        print(f"\n🧹 Phase 3: Cleaning up {len(connected_users)} connections...")
        cleanup_tasks = [asyncio.create_task(self.cleanup_user(user)) for user in self.users.values()]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self.print_3_stage_results(connect_time, stage_times, all_stage_results, connected_users)

    def print_3_stage_results(self, connect_time: float, stage_times: List[float], all_stage_results: List, connected_users: List[UserResult]):
        print(f"\n{'='*80}")
        print(f"🏁 3-STAGE CONCURRENT TEST RESULTS")
        print(f"{'='*80}")
        
        print(f"\n📈 Connection Phase:")
        print(f"   Target Users: {self.target_users}")
        print(f"   Connected Users: {len(connected_users)} ({len(connected_users)/self.target_users*100:.1f}%)")
        print(f"   Connection Time: {connect_time:.3f}s")
        
        if connected_users:
            connection_times = [u.connection_time for u in connected_users]
            print(f"   Average Connection Time: {statistics.mean(connection_times):.3f}s")
            print(f"   Min/Max Connection Time: {min(connection_times):.3f}s / {max(connection_times):.3f}s")
        
        print(f"\n⚡ Execution Stages Summary:")
        print(f"   Stage 1 Time: {stage_times[0]:.3f}s")
        print(f"   Stage 2 Time: {stage_times[1]:.3f}s") 
        print(f"   Stage 3 Time: {stage_times[2]:.3f}s")
        print(f"   Total Execution Time: {sum(stage_times):.3f}s")
        print(f"   Average Stage Time: {statistics.mean(stage_times):.3f}s")
        
        for stage_num, stage_results in enumerate(all_stage_results, 1):
            successful = [r for r in stage_results if r[1]]  # r[1] is execution_success
            failed = [r for r in stage_results if not r[1]]
            
            print(f"\n📊 Stage {stage_num} Details:")
            print(f"   Successful: {len(successful)}/{len(connected_users)} ({len(successful)/len(connected_users)*100:.1f}%)")
            print(f"   Failed: {len(failed)}")
            
            if successful:
                exec_times = [r[2] for r in successful]  # r[2] is execution_time
                action_counts = [r[3] for r in successful]  # r[3] is actions_count
                
                print(f"   Avg Execution Time: {statistics.mean(exec_times):.3f}s")
                print(f"   Min/Max Execution Time: {min(exec_times):.3f}s / {max(exec_times):.3f}s")
                print(f"   Total Actions: {sum(action_counts)}")
                print(f"   Avg Actions per User: {statistics.mean(action_counts):.1f}")
        
        all_successful = 0
        all_failed = 0
        all_exec_times = []
        all_actions = []
        
        for stage_results in all_stage_results:
            stage_successful = [r for r in stage_results if r[1]]
            stage_failed = [r for r in stage_results if not r[1]]
            all_successful += len(stage_successful)
            all_failed += len(stage_failed)
            all_exec_times.extend([r[2] for r in stage_successful])
            all_actions.extend([r[3] for r in stage_successful])
        
        total_operations = len(connected_users) * 3 
        success_rate = all_successful / total_operations if total_operations > 0 else 0
        
        print(f"\n🎯 Overall Performance:")
        print(f"   Total Operations: {total_operations} (3 stages × {len(connected_users)} users)")
        print(f"   Total Successful: {all_successful} ({success_rate*100:.1f}%)")
        print(f"   Total Failed: {all_failed}")
        
        if all_exec_times:
            print(f"   Overall Avg Execution Time: {statistics.mean(all_exec_times):.3f}s")
            print(f"   Overall Min/Max Execution Time: {min(all_exec_times):.3f}s / {max(all_exec_times):.3f}s")
            print(f"   Total Actions Generated: {sum(all_actions)}")
            print(f"   Actions per Second: {sum(all_actions)/sum(stage_times):.1f}")
        
        print(f"\n🎯 Performance Verdict:")
        if success_rate >= 0.95:
            print(f"   🟢 EXCELLENT - {success_rate*100:.1f}% success rate across all stages")
            print(f"   🟢 Server handled {len(connected_users)} concurrent users × 3 stages flawlessly!")
        elif success_rate >= 0.80:
            print(f"   🟡 GOOD - {success_rate*100:.1f}% success rate across all stages")
            print(f"   🟡 Server performed well under high concurrent load")
        elif success_rate >= 0.60:
            print(f"   🟠 FAIR - {success_rate*100:.1f}% success rate across all stages") 
            print(f"   🟠 Server struggled but handled most concurrent requests")
        else:
            print(f"   🔴 POOR - {success_rate*100:.1f}% success rate across all stages")
            print(f"   🔴 Server had difficulty handling {len(connected_users)} concurrent users")
        
        if sum(stage_times) > 0:
            throughput = total_operations / sum(stage_times)
            print(f"\n📈 Throughput Analysis:")
            print(f"   Operations per Second: {throughput:.1f}")
            print(f"   Concurrent Users Handled: {len(connected_users)}")
            print(f"   Peak Concurrent Operations: {len(connected_users)} simultaneous executions")
        
        print(f"{'='*80}")

    def signal_handler(self, signum, frame):
        print("\n🛑 Test interrupted by user")
        self.running = False

async def main():
    SERVER_URL = "ws://127.0.0.1:8000/ws"
    TARGET_USERS = 501
    
    print(f"🔥 High-Concurrency WebSocket Load Tester")
    print(f"Server: {SERVER_URL}")
    print(f"Target Users: {TARGET_USERS}")
    
    tester = ConcurrentLoadTester(SERVER_URL, TARGET_USERS)
    
    signal.signal(signal.SIGINT, tester.signal_handler)
    signal.signal(signal.SIGTERM, tester.signal_handler)
    
    try:
        await tester.run_concurrent_test()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())