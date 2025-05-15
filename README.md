set up :

1- Create a virtual environment to isolate the package dependencies locally : 
python -m venv env
windows :  `.\env\Scripts\activate`  ( `env\Scripts\activate.bat` On cmd ) 
mac / linux :  `source env/bin/activate` 

( note : if you get this error : 

`running scripts is disabled on this system`

its because of the "execution policy " of powershell 

solution : 
        
        1 - run vs code ( or your IDE ) as administrator

        2 - execute this commande ( temporary authorization ) :
        `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
        
         3 - rerun the command :  `.\venv\Scripts\activate`
)

2-  # Install Django and Django REST framework and other essential packages

`pip install -r requirements.txt`
