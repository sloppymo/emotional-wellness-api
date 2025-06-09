#!/usr/bin/env python3
"""Years of Lead CLI"""

import sys
from core import GameState

def main():
    print("=== Welcome to Years of Lead ===")
    print("A turn-based insurgency simulator")
    print()
    
    try:
        print("Initializing game state...")
        gs = GameState()
        print("Game initialized successfully!")
        print()
        
        while True:
            print(f"Turn {gs.turn_number} - Phase: {gs.current_phase.value}")
            print("Commands: 'advance' (advance turn), 'status' (show status), 'quit' (exit)")
            print()
            
            cmd = input("> ").strip().lower()
            
            if cmd == "advance":
                print("Advancing turn...")
                gs.advance_turn()
                print("Turn advanced!")
                print()
            elif cmd == "status":
                status = gs.get_status_summary()
                print(f"Turn: {status['turn']}")
                print(f"Phase: {status['phase'].value}")
                print(f"Active agents: {status['active_agents']}/{status['total_agents']}")
                print()
            elif cmd == "quit":
                print("Thanks for playing Years of Lead!")
                break
            else:
                print("Unknown command. Try 'advance', 'status', or 'quit'")
                print()
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 