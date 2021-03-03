COUNTRIES = (("countries",),{'type':str,'nargs':'+','help':"countries to work on (PATTERN [w/o ANTIPATTERN])",'metavar':'COUNTRY'})
SUFFIXES = (("suffixes",),{'type':str,'nargs':'+','help':"suffixes to download",'metavar':'SUFFIX'})
URL = (("-d","--download-url"),{'type':str,'dest':'url','help':"define url for download directory to be URL",'metavar':'URL'})
SHOW = (("-l","--list"),{'action':'store_true','dest':'show','default':False,'help':"list available countries (default: False)"})
WORKERS = (("-w","--max-workers"),{'type':int,'dest':'max_workers','help':"set maximum number of parallel workers to WORKERS",'metavar':'WORKERS'})


CONFIG = [
    ("osm",{'help':"download map data",'args':[SHOW,URL,WORKERS,COUNTRIES]}),
    ("graph",{'help':"download graph files",'args':[
        ("nx",{'help':"download NX graph files",'args':[SHOW,URL,COUNTRIES]}),
        ("gt",{'help':"download GT graph files",'args':[SHOW,URL,COUNTRIES]}),
        ("npz",{'help':"download NPZ graph files",'args':[SHOW,URL,COUNTRIES]})
    ]}),
    ("cache",{'help':"download cache files from Overpass API",'args':[SHOW,URL,COUNTRIES]}),
    ("merged",{'help':"download merged graph file",'args':[URL,SUFFIXES]})
]
BASE_URL="http://caracal.imada.sdu.dk/d4e/"
COUNTRIES=['Albania','Andorra','Austria','Belarus','Belgium','Bosnia and Herzegovina','Bulgaria','Croatia','Cyprus','Czechia','Denmark','Estonia','Faroe Islands','Finland','France','Georgia','Germany','Gibraltar','Greece','Guernsey','Hungary','Iceland','Ireland','Isle of Man','Italy','Jersey','Kosovo','Latvia','Liechtenstein','Lithuania','Luxembourg','Macedonia','Malta','Moldova','Monaco','Montenegro','Netherlands','Norway','Poland','Portugal','RU','Romania','San Marino','Serbia','Slovakia','Slovenia','Spain','Sweden','Switzerland','Turkey','Ukraine','United Kingdom']
OSM_COUNTRIES=['africa','africa_algeria','africa_angola','africa_benin','africa_botswana','africa_burkina-faso','africa_burundi','africa_cameroon','africa_canary-islands','africa_cape-verde','africa_central-african-republic','africa_chad','africa_comores','africa_congo-brazzaville','africa_congo-democratic-republic','africa_djibouti','africa_egypt','africa_equatorial-guinea','africa_eritrea','africa_ethiopia','africa_gabon','africa_ghana','africa_guinea','africa_guinea-bissau','africa_ivory-coast','africa_kenya','africa_lesotho','africa_liberia','africa_libya','africa_madagascar','africa_malawi','africa_mali','africa_mauritania','africa_mauritius','africa_morocco','africa_mozambique','africa_namibia','africa_niger','africa_nigeria','africa_rwanda','africa_saint-helena-ascension-and-tristan-da-cunha','africa_sao-tome-and-principe','africa_senegal-and-gambia','africa_seychelles','africa_sierra-leone','africa_somalia','africa_south-africa','africa_south-africa-and-lesotho','africa_south-sudan','africa_sudan','africa_swaziland','africa_tanzania','africa_togo','africa_tunisia','africa_uganda','africa_zambia','africa_zimbabwe','antarctica','asia','asia_afghanistan','asia_armenia','asia_azerbaijan','asia_bangladesh','asia_bhutan','asia_cambodia','asia_china','asia_gcc-states','asia_india','asia_indonesia','asia_iran','asia_iraq','asia_israel-and-palestine','asia_japan','asia_japan_chubu','asia_japan_chugoku','asia_japan_hokkaido','asia_japan_kansai','asia_japan_kanto','asia_japan_kyushu','asia_japan_shikoku','asia_japan_tohoku','asia_jordan','asia_kazakhstan','asia_kyrgyzstan','asia_laos','asia_lebanon','asia_malaysia-singapore-brunei','asia_maldives','asia_mongolia','asia_myanmar','asia_nepal','asia_north-korea','asia_pakistan','asia_philippines','asia_south-korea','asia_sri-lanka','asia_syria','asia_taiwan','asia_tajikistan','asia_thailand','asia_turkmenistan','asia_uzbekistan','asia_vietnam','asia_yemen','australia-oceania','australia-oceania_australia','australia-oceania_cook-islands','australia-oceania_fiji','australia-oceania_marshall-islands','australia-oceania_micronesia','australia-oceania_new-caledonia','australia-oceania_new-zealand','australia-oceania_papua-new-guinea','australia-oceania_samoa','central-america','central-america_bahamas','central-america_belize','central-america_cuba','central-america_guatemala','central-america_haiti-and-domrep','central-america_jamaica','central-america_nicaragua','europe','europe_albania','europe_alps','europe_andorra','europe_austria','europe_azores','europe_belarus','europe_belgium','europe_bosnia-herzegovina','europe_britain-and-ireland','europe_bulgaria','europe_croatia','europe_cyprus','europe_czech-republic','europe_dach','europe_denmark','europe_estonia','europe_faroe-islands','europe_finland','europe_france','europe_france_alsace','europe_france_aquitaine','europe_france_auvergne','europe_france_basse-normandie','europe_france_bourgogne','europe_france_bretagne','europe_france_centre','europe_france_champagne-ardenne','europe_france_corse','europe_france_franche-comte','europe_france_guadeloupe','europe_france_guyane','europe_france_haute-normandie','europe_france_ile-de-france','europe_france_languedoc-roussillon','europe_france_limousin','europe_france_lorraine','europe_france_martinique','europe_france_mayotte','europe_france_midi-pyrenees','europe_france_nord-pas-de-calais','europe_france_pays-de-la-loire','europe_france_picardie','europe_france_poitou-charentes','europe_france_provence-alpes-cote-d-azur','europe_france_reunion','europe_france_rhone-alpes','europe_georgia','europe_germany','europe_germany_baden-wuerttemberg','europe_germany_baden-wuerttemberg_freiburg-regbez','europe_germany_baden-wuerttemberg_karlsruhe-regbez','europe_germany_baden-wuerttemberg_stuttgart-regbez','europe_germany_baden-wuerttemberg_tuebingen-regbez','europe_germany_bayern','europe_germany_bayern_mittelfranken','europe_germany_bayern_niederbayern','europe_germany_bayern_oberbayern','europe_germany_bayern_oberfranken','europe_germany_bayern_oberpfalz','europe_germany_bayern_schwaben','europe_germany_bayern_unterfranken','europe_germany_berlin','europe_germany_brandenburg','europe_germany_bremen','europe_germany_hamburg','europe_germany_hessen','europe_germany_mecklenburg-vorpommern','europe_germany_niedersachsen','europe_germany_nordrhein-westfalen','europe_germany_nordrhein-westfalen_arnsberg-regbez','europe_germany_nordrhein-westfalen_detmold-regbez','europe_germany_nordrhein-westfalen_duesseldorf-regbez','europe_germany_nordrhein-westfalen_koeln-regbez','europe_germany_nordrhein-westfalen_muenster-regbez','europe_germany_rheinland-pfalz','europe_germany_saarland','europe_germany_sachsen','europe_germany_sachsen-anhalt','europe_germany_schleswig-holstein','europe_germany_thueringen','europe_great-britain','europe_great-britain_england','europe_great-britain_england_bedfordshire','europe_great-britain_england_berkshire','europe_great-britain_england_bristol','europe_great-britain_england_buckinghamshire','europe_great-britain_england_cambridgeshire','europe_great-britain_england_cheshire','europe_great-britain_england_cornwall','europe_great-britain_england_cumbria','europe_great-britain_england_derbyshire','europe_great-britain_england_devon','europe_great-britain_england_dorset','europe_great-britain_england_durham','europe_great-britain_england_east-sussex','europe_great-britain_england_east-yorkshire-with-hull','europe_great-britain_england_essex','europe_great-britain_england_gloucestershire','europe_great-britain_england_greater-london','europe_great-britain_england_greater-manchester','europe_great-britain_england_hampshire','europe_great-britain_england_herefordshire','europe_great-britain_england_hertfordshire','europe_great-britain_england_isle-of-wight','europe_great-britain_england_kent','europe_great-britain_england_lancashire','europe_great-britain_england_leicestershire','europe_great-britain_england_lincolnshire','europe_great-britain_england_merseyside','europe_great-britain_england_norfolk','europe_great-britain_england_north-yorkshire','europe_great-britain_england_northamptonshire','europe_great-britain_england_northumberland','europe_great-britain_england_nottinghamshire','europe_great-britain_england_oxfordshire','europe_great-britain_england_rutland','europe_great-britain_england_shropshire','europe_great-britain_england_somerset','europe_great-britain_england_south-yorkshire','europe_great-britain_england_staffordshire','europe_great-britain_england_suffolk','europe_great-britain_england_surrey','europe_great-britain_england_tyne-and-wear','europe_great-britain_england_warwickshire','europe_great-britain_england_west-midlands','europe_great-britain_england_west-sussex','europe_great-britain_england_west-yorkshire','europe_great-britain_england_wiltshire','europe_great-britain_england_worcestershire','europe_great-britain_scotland','europe_great-britain_wales','europe_greece','europe_hungary','europe_iceland','europe_ireland-and-northern-ireland','europe_isle-of-man','europe_italy','europe_italy_centro','europe_italy_isole','europe_italy_nord-est','europe_italy_nord-ovest','europe_italy_sud','europe_kosovo','europe_latvia','europe_liechtenstein','europe_lithuania','europe_luxembourg','europe_macedonia','europe_malta','europe_moldova','europe_monaco','europe_montenegro','europe_netherlands','europe_netherlands_drenthe','europe_netherlands_flevoland','europe_netherlands_friesland','europe_netherlands_gelderland','europe_netherlands_groningen','europe_netherlands_limburg','europe_netherlands_noord-brabant','europe_netherlands_noord-holland','europe_netherlands_overijssel','europe_netherlands_utrecht','europe_netherlands_zeeland','europe_netherlands_zuid-holland','europe_norway','europe_poland','europe_poland_dolnoslaskie','europe_poland_kujawsko-pomorskie','europe_poland_lodzkie','europe_poland_lubelskie','europe_poland_lubuskie','europe_poland_malopolskie','europe_poland_mazowieckie','europe_poland_opolskie','europe_poland_podkarpackie','europe_poland_podlaskie','europe_poland_pomorskie','europe_poland_slaskie','europe_poland_swietokrzyskie','europe_poland_warminsko-mazurskie','europe_poland_wielkopolskie','europe_poland_zachodniopomorskie','europe_portugal','europe_romania','europe_serbia','europe_slovakia','europe_slovenia','europe_spain','europe_sweden','europe_switzerland','europe_turkey','europe_ukraine','north-america','north-america_canada','north-america_canada_alberta','north-america_canada_british-columbia','north-america_canada_manitoba','north-america_canada_new-brunswick','north-america_canada_newfoundland-and-labrador','north-america_canada_northwest-territories','north-america_canada_nova-scotia','north-america_canada_nunavut','north-america_canada_ontario','north-america_canada_prince-edward-island','north-america_canada_quebec','north-america_canada_saskatchewan','north-america_canada_yukon','north-america_greenland','north-america_mexico','north-america_us','north-america_us-midwest','north-america_us-northeast','north-america_us-pacific','north-america_us-south','north-america_us-west','north-america_us_alabama','north-america_us_alaska','north-america_us_arizona','north-america_us_arkansas','north-america_us_california','north-america_us_california_norcal','north-america_us_california_socal','north-america_us_colorado','north-america_us_connecticut','north-america_us_delaware','north-america_us_district-of-columbia','north-america_us_florida','north-america_us_georgia','north-america_us_hawaii','north-america_us_idaho','north-america_us_illinois','north-america_us_indiana','north-america_us_iowa','north-america_us_kansas','north-america_us_kentucky','north-america_us_louisiana','north-america_us_maine','north-america_us_maryland','north-america_us_massachusetts','north-america_us_michigan','north-america_us_minnesota','north-america_us_mississippi','north-america_us_missouri','north-america_us_montana','north-america_us_nebraska','north-america_us_nevada','north-america_us_new-hampshire','north-america_us_new-jersey','north-america_us_new-mexico','north-america_us_new-york','north-america_us_north-carolina','north-america_us_north-dakota','north-america_us_ohio','north-america_us_oklahoma','north-america_us_oregon','north-america_us_pennsylvania','north-america_us_puerto-rico','north-america_us_rhode-island','north-america_us_south-carolina','north-america_us_south-dakota','north-america_us_tennessee','north-america_us_texas','north-america_us_utah','north-america_us_vermont','north-america_us_virginia','north-america_us_washington','north-america_us_west-virginia','north-america_us_wisconsin','north-america_us_wyoming','russia','russia_central-fed-district','russia_crimean-fed-district','russia_far-eastern-fed-district','russia_kaliningrad','russia_north-caucasus-fed-district','russia_northwestern-fed-district','russia_siberian-fed-district','russia_south-fed-district','russia_ural-fed-district','russia_volga-fed-district','south-america','south-america_argentina','south-america_bolivia','south-america_brazil','south-america_brazil_centro-oeste','south-america_brazil_nordeste','south-america_brazil_norte','south-america_brazil_sudeste','south-america_brazil_sul','south-america_chile','south-america_colombia','south-america_ecuador','south-america_paraguay','south-america_peru','south-america_suriname','south-america_uruguay','south-america_venezuela']
#OSM_COUNTRIES=['albania','andorra','austria','azores','belarus','belgium','bosnia-herzegovina','bulgaria','croatia','cyprus','czech-republic','denmark','estonia','faroe-islands','finland','france','georgia','germany','great-britain','greece','hungary','iceland','ireland-and-northern-ireland','isle-of-man','italy','kosovo','latvia','liechtenstein','lithuania','luxembourg','macedonia','malta','moldova','monaco','montenegro','netherlands','norway','poland','portugal','romania','russia','serbia','slovakia','slovenia','spain','sweden','switzerland','turkey','ukraine']
OSM_URL="https://download.geofabrik.de/"

def download_file(url,file_name,retries=10):
    from requests import get
    from shutil import copyfileobj
    from sys import exit
    from limic.util import status, md5file, options
    from os.path import exists
    download = True
    if options.md5sum:
        file_md5 = md5file(file_name) if exists(file_name) else None
        md5_retries = retries
        while True:
            timed_out = False
            try:
                r = get(url+".md5",timeout=5)
            except:
                timed_out = True
            if not timed_out and r.status_code == 200:
                break
            md5_retries -= 1
            if not md5_retries:
                status("ERROR(file.md5): HTTP status 200 expected, got "+str(r.status_code)+" for "+url+".md5")
                exit(-1)
            status("WARNING(download): RETRYING "+url+".md5")
        url_md5 = r.content.split()[0].decode('utf8')
        if file_md5 and url_md5 == file_md5:
            if options.verbosity >= 2:
                status('SKIPPING',end='   ')
            return file_name
    while True:
        r = get(url, stream=True)
        if r.status_code == 200:
            break
        retries -= 1
        if not retries:
            status("ERROR(file): HTTP status 200 expected, got "+str(r.status_code)+" for "+url)
            exit(-1)
        status("WARNING(download): RETRYING "+url+".md5")
    f = open(file_name, 'wb')
    copyfileobj(r.raw, f)
    f.close()
    if options.md5sum:
        file_md5 = md5file(file_name)
        if url_md5 != file_md5:
            status("ERROR(md5): "+file_md5+" vs "+url_md5)
            exit(-1)
        f = open(file_name+".md5","wt")
        f.write(file_md5+" "+file_name)
        f.close()
    return file_name

def download_osm(countries,url=None,show=False,max_workers=None):
    from limic.util import start,end,file_size,status
    from concurrent.futures import ProcessPoolExecutor, wait
    countries, url = common(countries,url,show,osm=True)
    if max_workers:
        executor = ProcessPoolExecutor(max_workers=max_workers)
        fs = []
        start("Downloading OSM map data for"," ".join(countries))
    for country in countries:
        file_url = OSM_URL+country.replace("_","/")+"-latest.osm.bz2"
        file_name = country+"-latest.osm.bz2"
        if max_workers:
            fs.append(executor.submit(download_file,file_url,file_name))
            continue
        start("Downloading OSM map data for",country)
        file_name = download_file(file_url,file_name)
        end('')
        file_size(file_name)
    if max_workers:
        running = len(fs)
        total = running
        while running:
            print("Waiting for",running,"out of",total,"processes ...")
            wait(fs,timeout=10)
            running = sum(0 if f.done() else 1 for f in fs)
        for f in fs:
            file_name = f.result()
            status(file_name,end=':')
            file_size(file_name,end='   ')
        end()

def download_cache(countries,url=None,show=False):
    from limic.util import start,end,file_size
    countries, url = common(countries,url,show)
    for country in countries:
        start("Downloading cache for",country)
        file_url = url+"cache."+country.replace(" ","%20")
        file_name = download_file(file_url,"cache."+country)
        end('')
        file_size(file_name)

def download_graph(suffix,countries,url=None,show=False,join=False):
    from limic.util import start,end,file_size
    countries, url = common(countries,url,show=show,join=join)
    for country in countries:
        start("Downloading",suffix.upper(),"graph for",country)
        file_url = url+"graph."+country.replace(" ","%20")+"."+suffix
        file_name = download_file(file_url,"graph."+country+"."+suffix)
        end('')
        file_size(file_name)

def download_graph_nx(countries,url=None,show=False):
    download_graph("nx",countries,url=url,show=show)

def download_graph_gt(countries,url=None,show=False):
    download_graph("gt",countries,url=url,show=show)

def download_graph_npz(countries,url=None,show=False):
    download_graph("npz",countries,url=url,show=show)
        
def download_merged(suffixes=("nx","gt","npz"),url=None):
    from limic.util import start,end,file_size
    if not url:
        url = BASE_URL
    for suffix in suffixes:
        start("Downloading merged",suffix.upper(),"graph for Europe")
        file_url = url+"merged.Europe."+suffix
        file_name = download_file(file_url,"merged.Europe."+suffix)
        end('')
        file_size(file_name)

def common(countries,url=None,show=False,osm=False,join=False):
    from fnmatch import translate
    from re import compile
    selected = set()
    anti = False
    ALL_COUNTRIES = OSM_COUNTRIES+COUNTRIES if join else (OSM_COUNTRIES if osm else COUNTRIES)
    for country in countries:
        if country == 'w/o':
            anti = True
        country = compile(translate(country).replace("%%",".*").replace("%","[^_]*"))
        for available in ALL_COUNTRIES:
            if country.match(available):
                if anti:
                    selected.discard(available)
                else:
                    selected.add(available)
    countries = list(selected)
    countries.sort()
    if show or not countries:
        from limic.util import options
        options.parser.error("Available countries:\n"+" ".join(ALL_COUNTRIES))
    if not url:
        url = OSM_URL if osm else BASE_URL
    return countries, url
