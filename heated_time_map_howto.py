import numpy as np
import scipy.ndimage as ndi
import matplotlib.pylab as plt

# this code shows how to create a smoothed heatmap of a scatterplot using a Gaussian filter
# see also http://stackoverflow.com/questions/6652671/efficient-method-of-calculating-density-of-irregularly-spaced-points

# use random xy coordinates
xcoords = np.random.normal(0, 0.1, 10000)
ycoords = np.random.normal(0, 0.3, 10000)

indices= (xcoords>0) & (xcoords<1) & (ycoords>0) & (ycoords<1) # indices of points between zero and one

xcoords=xcoords[indices] # only use xy coords between zero and one, for simplicity
ycoords=ycoords[indices]

plt.subplot(121) # first, a plot of the points themselves

plt.plot(xcoords,ycoords,'b.')

plt.xlim((0,1))
plt.ylim((0,1))

plt.subplot(122) # let's make a heatmap

Nside=1024 # this is the number of bins along x and y.

H = np.zeros((Nside,Nside)) # the 'histogram' matrix that counts the number of points in each grid-square

x_heat = (Nside-1)*xcoords # the xy coordinates scaled to the size of the matrix
y_heat = (Nside-1)*ycoords # subtract 1 since Python starts counting at 0, unlike Fortran and R

for i in range(len(xcoords)): # loop over all points to calculate the population of each bin
	
	H[int(x_heat[i]), int(y_heat[i])] = H[int(x_heat[i]), int(y_heat[i])] + 1 # int() outputs an integer.

	# in Python, the above line can actually be accomplished more compactly:
	# H[x_heat[i], y_heat[i]]  +=1

H = ndi.gaussian_filter(H,8) # here, 8 specifies the width of the Gaussian kernel in the x and y directions
H = np.transpose(H) # so that the orientation is the same as the scatter plot
# to bring out the individual points more, you can do: H=np.sqrt(H)
plt.imshow(H, origin='lower')

plt.show()
