from flask import Flask, jsonify, redirect , request , render_template
from flask_cors import CORS , cross_origin
import stripe
from datetime import datetime
from dotenv import load_dotenv
import os
import redis
import json
import requests

load_dotenv()



redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})

stripe.api_key = os.getenv("stripe_api_key")


@app.route('/api' , methods=["GET"])
def hello():
    return 'Payment Service!'

@app.route("/api/create_checkout-session" , methods=[ "POST"])
def checkout_session():
    data = request.get_json()
    print(data)
    unit_amount = int(float(data.get("price"))) * 100
    NAME= data.get("name")
    image = data.get("image")
    bookId = data.get("bookId")
    email = data.get("email")
    price = data.get("price")
    # adddressId = data.get("addressId")

    address_Body = {
        "firstName" : data.get("firstName"),
        "lastName" : data.get("lastName"),
        "postalCode" : data.get("postalCode"),
        "country" : data.get("country"),
        "state" : data.get("state"),
        "city" : data.get("city"),
        "phoneNumber" : data.get("phoneNumber"),
        "email" : data.get("email"),
        "addressLine1" : data.get("addressLine1"),
        "addressLine2" : data.get("addressLine2"),

    }
    headers = {
    'Content-Type': 'application/json'
    }

    
    addressResponse = requests.post("http://localhost:8080/api/address",json=address_Body, headers=headers)
    address_Data = addressResponse.json()
    print(address_Data)

    p = f"&book_id={bookId}&price={price}&address_id={address_Data['id']}&title={NAME}"
 
    checkout_session = stripe.checkout.Session.create(
        customer_email=email,
        billing_address_collection="auto",
        line_items=[
            {
                "price_data": {
                    "currency": "inr",
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": NAME,
                        "images" : [image]
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://127.0.0.1:4242/payment/success?session_id={CHECKOUT_SESSION_ID}" + p,
        cancel_url="http://127.0.0.1:4242/payment/failed",
    )
    Stripe_URL = jsonify({"url": checkout_session.url})
    print(Stripe_URL)
    Stripe_URL.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return Stripe_URL

@app.route('/payment/success', methods=['GET'])
def payment_success():

    print("Payment successful",request.args)
    session_id = request.args.get("session_id")
    title = request.args.get("title")
    bookId = request.args.get("book_id")
    price = request.args.get("price")
    addressId = request.args.get("address_id")
    print(session_id, title, bookId, price, addressId)

     # creating order
    order_Payload = {
        "status" : "PENDING"
    }
    headers = {
    'Content-Type': 'application/json'
    }

    
    orderResponse = requests.post("http://localhost:8080/api/orders",json=order_Payload, headers=headers)
    order_Data = orderResponse.json()
    print(order_Data)


    # Creating orderItem
    orderItem_Body = {
        "bookId" : bookId,
        "quantity" : 1,
        "price" : price
    }

    orderItem_Params = {
        "orderId" : order_Data['id']
    }

    orderItemReponse = requests.post("http://localhost:8080/api/orderItem",json=orderItem_Body, params=orderItem_Params ,headers=headers)
    orderItem_Data = orderItemReponse.json()
    print(orderItem_Data)

    # Creating Shipping

    shipping_Params = {
        'orderId' : order_Data['id'],
        'addressId' : addressId
    }
    shipping_Body = {
        'ShippingMethod' : "STANDARD"
    }

    shippingReponse = requests.post("http://localhost:8080/api/shipping", json=shipping_Body, params=shipping_Params ,headers=headers)
    shipping_Data = shippingReponse.json()
    print(shipping_Data)






    checkout_session = stripe.checkout.Session.retrieve(session_id)
    # print(checkout_session)

    email = checkout_session.get('customer_email')
    status = checkout_session.get('status')
    customer_details = checkout_session.get("customer_details")
    print(customer_details)
    id = checkout_session.get('id')
    total_amount = float(checkout_session.get('amount_total')) / 100
    timestamp = checkout_session.get("created")

    payment_Params ={
        'orderId' : order_Data['id']
    }

    payment_Body = {
        'stripePaymentId' : session_id,
        'paymentMethod' : "CARD",
        'amount' : total_amount
    }

    paymentReponse = requests.post("http://localhost:8080/api/payment", json=payment_Body, params=payment_Params ,headers=headers)
    payment_Data = paymentReponse.json()
    print(payment_Data)



    # Convert Unix timestamp to datetime object
    dt_object = datetime.fromtimestamp(timestamp)

    # Format datetime object to a readable string
    formatted_time = dt_object.strftime("%A, %B %d, %Y")


    print(email,status)
    print(customer_details.name)
    data = {
        "email" : email,
        "status" : status,
        "orderId" : id,
        "price" : total_amount,
        # "title" : title,
        "purchaseDate" : formatted_time,
        "subject" : "Order confirmation",
        "name" : customer_details.name
    }

    message = json.dumps(data)
    redis_client.lpush("message_queue",message)

    

    return render_template("success.html", email=email ,title=title, status=status , id=id , formatted_time=formatted_time , total_amount=total_amount)




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
    print("Running Server on port 4242")
    app.run(port=4242)