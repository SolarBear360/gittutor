"""
==============================================
練習git用的程式，基本上不能跑或不正確
==============================================

main 分支版本

"""


import oa
import ob

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

version = 0.05
#這是主要分支

load_dotenv()

app = Flask(__name__)

# MySQL 連線設定
app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
    drivername="mysql+pymysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.environ["DB_NAME"],
    query={"charset": "utf8mb4"},
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 餐廳
class Restaurants(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    address = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
        }


# 餐點
class Meals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    # 外鍵：對應 restaurants 資料表的 id
    restaurant_id = db.Column(
        db.Integer,
        db.ForeignKey("restaurants.id"),
        nullable=False
    )

    price = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "restaurant_id": self.restaurant_id,
            "price": self.price,
        }


# 測試後端是否正常運作
@app.get("/")
def index():
    return jsonify({"message": "Flask API is running"})


# 查詢所有餐廳
@app.get("/api/restaurants")
def get_restaurants():
    users = db.session.execute(
        select(Restaurants).order_by(Restaurants.id)
    ).scalars().all()

    return jsonify([user.to_dict() for user in users])

# 查詢所有餐點
@app.get("/meals")
def get_meals():
    users = db.session.execute(
        select(Meals).order_by(Meals.id)
    ).scalars().all()

    return jsonify([user.to_dict() for user in users])

# 新增餐廳
@app.post("/restaurants")
def create_restaurant():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "請提供 JSON 物件"}), 400
    name = data.get("name")
    address = data.get("address")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name 不可為空"}), 400

    if not isinstance(address, str) or not address.strip():
        return jsonify({"error": "address 不可為空"}), 400

    restaurant = Restaurants(
        name = name.strip(),
        address = address.strip(),
    )

    db.session.add(restaurant)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "餐廳已存在"}), 409

    return jsonify(restaurant.to_dict()), 201

#新增餐點
@app.post("/meals")
def create_meal():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "請提供 JSON 物件"}), 400

    name = data.get("name")
    restaurant_id = data.get("restaurant_id")
    price = data.get("price")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name 不可為空"}), 400
    
    if not isinstance(restaurant_id, str) or not restaurant_id.strip():
        return jsonify({"error": "restaurant_id 不可為空"}), 400

    if not isinstance(price, str) or not price.strip():
        return jsonify({"error": "price 不可為空"}), 400

    meal = Meals(
        name = name.strip(),
        restaurant_id = restaurant_id.strip(),
        price = price.strip(),
    )

    db.session.add(meal)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "餐點已存在或restaurant_id不存在"}), 409

    return jsonify(meal.to_dict()), 201

# 刪除餐廳
@app.delete("/restaurants/<int:restaurant_id>")
def delete_restaurant(restaurant_id):
    restaurant = db.session.get(Restaurants, restaurant_id)

    if restaurant is None:
        return jsonify({"error": "無此餐廳id"}), 404

    db.session.delete(restaurant)
    db.session.commit()

    return jsonify({"message": "刪除成功"})

# 刪除餐點
@app.delete("/meals/<int:meal_id>")
def delete_meal(meal_id):
    meal = db.session.get(Meals, meal_id)

    if meal is None:
        return jsonify({"error": "無此餐點id"}), 404

    db.session.delete(meal)
    db.session.commit()

    return jsonify({"message": "刪除成功"})

#查詢餐廳所有餐點
@app.route("/api/restaurants/<string:restaurant_name>", methods=["GET"])
def get_restaurant_meals(restaurant_name):
    sql = text("""
        SELECT *
        FROM meals
        WHERE meals.restaurant_id = (
            SELECT id
            FROM restaurants
            WHERE restaurants.name = :restaurant_name
        )
    """)

    result = db.session.execute(
        sql,
        {"restaurant_name": restaurant_name}
    )

    meals = [dict(row) for row in result.mappings().all()]

    return jsonify(meals)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5000)