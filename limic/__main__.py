from limic.route import CONFIG as ROUTE_CONFIG
from limic.init import CONFIG as INIT_CONFIG
from limic.download import CONFIG as DOWNLOAD_CONFIG
from limic.merge import CONFIG as MERGE_CONFIG
from limic.convert import CONFIG as CONVERT_CONFIG
from limic.prune import CONFIG as PRUNE_CONFIG
from limic.select import CONFIG as SELECT_CONFIG
from limic.length import CONFIG as LENGTH_CONFIG
from limic.fill import CONFIG as FILL_CONFIG
from limic.extract import CONFIG as EXTRACT_CONFIG
from limic.condense import CONFIG as CONDENSE_CONFIG
from limic.render import CONFIG as RENDER_CONFIG
from limic.serve import CONFIG as SERVE_CONFIG
from limic.test import CONFIG as TEST_CONFIG
CONFIG = [
    (("-v","--verbosity"),{'type':int,'default':1,'dest':'verbosity','help':"set verbosity level to LEVEL (default: 1)",'metavar':'LEVEL'}),
    (("-5","--md5"),{'action':'store_true','default':False,'dest':'md5sum','help':"deactivate MD5 checksumming (default: False)"}),
    (("-w","--overwrite"),{'action':'store_true','default':False,'dest':'overwrite','help':"overwrite if destinatone exists (default: False)"}),
    ("init",{'help':"Initialize the data files.",'args':INIT_CONFIG}),
    ("download",{'help':"Download graph, cache, or map files.",'args':DOWNLOAD_CONFIG}),
    ("route",{'help':"Route from one power tower to another.",'args':ROUTE_CONFIG}),
    ("convert",{'help':"Convert graphs/caches.",'args':CONVERT_CONFIG}),
    ("merge",{'help':"Merge graphs/caches.",'args':MERGE_CONFIG}),
    ("prune",{'help':"Prune graph by geometry.",'args':PRUNE_CONFIG}),
    ("select",{'help':"Select area from graph by geometry.",'args':SELECT_CONFIG}),
    ("length",{'help':"Compute total length of non-air edges.",'args':LENGTH_CONFIG}),
    ("fill",{'help':"Fill a cache with map data.",'args':FILL_CONFIG}),
    ("extract",{'help':"Extract NX graph from cache with map data.",'args':EXTRACT_CONFIG}),
    ("condense",{'help':"Condense linear segments", 'args':CONDENSE_CONFIG}),
    ("render",{'help':"Render graphs to HTML",'args':RENDER_CONFIG}),
    ("serve",{'help':"Serve interactive routing map",'args':SERVE_CONFIG}),
    ("test",{'help':"Extensive self tests.",'args':TEST_CONFIG}),
]

if __name__ == "__main__":
    from argparse import ArgumentParser
    from limic.util import set_option, parse_config
    from importlib import import_module
    from sys import argv
    if len(argv) == 1:
        argv.extend(["serve","auto","europe_denmark"])
    parser = ArgumentParser(description="Powerlines as drone highways.")
    parse_config(CONFIG, parser, [])
    args = parser.parse_args()
    set_option('verbosity',args.verbosity)
    set_option('md5sum',not args.md5sum)
    set_option('overwrite',args.overwrite)
    set_option('parser',parser)
    module = import_module(args.mod)
    func = vars(module)[args.func]
    del args.verbosity, args.md5sum, args.overwrite, args.mod, args.func, args.command
    func(**vars(args))
