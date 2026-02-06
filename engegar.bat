@echo off
cd /d "C:\Users\User\Documents\Python\Git\Cau"

:: Obre el ngrok amb el teu domini fix
start ngrok http --url=lakeesha-semiherbaceous-nonstudiously.ngrok-free.dev 8080

:: Espera una mica perquè el túnel s'activi
timeout /t 5

:: Llança el bot
python Allstendres.py

pause