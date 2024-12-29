class GameStats:
    def __init__(self):
        self.total_games = 0
        self.wins = 0
        self.defeats = 0
        self.nice = 0  # Ubah dari nice_shots ke nice
        self.current_bet = "1M"  # Default betting amount
        self.reset_stats()
        
    def reset_stats(self):
        """Reset statistik game"""
        self.total_games = 0
        self.wins = 0
        self.defeats = 0
        self.nice = 0  # Ubah dari nice_shots ke nice
        
    def update_stats(self, result):
        """Update statistik berdasarkan hasil game"""
        result = result.lower()
        self.total_games += 1
        
        if "nice" in result:
            self.nice += 1  # Ubah dari nice_shots ke nice
            print("Nice terdeteksi!")
        elif "winner" in result:
            self.wins += 1
            print("Winner terdeteksi!")
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
        print(f"Winner: {self.wins}")
        print(f"Defeat: {self.defeats}")
        print(f"Nice: {self.nice}")  # Ubah dari Nice Shots ke Nice
        print(f"Current Bet: {self.current_bet}")
        print("====================\n")
        
    def cleanup_game(self):
        """Cleanup setelah game selesai"""
        self.print_stats() 