from flask_restful import Resource
from flask import request, make_response, render_template
from hmac import compare_digest
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    get_jwt,
)
from models.user import UserModel
from schemas.user import UserSchema
from blocklist import BLOCKLIST
import traceback
from libs.mailgun import MailGunException
from models.confirmation import ConfirmationModel

USER_ALREADY_EXISTS = "A user with that username already exists."
EMAIL_ALREADY_EXISTS = "A user wiht email already exists."
CREATED_SUCCESSFULLY = "User created successfully."
USER_NOT_FOUND = "User not found."
USER_DELETED = "User deleted."
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "User <id={user_id}> successfully logged out."
NOT_CONFIRMED_ERROR="You have not confirmed registration, please check your email <{}>."
USER_CONFIMED="User confirmed."
FAILED_TO_CREATE="Internal server error. Failed to create user."
SUCCESS_REGISTER_MESSAGE="Account created succefully, an email with an activation link has been sent to your email address, please check"

user_schema=UserSchema()

class UserRegister(Resource):
    @classmethod
    def post(cls):
        user = user_schema.load(request.get_json())

        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXISTS}, 400
        
        if UserModel.find_by_email(user.email):
            return {"message": EMAIL_ALREADY_EXISTS}, 400

        try:
            user.save_to_db() #1
            confirmation=ConfirmationModel(user,id)#2
            confirmation.save_to_db() #3 
            user.send_confirmation_email() #4
            return {"message":SUCCESS_REGISTER_MESSAGE}, 201
        
        except MailGunException as e:
            # [#4] problem happen when sending confirmatin email -> not to save in the database
            user.delete_form_db()
            # message change to string
            return {"message":str(e)}, 500
        
        except:
            # [#1,2,3] data base fail. if falied to save user to db -> not to save in the database
            traceback.print_exc()
            user.delete_from_db()
            return {"message":FAILED_TO_CREATE}, 500


class User(Resource):
    """
    This resource can be useful when testing our Flask app. We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful when we are manipulating data regarding the users.
    """

    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        user.delete_from_db()
        return {"message": USER_DELETED}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        user_data = user_schema.load(request.get_json(), partial=("email",))
        
        user = UserModel.find_by_username(user_data.username)

        # this is what the `authenticate()` function did in security.py
        if user and compare_digest(user.password, user_data.password):
            confirmation=user.most_recent_confirmation
            if confirmation and confirmation.confirmed:
                # identity= is what the identity() function did in security.py—now stored in the JWT
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            return {"message":NOT_CONFIRMED_ERROR.format(user.username)},400

        return {"message": INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        jti = get_jwt()["jti"]  # jti is "JWT ID", a unique identifier for a JWT.
        user_id = get_jwt_identity()
        BLOCKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_required(refresh=True)
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200


