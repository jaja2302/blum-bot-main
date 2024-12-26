import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

class DQN(nn.Module):
    def __init__(self, input_size, output_size):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        return self.network(x)

class RLAgent:
    def __init__(self):
        self.state_size = 4  # Game state features
        self.action_size = 8  # Possible shooting angles/powers
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # Discount factor
        self.epsilon = 1.0   # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = DQN(self.state_size, self.action_size)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

    def get_state(self, game_screen, hoop_pos):
        """Convert game state to feature vector"""
        # Extract relevant features from game state
        ball_pos = self._detect_ball(game_screen)
        if ball_pos and hoop_pos:
            dx = hoop_pos[0] - ball_pos[0]
            dy = hoop_pos[1] - ball_pos[1]
            distance = np.sqrt(dx**2 + dy**2)
            angle = np.arctan2(dy, dx)
            return np.array([dx, dy, distance, angle])
        return np.zeros(self.state_size)

    def get_action(self, game_screen, hoop_pos):
        """Decide shooting parameters based on current state"""
        state = self.get_state(game_screen, hoop_pos)
        
        if random.random() < self.epsilon:
            # Exploration: random action
            angle = random.uniform(0, 90)
            power = random.uniform(0.3, 1.0)
        else:
            # Exploitation: use model
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                action_values = self.model(state_tensor)
            action_idx = torch.argmax(action_values).item()
            angle = (action_idx % 4) * 30  # 0, 30, 60, 90 degrees
            power = ((action_idx // 4) + 1) * 0.25  # 0.25, 0.5, 0.75, 1.0
            
        return (angle, power)

    def _detect_ball(self, game_screen):
        """Detect ball position in the game screen"""
        # Implement ball detection logic here
        # For now, return None
        return None

    def train(self, state, action, reward, next_state, done):
        """Train the model using experience replay"""
        self.memory.append((state, action, reward, next_state, done))
        
        if len(self.memory) < 32:  # Minimum batch size
            return
            
        batch = random.sample(self.memory, 32)
        
        # Implementation of DQN training
        # (Simplified for this example)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay 