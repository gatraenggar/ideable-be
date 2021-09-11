
class ModelMapper():
    def to_user_list(user_models):
        userList = []
        for user in user_models:
            userList.append({
                "uuid": user["uuid"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "first_name": user["first_name"],
                "is_confirmed": user["is_confirmed"],
                "created_at": user["created_at"],
            })

        return userList

    def to_single_user(user_model):
        user = user_model[0]
        return {
            "uuid": user["uuid"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "first_name": user["first_name"],
            "is_confirmed": user["is_confirmed"],
            "created_at": user["created_at"],
        }
