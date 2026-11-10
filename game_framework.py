import time
running = False
stack = []


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False

frame_time = 0.0

def run(start_mode):
    global running, stack
    running = True
    stack = [start_mode]
    start_mode.init()

    global frame_time
    frame_time = 0.0
    current_time = time.perf_counter()

    while running:
        time.sleep(0.01)
        # 현재 갱신 직전까지 실제로 경과한 시간을 모든 객체가 공유한다.
        now = time.perf_counter()
        frame_time = now - current_time
        current_time = now
        stack[-1].handle_events()
        if not running:
            break
        stack[-1].update()
        stack[-1].render()
        
