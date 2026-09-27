import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def create_checkout_session(course, user, success_url, cancel_url):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": course.title},
                "unit_amount": int(course.price * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=user.email,
        metadata={"course_id": str(course.id), "user_id": str(user.id)},
    )
    return session