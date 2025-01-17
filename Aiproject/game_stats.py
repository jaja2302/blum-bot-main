class GameStats:
    def __init__(self):
        self.reset_stats()
        self.current_bet = "1M"
        
    def reset_stats(self):
        """Reset statistik game"""
        self.total_games = 0
        self.wins = 0
        self.defeats = 0
        self.nice = 0
        
    def update_stats(self, result):
        """Update statistik berdasarkan hasil game"""
        result = result.lower()
        self.total_games += 1
        
        if "nice" in result:
            self.nice += 1
        elif "winner" in result:
            self.wins += 1
        elif "defeat" in result:
            self.defeats += 1
            
    def set_betting_amount(self, amount):
        self.current_bet = amount
        
    def print_stats(self):
        print("\n=== Statistik Game ===")
        print(f"Total Games: {self.total_games}")
        print(f"Winner: {self.wins}")
        print(f"Defeat: {self.defeats}")
        print(f"Nice: {self.nice}")
        print(f"Current Bet: {self.current_bet}")
        print("====================\n") 