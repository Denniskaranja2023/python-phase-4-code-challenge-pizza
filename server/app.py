#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class RestaurantResource(Resource):
    def get(self):
        restaurants= Restaurant.query.all()
        restaurants_list= [restaurant.to_dict(rules=('-restaurant_pizzas','-pizzas',)) for restaurant in restaurants]
        return make_response(restaurants_list, 200)

api.add_resource(RestaurantResource, '/restaurants')

class RestaurantById(Resource):
    def get(self, id):
        restaurant= Restaurant.query.filter_by(id=id).first()
        if restaurant:
            return make_response(restaurant.to_dict(rules=('-pizzas',)), 200)
        else:
            return make_response({"error": "Restaurant not found"}, 404)
    def delete(self, id):
        restaurant= Restaurant.query.filter_by(id=id).first()
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return make_response({}, 204)
        else:
            return make_response({"error": "Restaurant not found"}, 404)       
api.add_resource(RestaurantById, '/restaurants/<int:id>')

class PizzaResource(Resource):
    def get(self):
        pizzas= Pizza.query.all()
        pizzas_list= [pizza.to_dict(rules=('-resturants','-restaurant_pizzas',)) for pizza in pizzas]
        return make_response(pizzas_list, 200)
api.add_resource(PizzaResource, '/pizzas')

class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()

        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")
        price = data.get("price")

        pizza = Pizza.query.filter_by(id=pizza_id).first()
        restaurant = Restaurant.query.filter_by(id=restaurant_id).first()

        # check existence of pizza and restaurant
        if not pizza or not restaurant:
            return make_response({"errors": ["validation errors"]}, 400)

        try:
            new_restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )
            db.session.add(new_restaurant_pizza)
            db.session.commit()
        except ValueError:
            return make_response({"errors": ["validation errors"]}, 400)

        # Build the response including nested pizza and restaurant
        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": new_restaurant_pizza.pizza.to_dict(
                rules=('-restaurant_pizzas',)
            ),
            "restaurant": new_restaurant_pizza.restaurant.to_dict(
                rules=('-restaurant_pizzas', '-pizzas',)
            ),
        }

        return make_response(response_data, 201)

api.add_resource(RestaurantPizzasResource, '/restaurant_pizzas')
if __name__ == "__main__":
    app.run(port=5555, debug=True)
