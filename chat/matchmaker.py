import redis
import uuid
from datetime import datetime
from django.http import JsonResponse

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def start_chat(request):
    """
    this function help for creating a session_id if not exist then create a one
    after session_id created then create a hashset data in redis for user details storage
    once all things are done now push that session id into redis queue and change the status
    
    """
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key

    redis_key = f"user:{session_id}"
    if not r.exists(redis_key):
        r.hset(redis_key, mapping={
            "status": "online",
            "room_id": "",
            "joined_at": datetime.utcnow().isoformat()
        })
    r.hset(redis_key, "status", "waiting")

    if session_id not in r.lrange("waiting_users", 0, -1):
        r.lpush("waiting_users", session_id)

    match_users()


    return JsonResponse({
        "message": f"User {session_id} added to waiting queue",
        "session_id": session_id
    })

def match_users():
    """ 
    main matching algo which checks the redis queue if user available match them otherwise return null
     """

    while r.llen("waiting_users")>=2:
        user1 = r.lpop("waiting_users")
        user2 = r.lpop("waiting_users")

        if not user1 and not user2:
            return

        room_id = str(uuid.uuid4())

        
        for user in [user1, user2]:
            r.hset(f"user:{user}", mapping={
                "status": "in_room",
                "room_id": room_id
            })

        print(f"Matched {user1} and {user2} in room {room_id}")


def leave_chat(request):
    """
    Ends the current chat for the user and notifies the partner.
    If no session exists, create one (like start_chat does).
    """
    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key

    redis_key = f"user:{session_id}"
    room_id = r.hget(redis_key, "room_id")

    if not room_id:
        return JsonResponse({"message": "No active room for this user"})

    partner_id = None
    for key in r.scan_iter(match="user:*"):
        if key != redis_key and r.hget(key, "room_id") == room_id:
            partner_id = key.split("user:")[1]
            r.hset(key, mapping={"status": "online", "room_id": ""})
            break
            
    r.hset(redis_key, mapping={"status": "online", "room_id": ""})

    return JsonResponse({
        "message": f"User {session_id} left the room",
        "partner_notified": bool(partner_id)
    })


    
    