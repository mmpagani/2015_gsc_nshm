# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 16:17:40 2014

@author: tallen
"""

def return_annualised_haz_curves(hazcurvefile):
    from openquake.nrmllib.hazard.parsers import HazardCurveXMLParser
    hcm = HazardCurveXMLParser(hazcurvefile).parse()
    from numpy import array, log
    
    #extract curve lat/lons from POES
    curvelat = []
    curvelon = []
    hazcurves = []
    for loc, poes in hcm:
        curvelon.append(loc.x)
        curvelat.append(loc.y)
        hazcurves.append((poes))
    
    curvelon = array(curvelon)  
    curvelat = array(curvelat)
    hazcurves = array(hazcurves)
    
    investigation_time = float(hcm.metadata['investigation_time'])
    
    annual_hazcurves = []
    for i, hazcurve in enumerate(hazcurves):
        # for curves, plot annual probablility - need to check this!
        P0 = 1 - hazcurve
        n = -1*log(P0)
        annual_hazcurves.append(n / investigation_time)
        
    return annual_hazcurves, curvelon, curvelat, hcm.metadata
    
# return curves for given time interval
def return_haz_curves(hazcurvefile):
    from openquake.nrmllib.hazard.parsers import HazardCurveXMLParser
    hcm = HazardCurveXMLParser(hazcurvefile).parse()
    from numpy import array
    
    #extract curve lat/lons from POES
    curvelat = []
    curvelon = []
    hazcurves = []
    for loc, poes in hcm:
        curvelon.append(loc.x)
        curvelat.append(loc.y)
        hazcurves.append((poes))
    
    curvelon = array(curvelon)  
    curvelat = array(curvelat)
    hazcurves = array(hazcurves)
        
    return hazcurves, curvelon, curvelat, hcm.metadata    

# script to interpolate across nearby sites to derive hazard curve for site of interest
# also return hazard type (e.g. mean, median, quantile)
def interp_hazard_curve(sitelon, sitelat, hazcurvefile):
    from openquake.nrmllib.hazard.parsers import HazardCurveXMLParser
    from numpy import array, where
    from scipy import interpolate
    import warnings
    warnings.filterwarnings("ignore")
    
    
    hcm = HazardCurveXMLParser(hazcurvefile).parse()
    
    #curves = hcc._set_curves_matrix(hcm)
    
    #extract lat/lons from POES
    curlat = []
    curlon = []
    curves = []
    for loc, poes in hcm:
        curlon.append(loc.x)
        curlat.append(loc.y)
        curves.append((poes))
    
    curlon = array(curlon)  
    curlat = array(curlat)
    curves = array(curves)
    
    # check to see if site within model
    if sitelat >= min(curlat) and sitelat <= max(curlat) \
       and sitelon >= min(curlon) and sitelon <= max(curlon):
        
        # find indexes about site
        index1 = where((curlon >= sitelon-1.) & (curlon <= sitelon+1.) \
                       & (curlat >= sitelat-1.) & (curlat <= sitelat+1.))[0]
        
    lonstrip = array(curlon)
    latstrip = array(curlat)
    curstrip = array(curves)
        
    # build array of poes for each return period
    interphazcurve = []
    for i in range(0, len(curstrip[0])):
        poearray = []
        for c in curstrip:
            poearray.append(c[i])
        
        # standard 2D interpolation does not work!      
        '''
        # do 2D interpolation across log values
        interpfunc = interpolate.interp2d(lonstrip, latstrip, \
                                          log(array(poearray)), kind='linear')
        interphazcurve.append(exp(interpfunc(sitelon, sitelat)[0]))
        '''
        # use SmoothBivariateSpline instead
        '''
        # smooth ln hazard - changed to linear b/c cannot interp log(0)                              
        interpfunc = interpolate.SmoothBivariateSpline(lonstrip, latstrip, \
                                                       log(array(poearray)))
        # evaluate SmoothBivariateSpline                                  
        interphazcurve.append(exp(interpfunc.ev(sitelon, sitelat)))
        '''
        # smooth hazard                              
        interpfunc = interpolate.SmoothBivariateSpline(lonstrip, latstrip, \
                                                       array(poearray))
        # evaluate SmoothBivariateSpline                                  
        interphazcurve.append(interpfunc.ev(sitelon, sitelat))
            
    return array(interphazcurve), hcm.metadata, curstrip

'''
hazcurves is an array of poes 
'''
def plt_haz_curves(plt, hazcurves, metadata, sitename, **kwargs):
    '''
    kwargs:
        ext_curve: external curve (e.g. 2015 NBCC) in 2 x n array - [[imts] [poes]]
        ext_label: label for external hazard curve
        ampfact: factor for converting from B/C to C, etc
        xmaxlim: max x limit
        legendtxt: list of text for legend 
    '''
    from numpy import nan, isnan
    
    drawextcurve = False
    ampfact = 1.
    xmaxlim = nan
    legendtxt = []
    keys = ['ext_curve', 'ext_label', 'ampfact', 'xmaxlim']
    for key in keys:
        if key in kwargs:
            if key == 'ext_curve':
                ext_curves = kwargs[key]
                drawextcurve = True
                
            if key == 'ext_label':
                ext_label = kwargs[key]
            
            #amplification factor 
            if key == 'ampfact':
                ampfact = kwargs[key]
                
            #x limit 
            if key == 'xmaxlim':
                xmaxlim = kwargs[key]
                
             #legend 
            if key == 'legendtxt':
                legendtxt = kwargs[key]
    
    from numpy import arange, log
    
    #investigation_time = float(metadata['investigation_time'])
       
    ncurves = len(hazcurves)
    #plt.figure(1, figsize=(10, 10))
    cmap = plt.cm.get_cmap('hsv', ncurves+1)
    cs = (cmap(arange(ncurves)))
    
    # plot annualised OQ curves
    labels = ['OpenQuake']
    for i, hazcurve in enumerate(hazcurves):
        # for curves, plot annual probablility - need to check this!
        '''        
        P0 = 1 - hazcurve
        n = -1*log(P0)
        adj_hazcurve = n / investigation_time       
        '''
        plt.semilogy(metadata['imls'], hazcurve*ampfact, color=[cs[i][0],cs[i][1],cs[i][2]], lw=2.5)
        
    # plot external curves
    if drawextcurve == True:
        plt.semilogy(ext_curves[0], ext_curves[1], 'k-', lw=2.5)
        labels.append(ext_label)
        
        
    # make pretty
    plt.ylabel('Annual Probabability of Exceedance', fontsize=12)
    if metadata['statistics'] == 'mean':
        if metadata['imt'] == 'PGA' or metadata['imt'] == 'PGV':
            plt.xlabel(' '.join(('Mean ',metadata['imt'], 'Hazard (g)')), fontsize=12)
        else:
            plt.xlabel(' '.join(('Mean ',metadata['sa_period'], 's Hazard (g)')), fontsize=12)
    else:
        pctile = str(int(float(metadata['quantile_value'])*100))
        if metadata['imt'] == 'PGA' or metadata['imt'] == 'PGV':
            plt.xlabel(''.join((pctile, r'$^{th}$', ' Percentile ',metadata['imt'], \
                                ' Hazard (g)')), fontsize=12)
        else:
            plt.xlabel(''.join((pctile, r'$^{th}$', ' Percentile ',metadata['sa_period'], \
                                ' s Hazard (g)')), fontsize=12)
                                
    # plot 1/475 and 1/2475 yr lines
    ax = plt.gca()
    ymax = ax.get_ylim()[1]
    plt.ylim([2e-5, ymax])
    if isnan(xmaxlim):
        xmax = ax.get_xlim()[1]
    else:
        xmax = xmaxlim
    #prob10 = 1/475.
    prob02 = 1/2475.
    #plt.semilogy([0., xmax],[prob10, prob10],'k--') # temp only - interp to get value
    plt.semilogy([0., xmax],[prob02, prob02],'k--', lw=1.75) # 1/2,475 yrs
    
    plt.xlim([0, xmax])
    plt.title('Site: '+sitename)
    plt.grid(True, which='both')
    plt.legend(labels, loc=1)
    
    return plt 
    
# function to map hazard
def map_haz(fig, plt, haz_map_file, sitelon, sitelat, **kwargs):
    '''
    kwargs:
        shpfile: path to area source - is a list of files
        resolution: c (crude), l (low), i (intermediate), h (high), f (full)
        mbuffer: map buffer in degrees
    '''

    from oq_output.hazard_map_converter import parse_nrml_hazard_map
    from mpl_toolkits.basemap import Basemap
    from numpy import arange, array, log10, mean, mgrid, percentile
    from matplotlib.mlab import griddata
    from matplotlib import colors, colorbar, cm
    from os import path
    from mapping_tools import drawshapepoly, labelpolygon
    import shapefile
    
    # set kwargs
    drawshape = False
    res = 'c'
    mbuff = -0.3
    keys = ['shapefile', 'resolution', 'mbuffer']
    for key in keys:
        if key in kwargs:
            if key == 'shapefile':
                shpfile = kwargs[key]
                drawshape = True
                
            if key == 'resolution':
                res = kwargs[key]
                
            if key == 'mbuffer':
                mbuff = kwargs[key]
    
    metadata, values = parse_nrml_hazard_map(haz_map_file)
    
    hazvals = []
    latlist = []
    lonlist = []
    for val in values:    
        lonlist.append(val[0])
        latlist.append(val[1])
        hazvals.append(val[2])

    # get map bounds
    llcrnrlat = min(latlist) - mbuff/2.
    urcrnrlat = max(latlist) + mbuff/2.
    llcrnrlon = min(lonlist) - mbuff
    urcrnrlon = max(lonlist) + mbuff
    lon_0 = mean([llcrnrlon, urcrnrlon])
    lat_1 = percentile([llcrnrlat, urcrnrlat], 25)
    lat_2 = percentile([llcrnrlat, urcrnrlat], 75)
    
    m = Basemap(llcrnrlon=llcrnrlon,llcrnrlat=llcrnrlat, \
                urcrnrlon=urcrnrlon,urcrnrlat=urcrnrlat,
                projection='lcc',lat_1=lat_1,lat_2=lat_2,lon_0=lon_0,
                resolution=res,area_thresh=1000.)
                
    m.drawcoastlines(linewidth=0.5,color='k')
    m.drawcountries()
    
    # draw parallels and meridians.
    m.drawparallels(arange(-90.,90.,1.), labels=[1,0,0,0],fontsize=10, dashes=[2, 2], color='0.5', linewidth=0.5)
    m.drawmeridians(arange(0.,360.,1.), labels=[0,0,0,1], fontsize=10, dashes=[2, 2], color='0.5', linewidth=0.5)
    
    # make regular grid
    N = 150j
    extent = (min(lonlist), max(lonlist), min(latlist), max(latlist))
    xs,ys = mgrid[extent[0]:extent[1]:N, extent[2]:extent[3]:N]
    resampled = griddata(array(lonlist),array(latlist), log10(array(hazvals)), xs, ys)
    
    #############################################################################
    # transform grid to basemap
    
    # get 1D lats and lons for map transform
    lons = ogrid[extent[0]:extent[1]:N]
    lats = ogrid[extent[2]:extent[3]:N]
    
    # transform to map projection
    if max(lonlist) - min(lonlist) < 1: 
        transspace = 500
    elif max(lonlist) - min(lonlist) < 5: 
        transspace = 1000
    elif max(lonlist) - min(lonlist) < 10: 
        transspace = 2000
    else: 
        transspace = 5000
        
    nx = int((m.xmax-m.xmin)/transspace)+1
    ny = int((m.ymax-m.ymin)/transspace)+1
    transhaz = m.transform_scalar(resampled.T,lons,lats,nx,ny)
    
    m.imshow(transhaz, cmap='Spectral_r', extent=extent, vmin=-2, vmax=log10(2.), zorder=0)
    
    # plot site
    xx, yy = m(sitelon,sitelat)
    plt.plot(xx, yy, '*', ms=20, mec='k', mew=2.0,  mfc="None")
    
    # superimpose area source shapefile
    if drawshape == True:
        for shp in shpfile:
            sf = shapefile.Reader(shp)
            drawshapepoly(m, plt, sf, col='k', lw=1.5, polyline=True)
            labelpolygon(m, plt, sf, 'CODE', fsize=14)    
    
    # set colourbar
    # set cb for final fig
    plt.gcf().subplots_adjust(bottom=0.1)
    cax = fig.add_axes([0.6,0.05,0.25,0.02]) # setup colorbar axes.
    norm = colors.Normalize(vmin=-2, vmax=log10(2.))
    cb = colorbar.ColorbarBase(cax, cmap=cm.Spectral_r, norm=norm, orientation='horizontal')
    
    # set cb labels
    #linticks = array([0.01, 0.03, 0.1, 0.3 ])
    logticks = arange(-2, log10(2.), 0.25)
    cb.set_ticks(logticks)
    labels = [str('%0.2f' % 10**x) for x in logticks]
    cb.set_ticklabels(labels)
    
    # get map probabiltiy from filename
    mprob = path.split(haz_map_file)[-1].split('_')[-1].split('-')[0]
    probstr = str(int(float(mprob)*100))
    
    # set colourbar title    
    if metadata['statistics'] == 'mean':
        titlestr = ''.join((metadata['imt'], ' ', metadata['sa_period'], ' s ', \
                            probstr,'% in ',metadata['investigation_time'][0:-2], \
                            ' Year Mean Hazard (g)'))
        #cb.set_ticklabels(labels)
        cb.set_label(titlestr, fontsize=12)
        
    return plt 