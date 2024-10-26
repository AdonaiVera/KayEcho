import uuid
from datetime import datetime

class UserStateManager:
    def __init__(self, mongo_handler, user_id):
        self.mongo_handler = mongo_handler
        self.user_id = user_id
        self.collection = self.mongo_handler.db['user_states']

    def get_all_states(self):
        """Retrieve all states for the user and return them as a list."""
        states_cursor = self.collection.find(
            {"user_id": self.user_id}
        ) 

        # Convert cursor to a list of states
        states_list = list(states_cursor)
        return states_list

    def get_state(self):
        """Retrieve the current state for the user."""
        state = self.collection.find_one(
            {"user_id": self.user_id},
            sort=[("last_interaction", -1)] 
        )

        current_stage = "discover_user"
        if state:
            current_stage = state["current_stage"]

        new_state = {
            "user_id": self.user_id,
            "session_id": str(uuid.uuid4()),
            "current_stage": current_stage,
            "iterations": 0,
            "start_time": datetime.utcnow(),
            "last_interaction": datetime.utcnow(),
            "metadata": {
                "time_per_session": 0,
                "interaction_history": []
            }
        }
        self.collection.insert_one(new_state)
        
        return state, new_state


    def update_state(self, new_state):
        """Update the current state for the user."""
        new_state["last_interaction"] = datetime.utcnow()
        session_id = new_state["session_id"]
        interaction_time = datetime.utcnow()
        session_duration = (interaction_time - new_state["start_time"]).total_seconds()
        new_state["metadata"]["time_per_session"] = session_duration

        # Update the variable
        self.collection.update_one(
            {"user_id": self.user_id, "session_id": session_id},
            {"$set": new_state},
            upsert=True
        )