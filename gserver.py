import socket
import random
import json

host = "localhost"
port = 7777
banner = """
== Guessing Game v2.0 ==

Choose difficulty:
1. Easy (1-50)
2. Medium (1-100)
3. Hard (1-500)
"""

def generate_random_int(difficulty):
    ranges = {1: (1, 50), 2: (1, 100), 3: (1, 500)}
    low, high = ranges.get(difficulty, (1, 100))  
    return random.randint(low, high)

def load_leaderboard():
    try:
        with open("leaderboard", "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Error: Invalid JSON data in leaderboard. Starting with empty leaderboard.")
                return {}
    except FileNotFoundError:
        print("Leaderboard file not found. Creating a new one.")
        with open("leaderboard", "w") as f:
            json.dump({}, f)
        return {}

def update_leaderboard(leaderboard, name, score, difficulty):
    leaderboard[name] = {"score": score, "difficulty": difficulty}
    with open("leaderboard", "w") as f:
        json.dump(leaderboard, f)

def display_leaderboard(leaderboard):
    print("\nLeaderboard:")
    if leaderboard:
        for name, data in sorted(leaderboard.items(), key=lambda item: item[1]["score"]):
            print(f"{name}: {data['score']} (Difficulty: {data['difficulty']})")
    else:
        print("Leaderboard is empty.")


leaderboard = load_leaderboard()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(5)

print(f"Server is listening on port {port}")

while True:
    conn, addr = s.accept()
    print(f"New client: {addr[0]}")
    conn.sendall(banner.encode())
    
    guessme = None  
    difficulty = None

    while True:
        try:
            client_input = conn.recv(1024)
            if not client_input: 
                break

            data = json.loads(client_input.decode())

            if "difficulty" in data and guessme is None: 
                difficulty = data["difficulty"]
                guessme = generate_random_int(difficulty)
                conn.sendall(json.dumps({"message": "Guess the number!", "guessme": guessme}).encode())

            elif "guess" in data:
                guess = data["guess"]
                name = data["name"]
                score = data["score"] + 1

                if guess == guessme:
                    update_leaderboard(leaderboard, name, score, difficulty)
                    conn.sendall(json.dumps({"message": f"Correct Answer! Your score: {score}", "status": "win"}).encode())
                    display_leaderboard(leaderboard)
                    guessme = None 
                    difficulty = None
                else: 
                    response = {
                        "message": "Guess Lower!" if guess > guessme else "Guess Higher!",
                        "status": "incorrect"
                    }
                    conn.sendall(json.dumps(response).encode())

            elif "action" in data and data["action"] == "quit":
                conn.close()
                conn = None
                break

        except json.JSONDecodeError:
            conn.sendall(json.dumps({"message": "Invalid input. Please send valid JSON data.", "status": "error"}).encode())

    conn.close()



