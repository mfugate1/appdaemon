import requests

def add_track(host, player, track_id):
    lms_request(host, [player, ["playlistcontrol", "cmd:add", "track_id:" + track_id]])

def get_all_tracks(host):
    total = lms_request(host, ["-",["info", "total", "songs", "?"]])['result']['_songs']
    return lms_request(host, ["-", ["titles", "0", total]])['result']['titles_loop']
    
def lms_request(host, params):
    r = requests.post(host, json={"id":1,"method":"slim.request","params":params})
    return r.json()
    
def rescan(host):
    lms_request(host, ["-", ["rescan"]])
    
def rescan_finished(host):
    return lms_request(host, ["-", ["rescan", "?"]])['result']['_rescan'] != 1