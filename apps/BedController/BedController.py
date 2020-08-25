from datetime import datetime
from sleepyq import Sleepyq

import hassapi as hass
import secrets

BED_PRESETS = {
    "Favorite": 1,
    "Read": 2,
    "Watch TV": 3,
    "Flat": 4,
    "Zero G": 5,
    "Snore": 6
}

class BedController(hass.Hass):

    def initialize(self):
        self.client = self.get_client()
        self.start_update_timer()
        self.start_state_listeners()
        self.start_update_timer()
        self.stop_motion_listener = self.listen_event(self.stop_motion, self.args['stop_motion_event'])
        
    def terminate(self):
        self.cancel_state_listeners()
        self.cancel_update_timer()
            
    def start_state_listeners(self):
        self.preset_listener = self.listen_state(self.preset, self.args['preset_entity'])
        self.set_foot_position_listener = self.listen_state(self.set_position, self.args['foot_position_entity'], actuator = 'f')
        self.set_head_position_listener = self.listen_state(self.set_position, self.args['head_position_entity'], actuator = 'h')
        self.set_left_sleepnumber_listener = self.listen_state(self.set_sleepnumber, self.args['left_sleep_number_entity'], side = 'l')
        self.set_right_sleepnumber_listener = self.listen_state(self.set_sleepnumber, self.args['right_sleep_number_entity'], side = 'r')
        
    def cancel_state_listeners(self):
        if hasattr(self, 'preset_listener'):
            self.cancel_listen_state(self.preset_listener)
        if hasattr(self, 'set_foot_position_listener'):
            self.cancel_listen_state(self.set_foot_position_listener)
        if hasattr(self, 'set_head_position_listener'):
            self.cancel_listen_state(self.set_head_position_listener)
        if hasattr(self, 'set_left_sleepnumber_listener'):
            self.cancel_listen_state(self.set_left_sleepnumber_listener)
        if hasattr(self, 'set_right_sleepnumber_listener'):
            self.cancel_listen_state(self.set_right_sleepnumber_listener)
            
    def start_update_timer(self):
        self.update_timer = self.run_every(self.update, datetime.now(), self.args['update_interval_seconds'])
        
    def cancel_update_timer(self):
        if hasattr(self, 'update_timer'):
            self.cancel_timer(self.update_timer)
    
    def get_client(self):
        client = Sleepyq(secrets.SLEEP_IQ_USER, secrets.SLEEP_IQ_PASSWORD)
        client.login()
        return client
        
    def preset(self, entity, attribute, old, new, kwargs):
        self.log('[preset] Setting bed to preset position {}'.format(new))
        self.cancel_update_timer()
        self.client.preset(BED_PRESETS[new], 'r')
        self.start_update_timer()
    
    def set_position(self, entity, attribute, old, new, kwargs):
        self.log('[set_position] Setting bed position, actuator = {}, position = {}'.format(kwargs['actuator'], new))
        self.cancel_update_timer()
        self.client.set_foundation_position('r', kwargs['actuator'], float(new))
        self.start_update_timer()
    
    def set_sleepnumber(self, entity, attribute, old, new, kwargs):
        self.log('[set_sleepnumber] Setting bed sleep number, side = {}, value = {}'.format(kwargs['side'], new))
        self.cancel_update_timer()
        self.client.set_sleepnumber(kwargs['side'], float(new))
        self.start_update_timer()
        
    def stop_motion(self, event_name, data, kwargs):
        self.client.stop_motion('r')
        
    def update(self, kwargs):
        foundationStatus = self.client.foundation_status()
        
        self.cancel_state_listeners()
        
        if foundationStatus.fsCurrentPositionPresetRight != 'Not at preset':
            #self.select_option(self.args['preset_entity'], foundationStatus.fsCurrentPositionPresetRight)
            self.log('[update] Setting {} to {}'.format(self.args['preset_entity'], foundationStatus.fsCurrentPositionPresetRight))
            self.call_service('input_select/select_option', entity_id = self.args['preset_entity'], option = foundationStatus.fsCurrentPositionPresetRight)
            
        #self.set_value(self.args['foot_position_entity'], foundationStatus.fsRightFootPosition)
        #self.set_value(self.args['head_position_entity'], foundationStatus.fsRightHeadPosition)

        self.log('[update] Setting {} to {}'.format(self.args['foot_position_entity'], foundationStatus.fsRightFootPosition))
        self.call_service('input_number/set_value', entity_id = self.args['foot_position_entity'], value = foundationStatus.fsRightFootPosition)
        self.log('[update] Setting {} to {}'.format(self.args['head_position_entity'], foundationStatus.fsRightHeadPosition))
        self.call_service('input_number/set_value', entity_id = self.args['head_position_entity'], value = foundationStatus.fsRightHeadPosition)
        
        sleeperStatus = self.client.beds_with_sleeper_status()[0]
        
        #self.set_value(self.args['left_sleep_number_entity'], sleeperStatus.left.sleepNumber)
        #self.set_value(self.args['right_sleep_number_entity'], sleeperStatus.right.sleepNumber)

        self.log('[update] Setting {} to {}'.format(self.args['left_sleep_number_entity'], sleeperStatus.left.sleepNumber))
        self.call_service('input_number/set_value', entity_id = self.args['left_sleep_number_entity'], value = sleeperStatus.left.sleepNumber)
        self.log('[update] Setting {} to {}'.format(self.args['right_sleep_number_entity'], sleeperStatus.right.sleepNumber))
        self.call_service('input_number/set_value', entity_id = self.args['right_sleep_number_entity'], value = sleeperStatus.right.sleepNumber)
        
        self.start_state_listeners()