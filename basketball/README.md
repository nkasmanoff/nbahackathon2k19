Basketball Analytics
--------------------


Calcualting offensive and defensive rating of every player in the 2018 nba playoffs


So here's where I'm at

It is possible to calculated this stat for the first three quarters, at least according to the raptors wizards game which finished 102-92. I find that the players have identical offensive and defensive ratings for those 3 quarters, but this matching ends once the fourth is reached. 

I noted earlier on the total # of possessions seemed different between the NBA stats and what we were given, and now I'm actually seeing this in the fourth quarter. Pascal Siakam plays the entirety of the fourth, and his ORTG on the website is 145, and for us is 138. This seems to imply we are tracking more possessions than what are in the actual pbp, so this may be due to rulekeeping variation, or a particular issue. 

In order to isolate it further, I can see if any players who played in the fourth are not affected by this issue, and by slowly narrowing that window, see what "play" turned into a possession when perhaps it shouldn't have. 

Next up is also flagrant and technical free throws. 

Think through this one a little bit more, but confirm that even if you make the final free throw, if it is because of a flag or tech, the possession is not yet over! And to make things even trickier, keep in track the subs to occur during such events, and the free throw (fte) rule made to cover them too. 


By narrowing the window, it appears this extra possession occurs somewhere between when Kyle Lowry first checks into the game, and when Demar does. 