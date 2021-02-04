import requests 
import os
import urllib.request
import re
 
import PIL
from PIL import Image

posters_dir = 'posters'

api_key = 'bf41c278b93f331151c6d37080b8b284'
api_v4_key = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiZjQxYzI3OGI5M2YzMzExNTFjNmQzNzA4MGI4YjI4NCIsInN1YiI6IjVlODRkNWFkZGExMGYwMDAxNmVjYjcxMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.d71jrPRyr7WFONDP5djWHjbvo10iV01kgcSFnLINcAI'

# Create output directory if necessary
try:
    os.mkdir(posters_dir)
    print(f"Directory \"{posters_dir}\" created ")
except FileExistsError:
    print(f"Directory \"{posters_dir}\" already exists")
print()

# Taken from https://www.python-course.eu/levenshtein_distance.php
def levenshtein(s, t):
    rows = len(s)+1
    cols = len(t)+1
    dist = [[0 for x in range(cols)] for x in range(rows)]

    for i in range(1, rows):
        dist[i][0] = i

    for i in range(1, cols):
        dist[0][i] = i
        
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0
            else:
                cost = 1
            dist[row][col] = min(dist[row-1][col] + 1,      # deletion
                                 dist[row][col-1] + 1,      # insertion
                                 dist[row-1][col-1] + cost) # substitution
    
    return dist[row][col]

def get_imdb_img(title, output_filename):
    print("\tSearching for: " + title)

    response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}", params = {'query':title})
    response_json_results = response.json()['results']

    # The correct movie/show is not always the first one in the response, so we look for the response listing with an exact match or the least difference.
    curr_reponse_index = 0
    curr_closest_levenshtein = float('inf')
    curr_closest_index = 0
    for response_json_result in response_json_results:
        curr_levenshtein = levenshtein(title, response_json_result['title'])
        if curr_levenshtein == 0:
            curr_closest_levenshtein = curr_levenshtein
            curr_closest_index = curr_reponse_index
            break
        elif curr_levenshtein < curr_closest_levenshtein:
            curr_closest_levenshtein = curr_levenshtein
            curr_closest_index = curr_reponse_index
        curr_reponse_index += 1

    best_reponse_index = curr_closest_index

    if (len(response_json_results) == 0) or ('poster_path' not in response_json_results[best_reponse_index]):
        print(f"\tCouldn't find {title}")
        return False

    poster_path = response_json_results[best_reponse_index]['poster_path']

    if poster_path is None:
        print(f"\tCouldn't find {title}")
        return False

    #w500_base_url = 'https://image.tmdb.org/t/p/w500'
    original_base_url = 'https://image.tmdb.org/t/p/original'

    urllib.request.urlretrieve(original_base_url + poster_path, output_filename)

    img = Image.open(output_filename)
    img = img.resize((600, 900), PIL.Image.ANTIALIAS)
    img.save(output_filename)

    return True


directory = 'D:\MOVIES'
fetched_titles = []
skipped_titles = []
failed_titles = []

for filename in os.listdir(directory):
    if filename.endswith(".mp4") or filename.endswith(".mkv"): 
        #print(os.path.join(directory, filename))
        title = filename[:-4]
        output_filename = posters_dir + "/" + title + ".jpg"
        
        if os.path.exists(output_filename):
            skipped_titles.append(title)
            #print("\tSkipping " + output_filename)
            continue

        print("Fetching " + title + "...")
        if get_imdb_img(title, output_filename):
            fetched_titles.append(title)
            print("...Successfully fetched " + title)
        else:
            print("...Failed to fetch " + title)
            failed_titles.append(title)

    elif os.path.isdir(os.path.join(directory, filename)):
        #print(os.path.join(directory, filename))
        title = filename
        output_filename = posters_dir + "/" + title + ".jpg"

        if os.path.exists(output_filename):
            skipped_titles.append(title)
            #print("\tSkipping " + output_filename)
            continue
        
        print("Fetching " + title + "...")
        if get_imdb_img(title, output_filename):
            fetched_titles.append(title)
            print("Sucessfully fetched " + title)
        else:
            print("Failed to fetch " + title)
            failed_titles.append(title)

print()
print("===============================================")
print()
print("Fetched {} new posters.".format(len(fetched_titles)))
print("Skipped {} existing posters.".format(len(skipped_titles)))
print("Failed on {} posters.".format(len(failed_titles)))

if len(fetched_titles) > 0:
    print()
    print("Successful titles:")
    for fetched_title in fetched_titles:
        print(fetched_title)
if len(failed_titles) > 0:
    print()
    print("Failed titles:")
    for failed_title in failed_titles:
        print(failed_title)


