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
            
        self.log("[media_controller_command] Room = {}".format(room))

    def get_last_used_alexa(self):
        for room, values in self.args['rooms'].items():
            if self.get_state(values['alexa'], attribute='last_called'):
                return room
        return ''
        
    