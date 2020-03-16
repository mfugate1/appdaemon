import hassapi as hass
import subprocess

class ConfUpdater(hass.Hass):

    def initialize(self):
        self.run_event_listener = self.listen_event(self.run_updater, self.args.get('event', 'RUN_CONF_UPDATER'))
        
    def terminate(self):
        if hasattr(self, 'run_event_listener'):
            self.cancel_timer(self.run_event_listener)
            
    def run_updater(self, event_name, data, kwargs):
        self.log("[run_updater] Pulling latest configuration")
        subprocess.Popen(['/usr/bin/git', 'pull'], cwd = '/conf')