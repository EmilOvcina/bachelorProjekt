from limic.util import start, end, file_size, status, load_pickled, save_pickled
from sys import argv
if __name__ == "__main__":
    file_name_in = argv[1]
    file_name_out = argv[2]
    start("Loading graph from",file_name_in)
    g = load_pickled(file_name_in)
    end('')
    status(len(g.edges()),end='   ')
    file_size(file_name_in)
    start("Cleaning up graph")
    for u,v,d in g.edges(data=True):
        d['type'] = -1 if d['air'] else 0
        del d['air']
    end()
    start("Saving graph to",file_name_out)
    save_pickled(file_name_out,g)
    end('')
    file_size(file_name_out)

