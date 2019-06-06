Contained in this folder is what I've done so far at tackling the NBA Hackathon's 2019
business analytics question, of predicting the # of engagements a profile will have. 

I've begun this search across a few different avenues, which I'll describe
below and hopefully get back to later on. 


1.
Explored the correlation between users at post, and output. 

Actually found a decently sized, negative correlation, so maybe this has an influence? The interpretaiton of that would be as more people follow the account, the few people engage with a post. But what exactly is an engagement? 



2.

Examined the post type, photo, video, or album. 

In this case there was significant separation between video and the other two post types, suggesting that videos are far more likely to be engaged than albums or photos, which makes sense considering you can scroll and see a photo, but must interact with a video in order to view it.  Albums are just a group of photos, so maybe the user saw the first photo and thought that was good enough, seeing as the engagement rates between photo's and albums are almost inseparable at this point. 


3. 

Exploring users tagged in post. The NBA is a star driven league, so perhaps people are more likely to interact with a post if it is about D'Angelo Russell instead of DJ Augustin. However there are clear caveats to this idea, if a totally random player like Meyers Leonard explodes for a career night in which case that will be a massively popular post. 

However, the hypothesis is that a post containing a player encoded as a "star" will be more likely to receive more engagements, so I already created a dataset of all users tagged in posts by the NBA, and can use that to then go back to the training set and tag which posts contain a star (or multiple), and which don't. 

This will require going by hand and creating a list of accounts belonging to NBA stars, and potentially accounting for times where the star is in the description but not explicitly tagged (Kawhi Leonard doesn't even have an insta). Such manual work shouldn't be too costly however, and I expect it to bear some good results. 


4.

I also think post time may have an impact, which is encoded in the "Created" column. 

To start I've looked at two easily separable time based features, the month of the post, and the hour of the post, while also accounting for daylight savings encoded as EST or EDT. 

From this there are already some obvious outcomes, such as a post receiving less attention in September in the pre-season, or being posted at 6 in the morning. Further parsing and possibly faster encoding by time of day (morning afternoon evening) or part of year (preseasion offseason, season, playoffs) may be easier to read for a model. 


5. 

To potentially expediate the modelling process in the beginning, it may be easier to turn this into a classification task at first. I noticed in the initial histogram that there were two distributions of engagements, one high and one low. By using a k-means clustering algorithm to split this into those two groups/distributions, we can have a better indicator of how well our feature derivation/modelling process is working by just simply classifying based on those outputs rather than a regression task. 

Also worth of note there is a class imbalance in this case, so simple accuracy metrics won't do. 

6-. 

I haven't gotten this far, but other metrics could also be derived, length of insta post, weekend or weekday, good teams as well as good player flags, etc. 
