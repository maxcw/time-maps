import os,sys
import numpy as np
import matplotlib.pylab as plt
import scipy.ndimage as ndi
import datetime as dt
from twython import Twython
from colour import Color

def my_secrets(): # store your twitter codes
	
    d={}
    d['APP_KEY']="--"
    d['APP_SECRET']="--"
    d['my_access_token_key']="--"
    d['my_access_token_secret']="--"
	
    return d

def twitter_auth2(): # for Twython authentication
    
	secrets=my_secrets()
	
	APP_KEY=secrets['APP_KEY']
	APP_SECRET=secrets['APP_SECRET']
	my_access_token_key=secrets['my_access_token_key']
	my_access_token_secret=secrets['my_access_token_secret']
	
	twitter = Twython(APP_KEY, APP_SECRET,oauth_version=2)
	ACCESS_TOKEN = twitter.obtain_access_token()
	twitter = Twython(APP_KEY,access_token=ACCESS_TOKEN)
	
	return twitter

def get_dt(t): # converts a twitter time string to a datetime object
	
	splitted = t.split(' ')
	
	new_string = ' '.join(splitted[:4])+' '+splitted[-1]
	
	my_datetime = dt.datetime.strptime(new_string,'%c')
	
	return my_datetime

def grab_tweets(name_to_get): # download a user's twitter timeline, returning a list of tweets
	
	print 'downloading tweets:'
	
	twitter = twitter_auth2()
	
	first = twitter.get_user_timeline(screen_name=name_to_get, count=1)
	
	lis=[first[0]['id']] # list of tweet id's
	
	all_tweets=[]
	
	N_packets=16 # since packets come with 200 tweets each, this will add up to 3,200 (the maximum amount)
	
	for i in range(N_packets):

		print 'tweet packet =',i+1
		
		user_timeline=twitter.get_user_timeline(screen_name=name_to_get, count=200, max_id=lis[-1]-1)
		# if max_id=lis[-1], the earliest tweet from the last packet will be included as well
		
		all_tweets += user_timeline
		
		if(i==0):
			
			lis = [tweet['id'] for tweet in user_timeline]
		
		else:
			
			lis += [tweet['id'] for tweet in user_timeline]
	
	tweet_ids=[tweet['id'] for tweet in all_tweets]
	
	print 'number of unique tweets:', len(set(tweet_ids))
	
	return all_tweets

def make_heated_time_map(sep_array, Nside, width):

	print 'generating heated time map ...'
	
	# choose points within specified range. Example plot separations greater than 5 minutes:
#	indices = (sep_array[:,0]>5*60) & (sep_array[:,1]>5*60)
	indices=range(sep_array.shape[0]) # all time separations

	x_pts = np.log(sep_array[indices,0])
	y_pts = np.log(sep_array[indices,1])

	min_val = np.min([np.min(x_pts), np.min(y_pts)])
	
	x_pts = x_pts - min_val
	y_pts = y_pts - min_val
	
	max_val = np.max([np.max(x_pts), np.max(y_pts)])
	
	x_pts *= (Nside-1)/max_val
	y_pts *= (Nside-1)/max_val
	
	img=np.zeros((Nside,Nside))

	for i in range(len(x_pts)):

		img[x_pts[i],y_pts[i]] +=1

	img = ndi.gaussian_filter(img,width) # apply Gaussian filter
	
	img = np.sqrt(img) # taking the square root makes the lower values more visible

	img=np.transpose(img) # needed so the orientation is the same as scatterplot

	plt.imshow(img, origin='lower')
	
	## create custom tick marks. Calculate positions of tick marks on the transformed log scale of the image array
	
	plt.minorticks_off()
	
	## change font, which can also now accept latex: http://matplotlib.org/users/usetex.html
	plt.rc('text',usetex=False)
	plt.rc('font',family='serif')

	my_max = np.max([np.max(sep_array[indices,0]), np.max(sep_array[indices,1])])
	my_min = np.max([np.min(sep_array[indices,0]), np.min(sep_array[indices,1])])

	pure_ticks = np.array([1e-3,1,10,60*10,2*3600,1*24*3600, 7*24*3600])         # where the tick marks will be placed, in units of seconds. An additional value will be appended to the end for the max
	labels = ['1 msec','1 sec','10 sec','10 min','2 hr','1 day','1 week']  # tick labels

	index_lower=np.min(np.nonzero(pure_ticks >= my_min)) # index of minimum tick that is greater than or equal to the smallest time interval. This will be the first tick with a non-blank label
	
	index_upper=np.max(np.nonzero(pure_ticks <= my_max))
	
	ticks = pure_ticks[index_lower: index_upper + 1]
	ticks = np.log(np.hstack((my_min, ticks, my_max ))) # append values to beginning and end in order to specify the limits
	ticks = ticks - min_val
	ticks *= (Nside-1)/(max_val)
	
	labels= np.hstack(('',labels[index_lower:index_upper + 1],'')) # append blank labels to beginning and end
	
	plt.xticks(ticks, labels,fontsize=16)
	plt.yticks(ticks, labels,fontsize=16)

	plt.xlabel('Time Before Tweet',fontsize=18)
	plt.ylabel('Time After Tweet' ,fontsize=18)
	
	plt.show()

	return None

def make_time_map(times, times_tot_mins, sep_array, Ncolors):

	print 'rendering normal time map ...'
	
	## set up color list
	
	red=Color("red")
	blue=Color("blue")
	color_list = list(red.range_to(blue, Ncolors)) # range of colors evenly speced on the spectrum between red and blue. Each element is a colour object
	color_list = [c.hex for c in color_list] # give hex version
		
	fig=plt.figure()
	ax =fig.add_subplot(111)
	
	plt.rc('text',usetex=False)
	plt.rc('font',family='serif')
	
	colormap = plt.cm.get_cmap('rainbow')  # see color maps at http://matplotlib.org/users/colormaps.html
	
	order=np.argsort(times_tot_mins[1:-1]) # so that the red dots are on top
#	order=np.arange(1,len(times_tot_mins)-2) # dots are unsorted

	# taken from http://stackoverflow.com/questions/6063876/matplotlib-colorbar-for-scatter
	
	sc= ax.scatter(sep_array[:,0][order],sep_array[:,1][order],c=times_tot_mins[1:-1][order],vmin=0,vmax=24*60,s=25,cmap=colormap,marker='o',edgecolors='none')
	
	color_bar=fig.colorbar(sc,ticks=[0,24*15,24*30,24*45,24*60],orientation='horizontal',shrink=0.5)
	color_bar.ax.set_xticklabels(['Midnight','18:00','Noon','6:00','Midnight'])
	color_bar.ax.invert_xaxis()
	color_bar.ax.tick_params(labelsize=16)
	
	ax.set_yscale('log') # logarithmic axes
	ax.set_xscale('log')
	
	plt.minorticks_off()
	
	pure_ticks = np.array([1e-3,1,10,60*10,2*3600,1*24*3600, 7*24*3600]) # where the tick marks will be placed, in units of seconds.
	labels = ['1 msec','1 sec','10 sec','10 min','2 hr','1 day','1 week']  # tick labels
	
	max_val = np.max([np.max(sep_array[:,0]), np.max(sep_array[:,1])])
	
	ticks = np.hstack((pure_ticks, max_val))
	
	min_val = np.min([np.min(sep_array[:,0]), np.min(sep_array[:,1])])
	
	plt.xticks(ticks,labels,fontsize=16)
	plt.yticks(ticks,labels,fontsize=16)
	
	plt.xlabel('Time Before Tweet',fontsize=18)
	plt.ylabel('Time After Tweet',fontsize=18)
	
	plt.xlim((min_val, max_val))
	plt.ylim((min_val, max_val))
	
	ax.set_aspect('equal')
	
	plt.tight_layout()
	
	plt.show()

	return None

def analyze_tweet_times(name_to_get, all_tweets, HEAT):
	
	all_tweets = all_tweets[::-1] # reverse order so that most recent tweets are at the end

	times=[get_dt(tweet['created_at']) for tweet in all_tweets]
	
	timezone_shift=dt.timedelta(hours=4) # times are in GMT. Convert to eastern time.
	
	times = [time-timezone_shift for time in times]
	
	times_tot_mins = 24*60 - (60*np.array([t.hour for t in times]) + np.array([t.minute for t in times])) # 24*60 - number of minutes since midnight

	seps=np.array([(times[i]-times[i-1]).total_seconds() for i in range(1,len(times))])

	seps[seps==0]=1 # convert zero second separations to 1-second separations

	sep_array=np.zeros((len(seps)-1,3)) # 1st column: x-coords, 2nd column: y-coords, 3rd column: times

	sep_array[:,0]=seps[:-1]
	sep_array[:,1]=seps[1:]

	if(HEAT):
	
		Nside=4*256 # number of pixels along the x and y directions
		width=4 # the number of pixels that specifies the width of the Gaussians for the Gaussian filter

		make_heated_time_map(sep_array, Nside, width)

	else:
	
		Ncolors=24*60 # a different shade for each minute
	
		make_time_map(times, times_tot_mins, sep_array, Ncolors)

	print 'writing eps file...'
	print 'To avoid cluttered labels, you may have to expand the plotting window by dragging, and then save the figure'
	print 'to save as an eps, type: plt.savefig("filename.eps", format="eps",bbox_inches="tight", dpi=200)'
	print ''
	print 'Done!'
	
	plt.savefig(name_to_get+'.eps', format='eps',bbox_inches='tight', dpi=200) # save as eps

	return times,times_tot_mins,sep_array






