@echo off
echo Installing required packages...
pip install pyinstaller pygame

echo Creating client executable...
pyinstaller --onefile --windowed --name="FightingGame" --add-data="player1;player1" --add-data="player2;player2" --add-data="background.jpg;." --hidden-import=pygame --noconsole client.py

if exist "dist\\FightingGame.exe" (
    echo Copying game files...
    if not exist "FightingGame" mkdir FightingGame
    copy "dist\\FightingGame.exe" "FightingGame\\"
    xcopy /E /I /Y "player1" "FightingGame\\player1"
    xcopy /E /I /Y "player2" "FightingGame\\player2"
    copy "background.jpg" "FightingGame\\"
    
    echo.
    echo Build successful!
    echo The game is in the 'FightingGame' folder
    echo Just send the entire folder to your friends
) else (
    echo Build failed. Please check for errors above.
)

pause
