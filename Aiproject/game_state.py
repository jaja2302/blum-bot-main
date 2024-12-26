class GameState:
    MAINTENANCE = 'maintenance'
    WAITING = 'waiting'
    READY = 'ready'
    SHOOTING = 'shooting'
    SCORED = 'scored'
    
    def __init__(self):
        self.current_state = self.WAITING
        self.score = 0
        self.shots = 0
        
    def update(self, detection_result):
        if detection_result['status'] == 'maintenance':
            self.current_state = self.MAINTENANCE
        elif detection_result['status'] == 'active':
            if self.current_state != self.SHOOTING:
                self.current_state = self.READY 