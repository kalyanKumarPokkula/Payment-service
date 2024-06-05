from flask import Flask, jsonify, redirect , request , render_template
from flask_cors import CORS , cross_origin
import stripe
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

stripe.api_key = os.getenv("stripe_api_key")


@app.route('/')
def hello():
    return 'Hello, World!'

@app.route("/create_checkout-session" , methods=[ "POST"])

def checkout_session():
    data = request.get_json()
    print(data)
    unit_amount = int(float(data.get("price"))) * 100
    name = data.get("name")
    image = data.get("image")
    checkout_session = stripe.checkout.Session.create(
        customer_email="test@example.com",
        billing_address_collection="auto",
        line_items=[
            {
                "price_data": {
                    "currency": "inr",
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": name,
                        "images" : [image]
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://127.0.0.1:4242/payment/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://127.0.0.1:4242/payment/failed",
    )
    response = jsonify({"url": checkout_session.url})
    print(response)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.route('/payment/success', methods=['GET'])
def payment_success():
    print("Payment successful")
    session_id = request.args.get("session_id");
    print(session_id)

    checkout_session = stripe.checkout.Session.retrieve(session_id)
    print(checkout_session)

    email = checkout_session.get('customer_email')
    status = checkout_session.get('status')
    id = checkout_session.get('id')
    total_amount = float(checkout_session.get('amount_total')) / 100
    timestamp = checkout_session.get("created")

    # Convert Unix timestamp to datetime object
    dt_object = datetime.fromtimestamp(timestamp)

    # Format datetime object to a readable string
    formatted_time = dt_object.strftime("%A, %B %d, %Y")


    print(email,status)

    return render_template("success.html", email=email , status=status , id=id , formatted_time=formatted_time , total_amount=total_amount)




    # return jsonify({"status" : status, "message" : "payment successful", "data" : { "email" : email }} ,201)

@app.route('/payment/failure', methods=['GET'])
def payment_failed():
    print("Payment failed..")

    return jsonify({"status" : "success", "message" : "payment failed"} ,201)

@app.route('/redirect_to_bookstore')
def redirect_to_bookstore():
    # Replace with the URL of your Node.js server
    return redirect("http://localhost:5173")

if __name__ == '__main__':
    app.run(port=4242)