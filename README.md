# osu--beatmap-gen-v3
thomas' beatmap gen // wip

an osu! application that utilizes the osu! api v2 and chromedriver, along with various python modules including requests and selenium.

access to the osu! api requires OAuth which is handled within the program. the user is asked to authorize the app with their osu! account. access tokens that are granted expire after 24 hours of being issued.

IMPORTANT:

when asked to specify the 'number of maps to filter', this DOES NOT mean how many maps you want to download. rather, it's the amount of maps you want the program to initially gather, before filtering out (according to the filters you set).

also the program isn't as robust as i'd like it to be right now, as i'm still working on it. expect bugs/errors/random crashes from time to time. as long as you follow the instructions everything should be fine.
