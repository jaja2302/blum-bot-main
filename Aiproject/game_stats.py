class GameStats:
    def __init__(self):
        self.total_games = 0
        self.wins = 0
        self.defeats = 0
        self.nice_shots = 0
        self.current_bet = "1M"  # Default betting amount
        
    def update_stats(self, result):
        """Update statistik berdasarkan hasil game"""
        result = result.lower()
        self.total_games += 1
        
        if "nice" in result:
            self.nice_shots += 1
            print("Nice terdeteksi!")
        elif "winner" in result:
            self.wins += 1
            print("Win terdeteksi!")
        elif "defeat" in result:
            self.defeats += 1
            print("Defeat terdeteksi!")
            
    def set_betting_amount(self, amount):
        """Set jumlah betting yang akan digunakan"""
        self.current_bet = amount
        
    def print_stats(self):
        """Tampilkan statistik game"""
        print("\n=== Statistik Game ===")
        print(f"Total Games: {self.total_games}")
        print(f"Wins: {self.wins}")
        print(f"Defeats: {self.defeats}")
        print(f"Nice Shots: {self.nice_shots}")
        print(f"Current Bet: {self.current_bet}")
        print("====================\n") 