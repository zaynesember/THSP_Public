import tweepy as tw
from matplotlib import pyplot as plt
import numpy as np
import scipy as sp
import csv
from datetime import datetime

#Takes in screen name of the favoriter, number of pages of favorited tweets you want, and the api instance.
#Returns a list of screennames from the favorited tweets
def get_favorites_screennames(screen_name, pages, api):
    
    p=1
    id_list = []
    
    for p in range(pages):
        id_list.append(api.favorites(screen_name, page = str(p)))
    
    #id_list is actually a list of Tweepy Resultsets (one for each page) which are themselves a subclass of list. Nested for loops
    #are a slow way to deal with this and there may be a more efficient ways with vectorization
    sn_list = []
    
    for r in id_list:
        for s in r:
            sn_list.append(s.user.screen_name)
    
    return sn_list

#Same as get_favorites_screennames except it returns the user objects instead of the screennames. This doesn't seem easy to do with retweets
def get_favorites_users(screen_name, pages, api):
    
    p=1
    id_list = []
    
    for p in range(pages):
        id_list.append(api.favorites(screen_name, page = str(p)))
    
    #id_list is actually a list of Tweepy Resultsets (one for each page) which are themselves a subclass of list. Nested for loops
    #are a slow way to deal with this and there may be a more efficient ways with vectorization
    sn_list = []
    
    for r in id_list:
        for s in r:
            sn_list.append(s.user)
    
    return sn_list


#Takes in screen name of the retweeter, number of pages of tweets you want to pull retweets from, and the api instance.
#Returns a tuple of list of screennames from the retweets and tuple timestamp from first and last retweet
def get_retweets_screennames(screen_name, pages, api):
    
    p=1
    timeline_list = []
    
    for p in range(pages):
        timeline_list.append(api.user_timeline(screen_name, page = str(p)))
    
    #Again, timeline_list is actually a list of Tweepy Resultsets (one for each page) which are themselves a subclass of list
    sn_list = []
    timestamp_list = []
    
    for result_set in timeline_list:
        for tweet in result_set:
            
            #First check for the RT tag to know if it's a retweet then find the substring of the text containing the retweetee
            if tweet.text[0:2] == "RT":
                
                #Snip parts I know can't contain the screen name because of Twitter's 15 character limit
                sn = tweet.text[4:19]
                
                #For some reason using rfind was not working consistently so I'm using this less syntactically sugary method
                check = sn.find(':')
                if check != -1:
                    sn_list.append(sn[0:check])
                else: sn_list.append(sn)
                timestamp_list.append(tweet.created_at)
    
    return sn_list,(timestamp_list[-1],timestamp_list[0])

#Takes in screen name you want retweets from, api instance, and the number of pages of timeline to pull retweets from
#Returns a list of retweets (Tweet objects) from the screenname
#Uses much of the same code as get_retweets_screennames
def get_retweets_list(screen_name, api, pages=2):
    
    p=1
    timeline_list = []
    
    for p in range(pages):
        timeline_list.append(api.user_timeline(screen_name, page = str(p)))
    
    rt_list = []
    
    for result_set in timeline_list:
        for tweet in result_set:
            if tweet.text[0:2] == "RT":
                rt_list.append(tweet)
    
    return rt_list

#Matches screen name to categories of user and returns additional info
#Takes in a screen name and API instance
#Returns a list of strings with more info about the user
def get_user_info(screen_name, api):
    
    #Catch party accounts
    if screen_name == "GOP": return ["GOP"]
    if screen_name == "TheDemocrats": return ["Dem Party"]
    if screen_name == "SenateGOP": return ["Senate GOP"]
    if screen_name == "SenateDems": return ["Senate Dems"]
    if screen_name == "HouseGOP": return ["House GOP"]
    if screen_name == "HouseDemocrats": return ["House Dems"]
    
    #Catch if they're a representative or senator
    with open('116thCongressTwitter.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            if (row[2].lower() == screen_name.lower()) or (row[3].lower() == screen_name.lower()):
                #Returns [position, name, state icps, district code, state abbrev, party_code (Voteview), year born, nom dim 1, nom dim 2]
                return [row[1],row[0],row[5],row[6],row[7],row[8],row[9],row[10],row[11]]
    
    #Catch if it's a committee account
    with open('116thCongressCommittees.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            if row[3] == screen_name:
                #Returns [descriptor, chamber, committee name]
                return ["Committee",row[2],row[0]]
    
    #Catch if it's a caucus account
    #NOTE: The caucus csv is not complete as there are WAY too many caucuses to find without automation
    with open('116thCongressCaucuses.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            if row[2] == screen_name:
                #Returns [descriptor, caucus name]
                return ["Caucus", row[0]]
            
    #Catch if it's someone from the Executive Branch
    with open('ExecutiveTwitter.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            if row[1] == screen_name:
                #Returns [descriptor, name]
                return ["Executive",row[0]]
    
    #Catch if it's someone from the media
    #NOTE: The MediaAndJournalistsTwitter csv is not complete nor extensive
    with open('MediaAndJournalistsTwitter.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        for row in csv_reader:
            if row[3] == screen_name:
                #Returns [descriptor, Name, Network/Publication, Network/Publication 2]
                return ["Media/Journalist",row[0],row[1],row[2]]
            
    #Returns [descriptor, user's name, user's handle]
    return ["Other", api.get_user(screen_name).name, screen_name]

#Takes a list of screen names and returns an average of first dimension DW-NOMINATE scores from the applicable screen names
#on that list (voting representatives and senators)
def dw_avg(sn_list, api):
    
    count = 0
    sum = 0
    
    for name in sn_list:
        result = get_user_info(name,api)
        if (result[0]=="Rep" or result[0] == "Sen") and (result[7] != "NA" or result[7] != ""):
            #Have to catch exceptions caused by instances of non-voting members
            try:
                sum += float(result[7])
                count += 1
            except ValueError:
                continue
    return sum/count

#Adapted from here: https://www.geeksforgeeks.org/find-frequency-of-each-word-in-a-string-in-python/
#Takes in a list of anything
#Returns list of tuples that tells the frequency of each unique item in input_list
def freq(input_list): 
          
    input_list2 = []
    output_list = []

    for i in input_list:              
        if i not in input_list2: 
            input_list2.append(i)  
              
    for i in range(0, len(input_list2)): 
        output_list.append((input_list2[i], input_list.count(input_list2[i])))
    
    return output_list
    
    
    
    