"""가짜 결제 서비스."""
from __future__ import annotations

import random


class FakePayment:
    def __init__(self, fail_mode: bool = False):
        self.fail_mode = fail_mode
        self._order_seq = random.randint(10, 80)

    def charge(self, amount: int) -> tuple[bool, int | None]:
        """결제 시도. (성공여부, 주문번호) 반환. 실패 시 주문번호 None."""
        if self.fail_mode:
            return False, None
        self._order_seq += 1
        return True, self._order_seq
