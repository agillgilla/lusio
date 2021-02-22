import os
import sys
import re

season_delimiter = 'S'
episode_delimiter = 'E'
file_suffix = '.mp4'
dry_run = False
episodes_directory = 'D:\\MOVIES\\The New Adventures of Old Christine'

new_episodes_file = open('naooc.txt', 'r')

for folder, subs, files in os.walk(episodes_directory):
	#print(folder)
	#print(subs)
	#print(files)
	for file in sorted(files):
		if file.endswith(file_suffix):
			season_episode_pair = file.split(season_delimiter)
			season_episode_pair = season_episode_pair[1].split(episode_delimiter)
			season_episode_pair[1] = season_episode_pair[1].split(file_suffix)[0]

			season_str = str(season_episode_pair[0])
			if int(season_str) < 10:
				season_str = '0' + season_str

			episode_str = str(season_episode_pair[1])
			if int(episode_str) < 10:
				episode_str = '0' + episode_str

			#new_filename = season_delimiter + season_str + episode_delimiter + episode_str + file_suffix

			episode_name = new_episodes_file.readline().rstrip()

			new_filename = file.split(file_suffix)[0] + " (" + episode_name + ")" + file_suffix

			new_filename = new_filename.replace(':', ' -')
			new_filename = new_filename.replace('?', '')
			new_filename = new_filename.replace('/', ',')

			if not dry_run:
				os.rename(os.path.join(folder, file), os.path.join(folder, new_filename))

			print(file + "\t >> \t" + new_filename)
			

#    """with open(os.path.join(folder, 'python-outfile.txt'), 'w') as dest:
#        for filename in files:
#            with open(os.path.join(folder, filename), 'r') as src:
#                dest.write(src.read())"""