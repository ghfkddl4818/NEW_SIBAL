import time
import asyncio
from collections import deque

class RateLimiter:
    def __init__(self, rpm_soft, tpm_soft):
        self.rpm_limit = rpm_soft
        self.tpm_limit = tpm_soft
        self.requests = deque()
        self.tokens = deque()

    async def wait(self, estimated_tokens: int):
        current_time = time.time()

        while self.requests and self.requests[0] <= current_time - 60:
            self.requests.popleft()
            self.tokens.popleft()

        if len(self.requests) >= self.rpm_limit:
            sleep_time = self.requests[0] - (current_time - 60)
            await asyncio.sleep(sleep_time)
        
        total_tokens_in_window = sum(t for _, t in self.tokens)
        if total_tokens_in_window + estimated_tokens > self.tpm_limit:
            # This is a simplified wait, a more complex version would be needed
            await asyncio.sleep(5) # Simple wait, can be improved

        self.requests.append(current_time)
        self.tokens.append((current_time, estimated_tokens))

async def backoff_sleep(attempt: int, backoff_intervals: list):
    if attempt < len(backoff_intervals):
        sleep_time = backoff_intervals[attempt]
        await asyncio.sleep(sleep_time)
