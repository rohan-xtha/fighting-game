@echo off
echo Creating directory structure...
mkdir fighting-game-web
mkdir fighting-game-web\assets
mkdir fighting-game-web\assets\player1
mkdir fighting-game-web\assets\player2

echo Copying files...
copy "web_version\index.html" "fighting-game-web\"
copy "web_version\game_web.py" "fighting-game-web\"
copy "background.jpg" "fighting-game-web\assets\"

xcopy "player1" "fighting-game-web\assets\player1" /E /I /Y
xcopy "player2" "fighting-game-web\assets\player2" /E /I /Y

echo.
echo Files have been moved to the fighting-game-web folder
echo Next steps:
echo 1. cd fighting-game-web
echo 2. git init
echo 3. git add .
echo 4. git commit -m "Initial commit"
echo 5. Create a new repository on GitHub
echo 6. Follow the instructions to push your code

pause
