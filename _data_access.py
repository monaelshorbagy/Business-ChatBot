from data_access import DataAccess

data_access= DataAccess()

# data_access Functions:
# user:
# register_user
# login_user
# check_user_balance
# increment_user_usage
# request_quota
# reset_usage
#
# sessions:
# add_new_session
# set_total_cost
# end_session
#
# messages:
# add_new_message






users_data = [
    ("eng.talat", "eng.talat123"),
    ("eng.mona", "eng.mona123"),
    ("eng.jessica", "eng.jessica123"),
    ("eng.moamen", "eng.moamen123"),
    ("product.owner", "product.owner990"),
    ("scrum1", "scrum1ahbs199"),
    ("scrum2", "scrum2ahbs299"),
    ("scrum3", "scrum3ahbs399"),
    ("scrum4", "scrum4ahbs499"),
    ("rnd", "rnd1ahbs199"),
]

# Register each user
for username, password in users_data:
    user_id = data_access.register_user(username,password) # Sucess return user_id, Faild return 0
    print(f"User {username} registered with user_id: {user_id}")