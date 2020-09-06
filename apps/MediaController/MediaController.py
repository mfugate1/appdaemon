import hassapi as hass

class MediaController(hass.Hass):

    def initialize(self):
        self.event_listener = self.listen_event(self.media_controller_command, self.args.get('event', 'MEDIA_CONTROLLER_COMMAND'))
        
    def terminate(self):
        if hasattr(self, 'event_listener'):
            self.cancel_listen_event(self.event_listener)
        
    def media_controller_command(self, event_name, data, kwargs):
        if 'room' in data:
            room = data['room']
        else:
            room = self.get_last_used_alexa()
            
        if not room:
            self.log("[media_controller_command] No room given or found with alexa last_called")
            return

        if 'source' not in data:
            self.log("[media_controller_command] Missing source, nothing to do!")
            return
            
        source = data['source']
        room_info = self.args['rooms'][room]
            
        if source not in room_info['sources']:
            self.log("[media_controller_command] {} is not a source in {}".format(source, room))
            return
        
        self.log("[media_controller_command] Room = {}, Source = {}".format(room, data['source']))
        
        source_info = room_info['sources'][source]
        
        if 'receiver_source' in source_info:
            self.run_in(self.media_player_on, 0, entity_id = room_info['receiver'], source = source_info['receiver_source'])
            
        if 'tv_source' in source_info:
            self.run_in(self.media_player_on, 0, entity_id = room_info['tv'], source = source_info['tv_source'])
            
        if 'media' in source_info:
            media = source_info['media']
            if 'data' in media:
                media_data = media['data']
            else:
                media_data = {}
                
            self.call_service(media['service'], entity_id = media['entity_id'], **media_data)

    def media_player_on(self, kwargs):
        if self.get_state(kwargs['entity_id']) == 'off':
            self.turn_on(kwargs['entity_id'])

        self.listen_state(self.media_player_set_source, kwargs['entity_id'], new = 'on', duration = 0, immediate = True, oneshot = True, **kwargs)

    def media_player_set_source(self, entity, attribute, old, new, kwargs):
        if (self.get_state(entity, attribute = 'source', copy = False) != kwargs['source']):
            self.log('Setting source for {} to {}'.format(kwargs['entity_id'], kwargs['source']))
            self.call_service('media_player/select_source', entity_id = kwargs['entity_id'], source = kwargs['source'])
    
    def get_last_used_alexa(self):
        for room, values in self.args['rooms'].items():
            if self.get_state(values['alexa'], attribute='last_called', copy = False):
                return room
        return ''
        
    