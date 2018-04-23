import secrets
import string
from random import choice

from mongo_db_client import sport_together_db
import user_actions

games_db = sport_together_db("sport_together_game_details")

def check_mandatory_fields(game_info):
    for expected_key in ("type", "location", "game_owner_id"):
        if expected_key not in game_info.keys():
            raise KeyError(
                "Did not find `", expected_key, "` as a key in `game_info`"
            )

def add_game(game_info):
    """
    Add a game to the database of games.

    param(s):
    game_info (dict)    Expected keys: type, location, game_owner_id 

    return(s):
    (int) The id of the inserted game, or NoneType if the 
    game wasn't successfully inserted into the database.

    """

    check_mandatory_fields(game_info)

    # Get a unique ID for each game. This ID should be different from database ID
    alphabet = string.ascii_lowercase + string.digits
    while True:
        game_id = "".join(choice(alphabet) for i in range(10))
        if games_db.read({"game_id": game_id}) is None:
            break

    game_info["game_id"] = game_id
    game_info["html_version"] = _convert_game_info_to_html_row(game_info)
    
    insert_results = games_db.create(game_info)

    new_user_info = {
        "user_id": game_info["game_owner_id"],
        "games_owned": game_id
    }

    user_actions.update_user_append(new_user_info)
    
    if insert_results.inserted_id is not None:
        return game_id
    else:
        return None
    
def _convert_game_info_to_html_row(game_info):
    """
    Prepare a HTML-encoded version of each game for rendering.

    @param `game_info` (JSON): key-value pairs of containing info about the
    game.

    """

    check_mandatory_fields(game_info)

    return ''.join([
        "<tr><td>#", str(game_info["game_id"]), "</td>",
        "<td>", game_info["location"], "</td>",
        "<td>", game_info["type"], "</td>",
        "<td><button class='w3-btn w3-hover-white' onClick='return editgame(", 
        str(game_info["game_id"]), 
        ")'> <b><i class='fa fa-pencil fa-fw'></i></b></button></td><tr>"
    ])
    
def get_games(game_ids):
    """
    Get all the games using the supplied game IDs. Useful say when fetching
    all the games that a user is a part of.

    @param `game_ids` (Iterable): The IDs of the games to fetch.

    @returns (List): A list of JSON objects, each representing a game.

    """
    relevant_games = []
    for game_id in game_ids:
        game = games_db.read({"game_id": game_id})
        if game is not None:
            game.pop("_id", None)
            relevant_games.append(game)
    return relevant_games


def update_game_append(new_game_info):
    """
    Update specific fields in the game object. Useful when adding participants
    in an existing game. Prevents overwriting of existing information.

    @param `new_game_info` (JSON): key-value pairs of the info that needs to 
    be updated. The `game_id` key is mandatory.
    
    """

    if "game_id" not in new_game_info.keys():
        raise KeyError("`game_id` should be specified in the input.")

    game_id = new_game_info.pop("game_id", None)
    query = {"game_id": game_id}
    game_to_modify = games_db.read(query)
    
    for key in new_game_info:
        game_to_modify[key].append(new_game_info[key])

    game_to_modify["html_version"] = _convert_game_info_to_html_row(
        game_to_modify)
    return _helper_write_changes_to_db(game_to_modify)
        
def update_game(new_game_info):
    """
    Update specific fields in the game object. Useful when adding participants
    in an existing game. 

    @param `game_info` (JSON): key-value pairs of the info that needs to be
    updated. The `game_id` key is mandatory.

    @warning: If the key already exists in the game, the associated value will
    be overwritten!

    """

    if "game_id" not in new_game_info.keys():
        raise KeyError("`game_id` should be specified in the input.")
   
    game_to_modify = games_db.read({"game_id": new_game_info["game_id"]})
    for key in new_game_info:
        game_to_modify[key] = new_game_info[key]
    
    game_to_modify["html_version"] = _convert_game_info_to_html_row(game_to_modify)
    return _helper_write_changes_to_db(game_to_modify)
    

def _helper_write_changes_to_db(new_game_info):
    """

    Helper method for writing game information to the database.
    Used to avoid code duplication in `update_game` and 
    `update_game_append`.

    """
    update_results = {}
    result = games_db.update(
        {
            "game_id": new_game_info["game_id"]
        }, new_game_info
    )

    if result.modified_count == 1:
        update_results["game_info"] = new_game_info
    else:
        update_results["game_info"] = False

    return update_results

def main():    
    test_game = {
        'origin': 'Las Vegas', 
        'destination': 'Princeton University', 
        'departure_date': '2018-03-15', 
        'departure_time': '14:00', 
        'seats_available': '0', 
        'game_id': 4
    }
    # print(_convert_game_info_to_html_row(test_game))
    test_game["seats_available"] = 11
    print(update_game(test_game))

if __name__ == "__main__":
    main()
        