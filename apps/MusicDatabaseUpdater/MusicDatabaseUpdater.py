import hassapi as hass
import lms_utils
import pymysql.cursors
import secrets

class MusicDatabaseUpdater(hass.Hass):

    def bootstrap_db_event(self, event_name, data, kwargs):
        self.bootstrap_db()

    def bootstrap_db(self):
        self.log("[bootstrap_db] Setting up the music database")
        conn = self.getDbConn(False)
        
        self.log("[bootstrap_db] Checking to see if a database called {} already exists".format(self.args["db"]))
        with conn.cursor() as cursor:
            cursor.execute('SHOW DATABASES')
            result = cursor.fetchall()
            
            if self.args['db'] not in [x[0] for x in result]:
                self.log("[bootstrap_db] Database {} does not exist. Creating it now".format(self.args['db']))
                cursor.execute('CREATE DATABASE {}'.format(self.args['db']))
            
        conn.commit()
        conn.close()
        
        self.log("[bootstrap_db] Setting up table {}".format(self.args["table"]))
        conn = self.getDbConn()
        with conn.cursor() as cursor:
            cursor.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(self.args['table'], ", ".join(self.args['table_columns'])))
            
            # Keep table definition up to date if it has already been created. Can alter existing columns and add new ones
            # New columns need to be added to the end of the list in the config
            self.log("[bootstrap_db] Checking table columns")
            cursor.execute('DESC {}'.format(self.args['table']))
            result = cursor.fetchall()
            for i, col in enumerate(result):
                if col[0] != self.args['table_columns'][i].split()[0]:
                    self.log("[bootstrap_db] Updating column {} to {}".format(col[0], self.args['table_columns'][i]))
                    cursor.execute('ALTER TABLE {} CHANGE {} {}'.format(self.args['table'], col[0], self.args['table_columns'][i]))
            if len(result) != len(self.args['table_columns']):
                for col in self.args['table_columns'][len(result):]:
                    self.log("[bootstrap_db] Adding column {}".format(col))
                    cursor.execute('ALTER TABLE {} ADD {}'.format(self.args['table'], col))
            
        conn.commit()
        conn.close()
        self.log("[bootstrap_db] Database bootstrap complete")
        
    def getDbConn(self, withDb = True):
        if withDb:
            return pymysql.connect(host=secrets.MUSIC_UPDATER_DB_HOST, user=secrets.MUSIC_UPDATER_DB_USER, password=secrets.MUSIC_UPDATER_DB_PASS, db=self.args['db'])
        else:
            return pymysql.connect(host=secrets.MUSIC_UPDATER_DB_HOST, user=secrets.MUSIC_UPDATER_DB_USER, password=secrets.MUSIC_UPDATER_DB_PASS)

    def initialize(self):
        self.rescan_check_interval = self.args.get('rescan_check_interval', 10)
    
        self.log("[initialize] Starting event listeners")
        self.bootstrap_event_listener = self.listen_event(self.bootstrap_db_event, self.args.get('bootstrap_db_event', 'BOOTSTRAP_DB'))
        self.rescan_event_listener = self.listen_event(self.rescan_event, self.args.get('rescan_event', 'RESCAN_LMS'))
        self.update_music_event_listener = self.listen_event(self.update_music_event, self.args.get('update_music_event', 'UPDATE_MUSIC_DB'))
        
        self.bootstrap_db()
        
        if 'daily_run_time' in self.args:
            self.log("[initialize] Scheduling a rescan daily at {}".format(self.args["daily_run_time"]))
            self.schedule_handle = self.run_daily(self.rescan, datetime.datetime.strptime(self.args['daily_run_time'], '%H:%M:%S').time())
            
        self.log("[initialize] Initial setup complete")
        
    def rescan(self, kwargs):
        if self.get_state(self.args["app_switch"]) == "on" or kwargs.get('bypass_app_switch', False):
            self.log("[rescan] Running rescan on LMS")
            lms_utils.rescan(secrets.MUSIC_UPDATER_LMS_HOST)
            self.run_in(self.rescan_check, self.rescan_check_interval, **kwargs)
            
    def rescan_check(self, kwargs):
        if lms_utils.rescan_finished(secrets.MUSIC_UPDATER_LMS_HOST):
            self.log("[rescan_check] LMS rescan complete")
            if kwargs.get('run_update_music', True):
                self.run_in(self.update_music, 0)
        else:
            self.log("[rescan_check] Waiting for LMS rescan to finish...sleeping {} seconds".format(self.rescan_check_interval))
            self.run_in(self.rescan_check, self.rescan_check_interval, **kwargs)
            
    def rescan_event(self, event_name, data, kwargs):
        self.run_in(self.rescan, 0, bypass_app_switch = True, run_update_music = False)
        
    def trackNeedsUpdated(self, db_info, lms_info):
        update = False
        for i, value in enumerate(db_info):
            if value != lms_info[i]:
                update = True
                break
        return update
    
    def update_music_event(self, event_name, data, kwargs):
        self.run_in(self.update_music, 0)
        
    def update_music(self, kwargs):
        self.log('[update_music] Updating music database')
        conn = self.getDbConn()
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, artist, album, title, genre, duration FROM {}'.format(self.args['table']))
            tracks_in_db = { row[0]: row[1:] for row in cursor.fetchall()} 
            
        tracks_in_lms = { x['id']: [x['artist'],x['album'],x['title'],x['genre'],x['duration']] for x in lms_utils.get_all_tracks(secrets.MUSIC_UPDATER_LMS_HOST) }
        
        update_query = 'UPDATE {} SET artist = %s, album = %s, title = %s, genre = %s, duration = %s WHERE id = %s'.format(self.args['table'])
        insert_query = 'INSERT INTO {} (artist, album, title, genre, duration, id) VALUES (%s, %s, %s, %s, %s, %s)'.format(self.args['table'])
        
        update_count = 0
        insert_count = 0
        
        with conn.cursor() as cursor:
            for id, info in tracks_in_lms.items():
                query_params = [info[0], info[1], info[2], info[3], info[4], id]
                if id in tracks_in_db:
                    if self.trackNeedsUpdated(tracks_in_db[id], info):
                        cursor.execute(update_query, query_params)
                        update_count += 1
                else:
                    try:
                        cursor.execute(insert_query, query_params)
                        insert_count += 1
                    except Exception as ex:
                        self.error("Could not insert row for {}".format(query_params))
        conn.commit()
        conn.close()
        self.log("[update_music] Update complete, {} records inserted, {} records updated".format(insert_count, update_count))
                
    def terminate(self):
        if hasattr(self, 'schedule_handle'):
            self.cancel_timer(self.schedule_handle)
        if hasattr(self, 'bootstrap_event_listener'):
            self.cancel_listen_event(self.bootstrap_event_listener)
        if hasattr(self, 'update_music_event_listener'):
            self.cancel_listen_event(self.update_music_event_listener)
        if hasattr(self, 'rescan_event_listener'):
            self.cancel_listen_event(self.rescan_event_listener)