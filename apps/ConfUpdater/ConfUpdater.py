import hassapi as hass
import subprocess

class ConfUpdater(hass.Hass):

    def initialize(self):
        self.git_pull_event_listener = self.listen_event(self.git_pull, self.args['git_pull_event'])
        self.update_sleepyq_event_listener = self.listen_event(self.update_sleepyq, self.args['update_sleepyq_event'])
        
    def terminate(self):
        if hasattr(self, 'git_pull_event_listener'):
            self.cancel_timer(self.git_pull_event_listener)
        if hasattr(self, 'update_sleepyq_event_listener'):
            self.cancel_timer(self.update_sleepyq_event_listener)
            
    def git_pull(self, event_name, data, kwargs):
        self.log("[git_pull] Pulling latest configuration")
        subprocess.Popen(['/usr/bin/git', 'pull'], cwd = '/conf')
        
    def update_sleepyq(self, event_name, data, kwargs):
        self.log("[update_sleepyq] Reinstalling mfugate1/sleepyq python module")
        subprocess.Popen(['/usr/local/bin/pip3', 'install', '-e', 'git+https://github.com/mfugate1/sleepyq.git#egg=sleepyq'])