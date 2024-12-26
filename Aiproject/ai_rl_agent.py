import numpy as np
from collections import deque
import random
import time

class RLAgent:
    def __init__(self):
        # RL parameters
        self.state_size = 6  # [hoop_x, hoop_y, velocity_x, ball_x, ball_y, distance]
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0   # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # Discrete action space
        self.angles = [-60, -30, 30, 60]
        self.powers = [0.4, 0.6, 0.8]
        
        # Q-table: state discretization
        self.x_bins = 10
        self.y_bins = 10
        self.v_bins = 5
        self.d_bins = 10
        
        # Initialize Q-table
        self.q_table = {}
        
        # Track last position for velocity calculation
        self.last_pos = None
        self.last_time = None

    def discretize_state(self, state):
        """Convert continuous state to discrete state"""
        x, y, v_x, ball_x, ball_y, distance = state
        
        # Normalize and discretize values
        x_d = int(x / 1920 * self.x_bins)
        y_d = int(y / 1080 * self.y_bins)
        v_d = int(np.clip((v_x + 100) / 200 * self.v_bins, 0, self.v_bins-1))
        d_d = int(np.clip(distance / 1000 * self.d_bins, 0, self.d_bins-1))
        
        return (x_d, y_d, v_d, d_d)

    def get_state(self, game_screen, hoop_pos):
        """Convert game state to agent state"""
        x, y = hoop_pos
        ball_x = game_screen.shape[1] // 2
        ball_y = game_screen.shape[0] - 200
        
        # Calculate velocity
        velocity_x = 0
        current_time = time.time()
        if self.last_pos and self.last_time:
            dt = current_time - self.last_time
            if dt > 0:
                velocity_x = (x - self.last_pos[0]) / dt
        
        # Update last position
        self.last_pos = (x, y)
        self.last_time = current_time
        
        distance = np.sqrt((x - ball_x)**2 + (y - ball_y)**2)
        
        return np.array([x, y, velocity_x, ball_x, ball_y, distance])

    def get_action(self, game_screen, hoop_pos):
        """Select action using epsilon-greedy policy"""
        state = self.get_state(game_screen, hoop_pos)
        discrete_state = self.discretize_state(state)
        
        # Epsilon-greedy action selection
        if random.random() < self.epsilon:
            angle = random.choice(self.angles)
            power = random.choice(self.powers)
        else:
            # Get action with highest Q-value
            best_value = float('-inf')
            angle = self.angles[0]
            power = self.powers[0]
            
            for a in self.angles:
                for p in self.powers:
                    state_action = discrete_state + (a, p)
                    value = self.q_table.get(state_action, 0.0)
                    if value > best_value:
                        best_value = value
                        angle = a
                        power = p
        
        return (angle, power)

    def remember(self, state, action, reward, next_state, done):
        """Store experience in memory"""
        discrete_state = self.discretize_state(state)
        discrete_next_state = self.discretize_state(next_state)
        angle, power = action
        
        # Update Q-table
        state_action = discrete_state + (angle, power)
        
        # Get current Q value
        current_q = self.q_table.get(state_action, 0.0)
        
        # Get max Q value for next state
        next_max_q = 0.0
        for a in self.angles:
            for p in self.powers:
                next_state_action = discrete_next_state + (a, p)
                next_max_q = max(next_max_q, self.q_table.get(next_state_action, 0.0))
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.gamma * next_max_q * (1 - done) - current_q
        )
        
        # Update Q-table
        self.q_table[state_action] = new_q

    def train(self):
        """Update epsilon"""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_model(self):
        """Dummy method to maintain compatibility"""
        pass