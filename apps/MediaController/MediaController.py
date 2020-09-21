import hassapi as hass

class MediaController(hass.Hass):

    def initialize(self):
        self.event_listener = self.listen_event(self.media_controller_command, self.args['event'])
        
    def terminate(self):
        if hasattr(self, 'event_listener'):
            self.cancel_listen_event(self.event_listener)
        
    def media_controller_command(self, event_name, data, kwargs):
        if 'room' in data:
            room = data['room']
        else:
            room = self.get_state(self.args['last_called_room_entity'], copy = False)
            
        if not room:
            self.log("[media_controller_command] No room given or found with alexa last_called")
            return

        if 'source' not in data:
            self.log("[media_controller_command] Missing source, nothing to do!")
            return

        if room not in self.args['rooms']:
            self.log("[media_controller_command] A room called {} is not defined in the configuration".format(room))
            return
            
        source = data['source']
        room_info = self.args['rooms'][room]
            
        if source not in room_info['sources']:
            self.log("[media_controller_command] {} is not a source in {}".format(source, room))
            self.call_service('notify/alexa_media', target = self.get_state(self.args['last_called_device_entity'], copy = False), data = {'type': 'tts'}, message = "{} is not a source in {}".format(source, room))
            return
        
        self.log("[media_controller_command] Room = {}, Source = {}".format(room, data['source']))
        
        source_info = room_info['sources'][source]
        
        if 'receiver_source' in source_info:
            self.run_in(self.media_player_on, 0, entity_id = room_info['receiver'], source = source_info['receiver_source'])
            
        if 'tv_source' in source_info:
            self.run_in(self.media_player_on, 0, entity_id = room_info['tv'], source = source_info['tv_source'])
            
        if 'media' in source_info:
            media = source_info['media']
            delay = 0
            if 'delay' in media:
                delay = media['delay']
                self.log("[media_controller_command] Delay for service call set to {}".format(delay))
                
            self.run_in(self.media_call_service, delay, media = media)

    def media_player_on(self, kwargs):
        if self.get_state(kwargs['entity_id']) == 'off':
            self.log("[media_player_on] Turning on {}".format(kwargs['entity_id']))
            self.turn_on(kwargs['entity_id'])
            self.listen_state(self.media_player_state_on, kwargs['entity_id'], new = 'on', duration = 0, immediate = True, oneshot = True, **kwargs)
        else:
            self.run_in(self.media_player_set_source, 0, **kwargs)
            
    def media_player_state_on(self, entity, attribute, old, new, kwargs):
        if (self.get_state(entity, attribute = 'source', copy = False) != kwargs['source']):
            delay = 0
            if entity in self.args['device_config'] and 'source_command_delay' in self.args['device_config'][entity]:
                delay = self.args['device_config'][entity]['source_command_delay']
            self.run_in(self.media_player_set_source, delay, **kwargs)
        else:
            self.log("[media_player_state_on] Source of {} is already set to {}".format(entity, kwargs['source']))

    def media_player_set_source(self, kwargs):
        self.log('[media_player_set_source] Setting source for {} to {}'.format(kwargs['entity_id'], kwargs['source']))
        self.call_service('media_player/select_source', entity_id = kwargs['entity_id'], source = kwargs['source'])
    
    def media_call_service(self, kwargs):
        media_data = {}
        if 'data' in kwargs['media']:
            media_data = kwargs['media']['data']
        
        self.log("[media_call_service] Calling service {} for {}".format(kwargs['media']['service'], kwargs['media']['entity_id']))
        self.call_service(kwargs['media']['service'], entity_id = kwargs['media']['entity_id'], **media_data)