import os
import shutil
import PyInstaller.__main__

def clean_build():
    # Remove previous build files
    for item in ['build', 'dist', 'FightingGame.spec']:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)

def build_client():
    print("Building client executable...")
    PyInstaller.__main__.run([
        'client.py',
        '--name=FightingGameClient',
        '--onefile',
        '--windowed',
        '--add-data=player1;player1',
        '--add-data=player2;player2',
        '--add-data=background.jpg;.',
        '--hidden-import=pygame',
        '--noconsole'
    ])
    
    # Create a folder for the client app
    client_dir = 'FightingGame_Client'
    if not os.path.exists(client_dir):
        os.makedirs(client_dir)
    
    # Copy necessary files
    shutil.move('dist/FightingGameClient.exe', f'{client_dir}/FightingGame.exe')
    shutil.copytree('player1', f'{client_dir}/player1', dirs_exist_ok=True)
    shutil.copytree('player2', f'{client_dir}/player2', dirs_exist_ok=True)
    shutil.copy('background.jpg', client_dir)
    
    # Create a README file
    with open(f'{client_dir}/README.txt', 'w') as f:
        f.write("Fighting Game - Client\n")
        f.write("1. Run 'FightingGame.exe'\n")
        f.write("2. Enter the host's IP address when prompted\n")
        f.write("3. Use arrow keys + K/L to play\n\n")
        f.write("Controls:\n")
        f.write("Player 2: Arrow keys + K (punch) / L (kick)")
    
    print(f"\nClient app created in '{client_dir}' folder")
    print(f"Zip the '{client_dir}' folder and share it with other players")

def build_server():
    print("\nBuilding server executable...")
    PyInstaller.__main__.run([
        'server.py',
        '--name=FightingGameServer',
        '--onefile',
        '--noconsole'
    ])
    
    # Create a folder for the server app
    server_dir = 'FightingGame_Server'
    if not os.path.exists(server_dir):
        os.makedirs(server_dir)
    
    # Copy necessary files
    shutil.move('dist/FightingGameServer.exe', f'{server_dir}/FightingGameServer.exe')
    
    # Create a README file
    with open(f'{server_dir}/README.txt', 'w') as f:
        f.write("Fighting Game - Server\n")
        f.write("1. Run 'FightingGameServer.exe'\n")
        f.write("2. Note your public IP address (use whatismyip.com)\n")
        f.write("3. Share this IP with other players\n")
        f.write("4. Run the client app and connect to your IP\n\n")
        f.write("Note: You may need to forward port 5555 in your router settings")
    
    print(f"\nServer app created in '{server_dir}' folder")
    print("Run this on the host computer")

if __name__ == "__main__":
    clean_build()
    build_client()
    build_server()
    print("\nBuild complete!")
    print("1. Share the 'FightingGame_Client' folder with other players")
    print("2. Keep the 'FightingGame_Server' folder for yourself")
    print("3. Make sure to forward port 5555 on your router for online play")
