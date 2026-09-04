import razorpay

# Oops - developer hardcoded the live key instead of using env vars!
client = razorpay.Client(auth=("rzp_live_HARDCODED_KEY_1234567", "secret_hardcoded_abc123xyz"))

def process_payment(amount):
    return client.payment.create({"amount": amount, "currency": "INR"})
