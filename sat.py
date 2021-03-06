import numpy as np
from urllib import urlretrieve
import ipdb
import matplotlib.pylab as pl

# Create your own satellite-image-only map on mapbox.  
# I deleted the following one to prevent future charges, 
# but the address should look something like this.
http_base='http://api.tiles.mapbox.com/v2/rkeisler.gh8kebdo/'

# Define the path for saving stuff.
basepath = '/Users/rkeisler/Desktop/satellite/'
imgpath = basepath+'img/'
labelpath = basepath+'label/'

def do_everything():
    download_chunk('atx',19)
    label_data('atx', size=2000)
    get_colors(name='pool',ncolors=10, quick=False)
    rf, colors = train_classifier(prefix='atx', nside=32, ds=4, color_thresh=30)
    xtile, ytile, proba = predict_proba_all(rf, colors)
    write_to_csv(xtile, ytile, proba, 'atx')    

def latlong_to_xyz(lat_deg, lon_deg, zoom):
    lat_rad = lat_deg*np.pi/180.
    lon_rad = lon_deg*np.pi/180.
    n = 2. ** zoom
    xtile = n * ((lon_deg + 180) / 360)
    ytile = n * (1 - (np.log(np.tan(lat_rad) + 1./np.cos(lat_rad)) / np.pi)) / 2.
    return int(xtile), int(ytile), zoom

def xyz_to_latlong(x, y, zoom):
  n = 2.0 ** zoom
  lon_deg = x / n * 360.0 - 180.0
  lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * y / n)))
  lat_deg = np.degrees(lat_rad)
  return (lat_deg, lon_deg)

def latlong_to_xyz(lat_deg, lon_deg, zoom):
    lat_rad = lat_deg*np.pi/180.
    lon_rad = lon_deg*np.pi/180.
    n = 2. ** zoom
    xtile = n * ((lon_deg + 180) / 360)
    ytile = n * (1 - (np.log(np.tan(lat_rad) + 1./np.cos(lat_rad)) / np.pi)) / 2.
    return int(xtile), int(ytile), zoom

def xyz_to_ZXY_string(x,y,z):
    return '%i/%i/%i'%(z,x,y)+'.png'

def latlong_to_ZXY_string(lat_deg, lon_deg, zoom):
    x,y,z = latlong_to_xyz(lat_deg, lon_deg, zoom)
    return xyz_to_ZXY_string(x,y,z)

def latlong_rectange_to_xyz(lat1, lat2, lon1, lon2, zoom):
    lat_min=np.min([lat1,lat2])
    lat_max=np.max([lat1,lat2])    
    lon_min=np.min([lon1,lon2])
    lon_max=np.max([lon1,lon2])        
    x_min, y_max, zoom = latlong_to_xyz(lat_min, lon_min, zoom)
    x_max, y_min, zoom = latlong_to_xyz(lat_max, lon_max, zoom)
    return x_min, x_max, y_min, y_max

def xyz_to_savename(x,y,z,prefix='tmp'):
    return prefix+'_x%i_y%i_z%i'%(x,y,z)+'.png'

def xyz_from_filename(filename):
    tmp=filename.split('/')[-1]
    xtmp = int(tmp.split('x')[-1].split('_')[0].split('.')[0])
    ytmp = int(tmp.split('y')[-1].split('_')[0].split('.')[0])
    ztmp = int(tmp.split('z')[-1].split('_')[0].split('.')[0])
    return xtmp, ytmp, ztmp

def hms_to_deg(hour, min, sec):
    return np.sign(hour)*(np.abs(hour)+min/60.+sec/3600.)

def download_one(x,y,zoom,prefix='tmp'):
    url=http_base+xyz_to_ZXY_string(x,y,zoom)+'.png'
    savename=imgpath+xyz_to_savename(x,y,zoom,prefix=prefix)
    urlretrieve(url, savename)

def download_chunk(name, zoom, download=True):
    d=define_chunk(name)
    download_rectangle(d['lat1'],d['lat2'],
                       d['lon1'],d['lon2'],
                       zoom, prefix=d['prefix'], 
                       download=download)
    
def download_rectangle(lat1, lat2, lon1, lon2, 
                       zoom, prefix='tmp', download=True):
    x_min, x_max, y_min, y_max = latlong_rectange_to_xyz(lat1, lat2, lon1, lon2, zoom)
    n_x = x_max-x_min
    n_y = y_max-y_min
    n_tiles = n_x*n_y
    x_count=0
    print 'Downloading X=(%i,%i), Y=(%i,%i)'%(x_min,x_max,y_min,y_max)
    print 'n_x: %i'%n_x
    print 'n_y: %i'%n_y
    print 'That is %i tiles.'%n_tiles
    if not(download): return
    for x_tmp in range(x_min, x_max):
        x_count+=1
        print '%i/%i'%(x_count,n_x)
        for y_tmp in range(y_min, y_max):
            download_one(x_tmp,y_tmp,zoom,prefix=prefix)


def define_chunk(name):
    atx=dict(prefix='atx',
             lat1=hms_to_deg(30,20,21.95),
             lat2=hms_to_deg(30,12,32.97),
             lon1=hms_to_deg(-97,50,33.81),
             lon2=hms_to_deg(-97,38,12.31))
    chunks=dict(atx=atx)
    return chunks[name]

 
def label_data(prefix, size=100, savename=None):
    from glob import glob
    from os.path import basename
    from PIL import Image
    from os.path import isfile
    if savename==None: savename=labelpath+'label_'+prefix+'.txt'
    # We want to avoid labeling an image twice, so keep track
    # of what we've labeled in previous labeling sessions.
    if isfile(savename):
        fileout = open(savename,'r')
        already_seen = [line.split(',')[0] for line in fileout]
        fileout.close()
    else: already_seen = []
    # Now reopen the file for appending.
    fileout = open(savename,'a')
    pl.ion()
    pl.figure(1,figsize=(9,9))
    files = glob(imgpath+prefix+'*.png')
    for file in np.random.choice(files, size=size, replace=False):
        if basename(file) in already_seen: continue
        pl.clf()
        pl.subplot(1,1,1)
        pl.imshow(np.array(Image.open(file)))
        pl.title(file)
        pl.axis('off')
        pl.draw()
        label = get_one_char()
        if label=='q': break
        fileout.write(basename(file)+','+label+'\n')
        print file,label
    fileout.close()
    return

def get_one_char():
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
    finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_label(prefix):
    savename = labelpath+'label_'+prefix+'.txt'
    file=open(savename,'r')
    n={}
    for line in file:
        tmp=line.split(',')
        if is_number(tmp[1]): n[tmp[0]]=int(tmp[1])
        else: n[tmp[0]]=0
    file.close()
    return n

def load_labeled(prefix='atx', nside=32, quick=False):
    import cPickle as pickle
    savename=basepath+'tmp_train_'+prefix+'_%i'%nside+'.pkl'
    if quick:
        X, y = pickle.load(open(savename,'r'))
        return X, y
    from PIL import Image
    tmp=read_label(prefix)
    X=[]; y=[]
    for name,label in tmp.iteritems():
        img_name = imgpath+name
        img = Image.open(img_name)
        if nside!=256: img=img.resize((nside,nside),Image.ANTIALIAS)
        img = np.array(img)
        if False:
            print img.shape
            pl.imshow(img)
            pdb.set_trace()
        X.append(img)
        y.append(label>0)
    X = np.array(X)
    y = np.array(y).astype(int)    
    pickle.dump((X,y), open(savename, 'w'))
    return X,y


def get_colors(name='pool',ncolors=10, quick=True):
    import cPickle as pickle
    savename = basepath+name+'.pkl'
    if quick: return pickle.load(open(savename,'r'))
    if name=='pool':
        base_colors = [[154, 211, 210], 
                       [104, 148, 156],
                       [70, 160, 162],
                       [93, 152, 140],
                       [58, 104, 99]]
    colors=[]; 
    for i in range(ncolors):
        for base_color in base_colors:
            colors.append(np.array(base_color)+np.random.randint(-30,high=20,size=3))
        colors.append(np.random.randint(0,high=255,size=3))
    pickle.dump(colors, open(savename,'w'))
    return colors
    

def get_features(X_img, colors, thresh=30, ds=4):
    nsamp=X_img.shape[0]
    nside=X_img.shape[1]
    features = []
    for color in colors:
        ok_color = np.product(np.abs(X_img - np.array(color))<thresh,axis=-1)
        sm_ok_color = ok_color.reshape(nsamp,nside/ds,ds,nside/ds,ds).mean(4).mean(2)
        max_sm = np.max(np.max(sm_ok_color,axis=-1),axis=-1)
        sum_sm = np.sum(np.sum(sm_ok_color,axis=-1),axis=-1)
        features.append(max_sm)
        features.append(sum_sm)
    features = np.vstack(features).T
    return features    
   
def train_classifier(prefix='atx', nside=32, ds=4, color_thresh=30, test_size=0.5):
    X_img,y=load_labeled(prefix=prefix,nside=nside,quick=False)
    if prefix=='atx': color_name='pool'
    colors = get_colors(name=color_name, quick=True)
    print '...getting features...'
    X = get_features(X_img, colors, ds=ds, thresh=color_thresh)
    print '...done getting features...'
    from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
    from sklearn.cross_validation import train_test_split
    from sklearn import metrics

    rf = ExtraTreesClassifier(n_estimators=200, n_jobs=6, max_features=0.02)
    X_train, X_test, y_train, y_test, img_train, img_test = train_test_split(X,y,X_img,test_size=0.5)
    print '...fitting...'
    rf.fit(X_train, y_train)
    y_proba = rf.predict_proba(X_test)[:,1]
    fpr, tpr, thresholds = metrics.roc_curve(y_test, y_proba)
    auc = metrics.auc(fpr, tpr)

    pl.clf(); pl.plot(fpr, tpr, 'b-o')
    pl.plot(fpr, fpr/np.mean(y), 'r--'); pl.ylim(0,1); pl.xlim(0,1)
    pl.title('AUC: %0.3f'%auc)

    for i,th in enumerate(thresholds): print th,tpr[i],tpr[i]/fpr[i]
    prob_thresh=0.6
    wh_missed=np.where((y_proba<prob_thresh)&(y_test==1))[0]
    wh_ok=np.where((y_proba>prob_thresh)&(y_test==1))[0]

def iimshow(img):
    pl.clf(); pl.imshow(np.array(img,dtype=np.uint8))
        
def predict_proba_all(classifier, colors, prefix='atx', batchsize=1000, nside=32):
    from glob import glob
    from PIL import Image
    files = glob(imgpath+prefix+'*.png')
    np.random.shuffle(files)
    nfiles = len(files)
    #nbatches=2 #tmpp
    nbatches = np.ceil(1.*nfiles/batchsize).astype(int)
    x=[]; y=[]; proba=[]
    for ibatch in range(nbatches):
        print ibatch,nbatches
        imgs = []
        imin=ibatch*batchsize
        imax=np.min([(ibatch+1)*batchsize, nfiles])
        # load and resize these images
        for file in files[imin:imax]:
            img = Image.open(file)
            if nside!=256: img=img.resize((nside,nside),Image.ANTIALIAS)
            img = np.array(img)
            imgs.append(img)
            xtmp, ytmp, ztmp = xyz_from_filename(file)
            x.append(xtmp)
            y.append(ytmp)
        this_X = get_features(np.array(imgs), colors)
        this_proba = classifier.predict_proba(this_X)[:,1]
        proba.append(this_proba)
    proba=np.hstack(proba)
    x=np.array(x)
    y=np.array(y)
    return x,y,proba

def write_to_csv(xtile,ytile,proba, proba_cut=0.4):
    wh=np.where(proba>proba_cut)[0]
    print len(wh)
    lat, lon = xyz_to_latlong(xtile[wh], ytile[wh], 19)
    medx=int(np.median(xtile))
    medy=int(np.median(ytile))
    dlat, dlon = xyz_to_latlong(np.array([medx,medx+1]), np.array([medy,medy+1]), 19)
    lat -= (0.5*(max(dlat)-min(dlat)))
    lon += (0.5*(max(dlon)-min(dlon)))
    file=open(prefix+'.csv','w')
    file.write('lat,lon\n')
    for this_lat, this_lon in zip(lat,lon):
        file.write('%0.7f,%0.7f'%(this_lat, this_lon)+'\n')
    file.close()


    
