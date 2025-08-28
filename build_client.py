import os
import shutil
import PyInstaller.__main__

def build_client():
    print("Creating client executable...")
    
    # Create build directory if it doesn't exist
    if not os.path.exists('dist'):
        os.makedirs('dist')
    
    # PyInstaller configuration
    PyInstaller.__main__.run([
        'client.py',
        '--onefile',
        '--windowed',
        '--name=FightingGameClient',
        '--add-data=player1;player1',
        '--add-data=player2;player2',
        '--add-data=background.jpg;.',
        '--hidden-import=pygame',
        '--noconsole'
    ])
    
    # Copy necessary files to dist folder
    files_to_copy = ['player1', 'player2', 'background.jpg']
    for file in files_to_copy:
        if os.path.isdir(file):
            dest = os.path.join('dist', file)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(file, dest)
        else:
            shutil.copy2(file, 'dist')
    
    print("\nBuild complete! The game is in the 'dist' folder.")
    print("Send the entire 'dist' folder to your friend.")
    print("They just need to run 'FightingGameClient.exe' to play!")

if __name__ == "__main__":
    build_client()
