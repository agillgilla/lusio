import os
import json
import requests

OMDB_API_KEY = '52002791'

MEDIA_INFO_FILENAME = 'media_info.json'

existing_titles = set()

media_info_dict = {}

try:
    with open(MEDIA_INFO_FILENAME, 'r+') as info_json_file:
        media_info_dict = json.load(info_json_file)
        for media_info in media_info_dict:
            existing_titles.add(media_info)
except FileNotFoundError as fnfe:
    print("The JSON file wasn't found.  A new one will be created.")

directory = 'D:\MOVIES'
fetched_titles = []
skipped_titles = []
failed_titles = []

omdb_api_base_url = 'http://www.omdbapi.com/'

def get_info(title):
    request_url = omdb_api_base_url + title

    try:
        response = requests.get(omdb_api_base_url, params = {'apikey' : OMDB_API_KEY, 't' : title})
        response_json_results = response.json()
        #print(response_json_results)

        media_info = {}

        media_info['title'] = response_json_results['Title']
        media_info['year'] = response_json_results['Year']
        media_info['rated'] = response_json_results['Rated']
        media_info['runtime'] = response_json_results['Runtime']
        media_info['genre'] = response_json_results['Genre']
        media_info['plot'] = response_json_results['Plot']
        media_info['director'] = response_json_results['Director']
        media_info['actors'] = response_json_results['Actors']

        for rating in response_json_results['Ratings']:
            if rating['Source'] == 'Internet Movie Database':
                media_info['rating_imdb'] = rating['Value']
            elif rating['Source'] == 'Rotten Tomatoes':
                media_info['rating_rotten'] = rating['Value']
            elif rating['Source'] == 'Metacritic':
                media_info['rating_meta'] = rating['Value']

        return media_info

    except Exception as e:
        print(e)

    return None

for filename in os.listdir(directory):
    if filename.endswith(".mp4") or filename.endswith(".mkv"): 
        #print(os.path.join(directory, filename))
        title = filename[:-4]
    elif os.path.isdir(os.path.join(directory, filename)):
        if filename.endswith(' x265'):
            title = filename[:-5]
        else:
            title = filename
    else:
        continue
    
    if title in media_info_dict:
        skipped_titles.append(title)
        #print("\tSkipping " + output_filename)
        continue

    print("Fetching info for " + title + "...")
    media_info = get_info(title)
    if media_info is not None:
        #media_info_dict['media_infos'].append(media_info)
        media_info_dict[title] = media_info
        fetched_titles.append(title)
        print("...Successfully fetched info for " + title)
    else:
        print("...Failed to fetch info for " + title)
        failed_titles.append(title)

print()
print("===============================================")
print()
print("Fetched {} new infos.".format(len(fetched_titles)))
print("Skipped {} existing infos.".format(len(skipped_titles)))
print("Failed on {} infos.".format(len(failed_titles)))

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


with open(MEDIA_INFO_FILENAME, 'w') as info_json_file:
    json.dump(media_info_dict, info_json_file, indent=4, sort_keys=True)
