'''
Created on Nov 18, 2014

@author: joro
'''
import re

import musicbrainzngs as mb
# import Levenshtein
import os
import fnmatch
import sys
from eyed3.utils.cli import LoggingAction
import logging
mb.set_useragent("Dunya", "0.1")
mb.set_rate_limit(False)
mb.set_hostname("musicbrainz.s.upf.edu")

import json


def match( a, b):
       
        a = a.lower()
        b = b.lower()

     

        # lowercase and remove all non-letters (spaces, ', -, etc)
        a = re.sub(r"[^a-z]", "", a)
        b = re.sub(r"[^a-z]", "", b)

        # if a match, return
        if a == b:
            return True

        # otherwise, do edit distance.
        # an edit of <= 3 at the end of a string counts as a match
#         if len(a) > len(b):
#             a, b = b, a
#         # now, a is the shorter one. If a starts in b at position 0
#         #  then we have the overlap at the end
#         if b.startswith(a):
#             return True
# 
#         # Otherwise, chop both strings to the length of the shortest
#         # one, and check lev distance between them for <= 3
#         b = b[:len(a)]
#         return Levenshtein.distance(a, b) <= 3
        return False

def load_mbidlist(URIAbzIdList):
    fp = open(URIAbzIdList)
    recs = [l.strip() for l in fp.readlines()]
    return set(recs)


class SalamiEntry():
    
    def __init__(self, title, artist, key):
      self.title= title
      self.artist = artist
      self.key = key  
    
    
def search_artist(queryArtistname):
    listArtists = mb.search_artists(artist=queryArtistname)['artist-list']
#    check that artists have correct name
    listArtistsRelevantNames = []
    for artist in listArtists:
        # check relevance of artist. TODO: break do offset and limit, not to miss artist 
        if artist['name'] == queryArtistname:
            listArtistsRelevantNames.append(artist)
     
    return listArtistsRelevantNames
        
        

def isRecordingInAbrainz( r, mbSet):
    return r["id"] in mbSet
               

def search_rec_with_artist(queryRecName, artist, mbSet):
    queryRecNameQuotes = '"%s"' % queryRecName
    
    artistMBID = artist['id']
    
    offset = 0
    limit = 100
    while True:
        result = mb.search_recordings(queryRecNameQuotes, arid=artistMBID, offset=offset, limit=limit)
        recs = result['recording-list']
    
        for r in recs:
            if not match( r['title'], queryRecName) :
                break
            
            # match recordingMBIDs in ABrainz
            if isRecordingInAbrainz(r, mbSet ):
                print "found recording with title {} with artist {} and with rec MBID {} in acoustic brainz".format(r["title"].encode('utf-8','replace'), artist["name"].encode('utf-8','replace'), r['id'].encode('utf-8','replace') )
                return r

        if offset > 200:
            print "Looked for this song in the 1000 first results but didn't find it, stopping"
            break
    
        offset += limit
    return None

def loadQueries(pathbillBoardFiles):

    queries = []
    URISalamis = []

    # get File Names
    for root, dirnames, filenames in os.walk(pathbillBoardFiles ):
        for filename in fnmatch.filter(filenames, 'salami_chords.txt'):
            
            URIsalami  = os.path.join(root, filename)
            
            # parse file
            fp = open(URIsalami)
            entries = fp.readlines()
            
            line1 = entries[0].strip()
            title = line1.split(':')[1].strip()
            
            line2 = entries[1].strip()
            artist = line2.split(':')[1].strip()
            
            line3 = entries[2].strip()
            name3 = line3.split(':')[0]
            
            line4 = entries[3].strip()
            name4 = line4.split(':')[0]
            
            
            if name3 == "# tonic":
                key = line3.split(':')[1].strip()
            elif name4 == "# tonic":
                key = line4.split(':')[1].strip()
            else: sys.exit("no key found. Exiting!") 
            
            
            fp.close()
            
            salamiEntry = SalamiEntry(title, artist, key)
            queries.append(salamiEntry)
            URISalamis.append(URIsalami)
    
    return queries, URISalamis
    
# def getArtistMBID(queryWorkTitle, queryArtist):
#     
#     artistMBID = 0
#     
#     
#     works = mb.search_works(queryWorkTitle)["work-list"]
#     for w in works:
#         for a in w.get("artist-relation-list", []):
#             a = a["artist"]
#             aname = a["name"]
#             wname = w["title"]
#             #if isinstance(aname, unicode):
#             #    aname = unidecode.unidecode(aname)
#             #if isinstance(wname, unicode):
#             #    wname = unidecode.unidecode(wname)
# # next 2 lines: matching a work by queryArtist (NOTE: in mb it is termed artist) and name 
#             anywork = match(queryWorkTitle, wname)
#             anyname = match(queryArtist, aname)
# 
# # here listing all recordings of found work:  
#             
# #             reclist = self.recordingids_for_work(w["id"])
# #             
# #             # second chance to match the artists name
# #             for n in self.aliases_for_artist(a["id"]):
# #                 anyname = anyname or self.match(queryArtist, n)
# #             # check if performer is not by chance the saught queryArtist
# #             for r in reclist:
# #                 for n in self.get_performance_credit_for_recording(r):
# #                     anyname = anyname or self.match(queryArtist, n)
# #             # do not know this one yet
# #             for wa in self.aliases_for_work(w["id"]):
# #             
# #                 print "matching a work alias", wa
# #                 anywork = anywork or self.match(queryWorkTitle, wa)
# #             if anywork and anyname:
# #                 print "  match: %s by %s - http://musicbrainz.org/work/%s" % (w["title"], aname, w["id"])
# #                 print "http://musicbrainz.org/work/%s" % (w["id"])
# # 
# #     
#     return artistMBID 


def prependLineToFile(URI_file, lineText):
    f = open(URI_file,'r')
    temp = f.read()
    f.close()

    f = open(URI_file, 'w')
    f.write(lineText)

    f.write(temp)
    f.close()
    
    
    
def doit(argv):
    
    if len(argv) != 3:
            print "Tool to match the ground truth chords annotations of McGill-Billboard_Chords to abzRecordings\n\n"
            print ("usage: {}  <URI_abzRecordings>  <URI_McGill-Billboard_Chords>".format(argv[0]) )
            print "<URI_abzRecordings> can be found on abz server \n <URI_McGill-Billboard_Chords> can be found here http://ddmal.music.mcgill.ca/billboard" 
            sys.exit();
    
#     URIAbzIdList  = '/Users/joro/Downloads/abzrecordings'
    URIAbzIdList = argv[1]

    
    mbSet = load_mbidlist(URIAbzIdList)
    # result: recording MBID -> key
    matchedDict = {}
    
#     pathbillBoardFiles= '/Users/joro/Downloads/McGill-Billboard_Chords'
    pathbillBoardFiles = argv[2]
    queries, URISalamis = loadQueries(pathbillBoardFiles)
    lengthQueries =len(queries) 
    
    for index, (salamiQuery, currURIsalami) in enumerate(zip(queries, URISalamis)):
        logging.info("finding match for query {} out of {}".format(index, lengthQueries))  
        queryArtist = salamiQuery.artist
        queryRecordingTitle = salamiQuery.title
        
    #     queryArtist = 'Bette Midler'
    #     queryRecordingTitle = 'The Rose'

        # salamiQuery artist_MBID by ArtistName  
        listArtists = search_artist(queryArtist)
        
        for artist in listArtists:
            
            # salamiQuery composition_MBID by artist_MBID and Recording Title
            recording = search_rec_with_artist(queryRecordingTitle, artist, mbSet)    
            if recording!= None:
                
                matchedDict[recording["id"]] = salamiQuery.key
#                 prependLineToFile(currURIsalami, recording["id"])
        print matchedDict
               
                
    print " Finished! \n {} recordings found ".format(len( matchedDict))
    # serielize to file 
    with open('mapRecID2Key.txt', 'w') as f:
        json.dump(matchedDict, f, sort_keys = True, indent = 4, ensure_ascii=False)
                                                    
if __name__ == "__main__":
    doit(sys.argv)
    