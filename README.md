<p float="left">
<img src="https://github.com/thom974/osu--beatmap-gen-v3/assets/74675902/3444e654-4f5f-495a-b042-15b0eb11d585" width="500" /> <img src="https://github.com/thom974/osu--beatmap-gen-v3/assets/74675902/9a390cab-c6eb-44af-9da6-6cde41caa00d" width="500" /> <img src="https://github.com/thom974/osu--beatmap-gen-v3/assets/74675902/f20bab38-c364-4ef9-9c2a-5a932053a777" width="500" /> <img src="https://github.com/thom974/osu--beatmap-gen-v3/assets/74675902/b1754a0b-3dfa-4265-a6f2-6a3e7dfe966b" width="500" />
</p>
 
# osu--beatmap-gen-v3
python program with GUI made to generate maps for the game osu!

an osu! application that utilizes the osu! api v2 and chromedriver, along with various python modules including requests and selenium.

access to the osu! api requires OAuth which is handled within the program. the user is asked to authorize the app with their osu! account. access tokens that are granted expire after 24 hours of being issued.

IMPORTANT:

when asked to specify the 'number of maps to filter', this DOES NOT mean how many maps you want to download. rather, it's the amount of maps you want the program to initially gather, before filtering out (according to the filters you set).

also the program isn't as robust as i'd like it to be right now, as i'm still working on it. expect bugs/errors/random crashes from time to time. as long as you follow the instructions everything should be fine.

# installing the virtual environment 

note: you must have pipenv installed!

an installation of the program's virtual environment is necessary for all the dependencies. to install the virtual environment, open a Command Prompt in the 'Generator' folder. you then need to run this command:

pipenv install --ignore-pipfile 

to run the program, make sure Command Prompt is in the 'Generator' directory:

pipenv run python main.py 

OR // run the bat file.
