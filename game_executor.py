import sys
from io import StringIO
import traceback
import time

class Player:
    def __init__(self, executor):
        self.executor = executor
        self.position = {"x": 0, "y": 0}
        # self.reset_position = {"x": 0, "y": 0}
        
    def move_up(self, steps=1):
        if not isinstance(steps, int) or steps < 0:
            steps = 1
        
        old_pos = self.position.copy()
        self.position["y"] -= steps
        
        action = {
            "type": "move",
            "direction": "up",
            "steps": steps,
            "from": old_pos,
            "to": self.position.copy()
        }
        
        self.executor.add_action(action)
        # print(f"Moved up {steps} steps to ({self.position['x']}, {self.position['y']})")
        return f"Moved up {steps} steps"
    
    def move_down(self, steps=1):
        if not isinstance(steps, int) or steps < 0:
            steps = 1
        
        old_pos = self.position.copy()
        self.position["y"] += steps
        
        action = {
            "type": "move", 
            "direction": "down",
            "steps": steps,
            "from": old_pos,
            "to": self.position.copy()
        }
        
        self.executor.add_action(action)
        # print(f"Moved down {steps} steps to ({self.position['x']}, {self.position['y']})")
        return f"Moved down {steps} steps"
    
    def move_left(self, steps=1):
        if not isinstance(steps, int) or steps < 0:
            steps = 1
        
        old_pos = self.position.copy()
        self.position["x"] -= steps
        
        action = {
            "type": "move",
            "direction": "left", 
            "steps": steps,
            "from": old_pos,
            "to": self.position.copy()
        }
        
        self.executor.add_action(action)
        # print(f"Moved left {steps} steps to ({self.position['x']}, {self.position['y']})")
        return f"Moved left {steps} steps"
    
    def move_right(self, steps=1):
        if not isinstance(steps, int) or steps < 0:
            steps = 1
        
        old_pos = self.position.copy()
        self.position["x"] += steps
        
        action = {
            "type": "move",
            "direction": "right",
            "steps": steps, 
            "from": old_pos,
            "to": self.position.copy()
        }
        
        self.executor.add_action(action)
        # print(f"Moved right {steps} steps to ({self.position['x']}, {self.position['y']})")
        return f"Moved right {steps} steps"
    
    # def reset(self):
    #     self.position = self.reset_position.copy()
    #     action = {
    #         "type": "reset",
    #         "position": self.position.copy()
    #     }
    #     self.executor.add_action(action)
    #     print("reset to starting position")
    #     return "Player reset"

class GameExecutor:
    def __init__(self):
        self.player = Player(self)
        self.actions = []
        
    def add_action(self, action):
        self.actions.append(action)
        print(f"action added: {action}")
    
    # def reset(self):
    #     self.player.reset()
    #     self.actions.clear()
    
    async def execute_player_code(self, code: str) -> dict:
        print(f"executing:\n{code}")
        
        self.actions.clear()
        
        execution_result = {
            "success": True,
            "output": "",
            "error": "",
            "actions": [],
            "player_position": self.player.position.copy(),
            "execution_time": 0.0,
            "valid_commands": 0
        }
        
        old_stdout = sys.stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            start_time = time.time()
            
            safe_globals = {
                '__builtins__': {
                    # 'print': print,
                    'range': range,
                    'len': len,
                    'int': int,
                    'str': str,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'sum': sum,
                    'enumerate': enumerate,
                    'zip': zip,
                },
                'player': self.player
            }
            
            safe_locals = {}
            
            print("exec()")
            
            exec(code, safe_globals, safe_locals)
            
            execution_time = time.time() - start_time
            
            output = captured_output.getvalue()
            
            execution_result.update({
                "output": output,
                "actions": self.actions.copy(),
                "player_position": self.player.position.copy(),
                "execution_time": execution_time,
                "valid_commands": len(self.actions)
            })
            
            print(f"actions: {len(self.actions)}, output: {output}")
            
        except SyntaxError as e:
            print(f"Syntax Error: {e}")
            execution_result.update({
                "success": False,
                "error": f"Syntax Error: {str(e)}",
                "error_line": e.lineno - 1 if e.lineno else 0,
                "traceback": f"Line {e.lineno}: {e.text.strip() if e.text else ''}"
            })
            
        except Exception as e:
            print(f"Runtime Error: {e}")
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback_str = traceback.format_exc()
            
            execution_result.update({
                "success": False,
                "error": error_msg,
                "traceback": traceback_str
            })
            
        finally:
            sys.stdout = old_stdout
            
        print(f"execution result: {execution_result}")
        return execution_result