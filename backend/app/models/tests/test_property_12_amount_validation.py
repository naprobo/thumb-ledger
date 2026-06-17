# Feature: mobile-bookkeeping-app, Property 12: 非数字金额被拒绝
"""
属性测试：Property 12 — 非数字金额被拒绝

对于任何提交了非数字或非整数金额的交易创建请求，
Transaction_Service 应返回 422 Unprocessable Entity 错误。

Validates: Requirements 8.3
"""
import uuid
from datetime import date
from typing import Annotated, Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError, field_validator
from pydantic import ConfigDict


# ---------------------------------------------------------------------------
# Pydantic Schema（简化版，模拟实际 Transaction 创建时的验证逻辑）
# 在完整路由实现前，此 Schema 用于验证金额字段约束的正确性。
# ---------------------------------------------------------------------------

class TransactionCreateSchema(BaseModel):
    """
    交易创建请求体的最小验证 Schema，专注于金额字段约束。

    使用 strict 模式：
    - 不接受浮点数（如 1.0）自动转换为整数
    - 不接受布尔值（bool 是 int 的子类，但语义上不合法）
    - 不接受非数字字符串
    """

    model_config = ConfigDict(strict=True)

    ledger_id: uuid.UUID
    amount: int  # strict 模式下：仅接受真正的 int 类型
    currency_code: str
    transaction_date: date

    @field_validator("amount", mode="after")
    @classmethod
    def amount_must_be_positive_integer(cls, v: Any) -> int:
        """
        金额字段约束：
        - strict 模式已拒绝非 int 类型（float、str、bool）
        - 此处额外验证必须为正数（> 0）
        """
        if v <= 0:
            raise ValueError("amount must be a positive integer")
        return v


# ---------------------------------------------------------------------------
# 正例：有效整数金额应被接受
# ---------------------------------------------------------------------------

@given(amount=st.integers(min_value=1, max_value=10_000_000_000))
@settings(max_examples=100)
def test_valid_integer_amount_accepted(amount: int) -> None:
    """
    **Validates: Requirements 8.3**

    对于任意正整数金额，Schema 应接受该值而不抛出异常。
    """
    schema = TransactionCreateSchema(
        ledger_id=uuid.uuid4(),
        amount=amount,
        currency_code="JPY",
        transaction_date=date.today(),
    )
    assert schema.amount == amount


# ---------------------------------------------------------------------------
# 反例：零或负整数应被拒绝
# ---------------------------------------------------------------------------

@given(amount=st.integers(max_value=0))
@settings(max_examples=100)
def test_zero_or_negative_amount_rejected(amount: int) -> None:
    """
    **Validates: Requirements 8.3**

    对于零或负整数金额，Schema 应抛出 ValidationError。
    """
    with pytest.raises(ValidationError):
        TransactionCreateSchema(
            ledger_id=uuid.uuid4(),
            amount=amount,
            currency_code="JPY",
            transaction_date=date.today(),
        )


# ---------------------------------------------------------------------------
# 反例：非数字字符串应被拒绝
# ---------------------------------------------------------------------------

@given(
    amount=st.text(
        alphabet=st.characters(
            blacklist_categories=("Nd",),  # 排除 Unicode 数字字符
            blacklist_characters="0123456789",
        ),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_non_numeric_string_amount_rejected(amount: str) -> None:
    """
    **Validates: Requirements 8.3**

    对于任意非数字字符串金额，Schema 应抛出 ValidationError。
    """
    with pytest.raises(ValidationError):
        TransactionCreateSchema(
            ledger_id=uuid.uuid4(),
            amount=amount,  # type: ignore[arg-type]
            currency_code="JPY",
            transaction_date=date.today(),
        )


# ---------------------------------------------------------------------------
# 反例：浮点数应被拒绝（不是整数类型）
# ---------------------------------------------------------------------------

@given(
    amount=st.floats(
        min_value=-1e9,
        max_value=1e9,
        allow_nan=False,
        allow_infinity=False,
    )
)
@settings(max_examples=100)
def test_float_amount_rejected(amount: float) -> None:
    """
    **Validates: Requirements 8.3**

    对于任意浮点数金额（包括 1.0 这种整数浮点数），Schema 应抛出 ValidationError。
    浮点数即使值是整数（如 100.0），也不被接受，因为类型严格匹配整数。
    """
    with pytest.raises(ValidationError):
        TransactionCreateSchema(
            ledger_id=uuid.uuid4(),
            amount=amount,  # type: ignore[arg-type]
            currency_code="JPY",
            transaction_date=date.today(),
        )


# ---------------------------------------------------------------------------
# 反例：布尔值应被拒绝（bool 是 int 的子类，但语义上不合法）
# ---------------------------------------------------------------------------

@given(amount=st.booleans())
@settings(max_examples=100)
def test_boolean_amount_rejected(amount: bool) -> None:
    """
    **Validates: Requirements 8.3**

    对于布尔值金额（True/False），Schema 应抛出 ValidationError。
    虽然 Python 中 bool 是 int 的子类，但金额字段不应接受布尔值。
    """
    with pytest.raises(ValidationError):
        TransactionCreateSchema(
            ledger_id=uuid.uuid4(),
            amount=amount,  # type: ignore[arg-type]
            currency_code="JPY",
            transaction_date=date.today(),
        )


# ---------------------------------------------------------------------------
# 反例：None 应被拒绝
# ---------------------------------------------------------------------------

def test_none_amount_rejected() -> None:
    """
    **Validates: Requirements 8.3**

    对于 None 金额，Schema 应抛出 ValidationError（amount 字段为必填项）。
    """
    with pytest.raises(ValidationError):
        TransactionCreateSchema(
            ledger_id=uuid.uuid4(),
            amount=None,  # type: ignore[arg-type]
            currency_code="JPY",
            transaction_date=date.today(),
        )
