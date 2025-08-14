class level2:
    def __init__(self):
        self.all_levers_pulled = False
        self.spike_activated = True
        self.num_levers_pulled = 0
        self.lever_states = {
            'lever1': False,
            'lever2': False,
            'lever3': False,
            'lever4': False
        }

    def pull_lever(self, lever_id):
        if lever_id in self.lever_states and not self.lever_states[lever_id]:
            self.lever_states[lever_id] = True
            self.num_levers_pulled += 1
            return True
        return False

    def update(self):
        if self.num_levers_pulled == 4:
            self.all_levers_pulled = True
            self.spike_activated = False
