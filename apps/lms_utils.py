import requests

def add_track(host, player, track_id):
    lms_request(host, [player, ["playlistcontrol", "cmd:add", "track_id:" + track_id]])

def get_all_tracks(host):
    total = lms_request(host, ["-",["info", "total", "songs", "?"]])['result']['_songs']
    return lms_request(host, ["-", ["titles", "0", total]])['result']['titles_loop']
    
def get_player_count(host):
    return lms_request(host, ["-", ["player", "count", "?"]])['result']['_count']
    
def get_players(host):
    players = {}
    for i in range(get_player_count(host)):
        name = lms_request(host, ["-", ["player", "name", i, "?"]])['result']['_name']
        players[name] = lms_request(host, ["-", ["player", "id", i, "?"]])['result']['_id']
    return players
    
def lms_request(host, params):
    r = requests.post(host, json={"id":1,"method":"slim.request","params":params})
    return r.json()
    
def rescan(host):
    lms_request(host, ["-", ["rescan"]])
    
def rescan_finished(host):
    return lms_request(host, ["-", ["rescan", "?"]])['result']['_rescan'] != 1