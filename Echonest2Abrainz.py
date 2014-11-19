'''
Created on Nov 18, 2014

@author: joro
'''
import re

import musicbrainzngs as mb
import Levenshtein
import os
import fnmatch
import sys
mb.set_useragent("Dunya", "0.1")
mb.set_rate_limit(False)
mb.set_hostname("musicbrainz.s.upf.edu")




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
    
    def __init__(self, title, artist):
      self.title= title
      self.artist = artist  
    
    
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
                print "found recording with title {} with artist {} and with rec MBID {} in acoustic brainz".format(r["title"], artist["name"], r["id"])
                return r

        if offset > 1000:
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
            fp.close()
            
            salamiEntry = SalamiEntry(title, artist)
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
    listMatchedRecordings = []
    
#     pathbillBoardFiles= '/Users/joro/Downloads/McGill-Billboard_Chords'
    pathbillBoardFiles = argv[2]
    queries, URISalamis = loadQueries(pathbillBoardFiles)
    
    for query, currURIsalami in zip(queries, URISalamis): 
        queryArtist = query.artist
        queryRecordingTitle = query.title
        
    #     queryArtist = 'Bette Midler'
    #     queryRecordingTitle = 'The Rose'

        # query artist_MBID by ArtistName  
        listArtists = search_artist(queryArtist)
        
        for artist in listArtists:
            
            
            
            # query composition_MBID by artist_MBID and Recording Title
            recording = search_rec_with_artist(queryRecordingTitle, artist, mbSet)    
            if recording!= None:
                
                prependLineToFile(currURIsalami, recording["id"])
               
                
                listMatchedRecordings.append(recording)
    print " Finished! \n {} recordings found ".format(len( listMatchedRecordings))
                                                    
if __name__ == "__main__":
    doit(sys.argv)
    