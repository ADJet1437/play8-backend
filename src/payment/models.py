from pydantic import BaseModel


class CreatePaymentIntentRequest(BaseModel):
    machine_id: str
    start_time: str
    end_time: str


class PaymentIntentResponse(BaseModel):
    booking_id: str
    client_secret: str
    amount: int       # in öre
    amount_sek: float  # display amount in SEK


class RefundResponse(BaseModel):
    booking_id: str
    status: str
    message: str


class VerifyPaymentRequest(BaseModel):
    payment_intent_id: str


class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    stripe_payment_intent_id: str
    amount: int
    currency: str
    status: str
