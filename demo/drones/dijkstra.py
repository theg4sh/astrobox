import sys

class Dijkstra:
    def __init__(self, unit, points=None):
        self._unit = unit
        self._points = points if points else []
        self._weights = [[0.0 for _ in range(len(self._points))] for _ in range(len(self._points))]
        # self._weights_range = [0.0, 0.0]

    @staticmethod
    def maxint():
        return sys.maxsize

    @property
    def points(self):
        return self._points

    @property
    def weights(self):
        return self._weights

    def _get_closest(self):
        if not self._unit.is_alive:
            return
        uclosest = self._points[0]
        dclosest = self._points[0].distance_to(self._unit)
        for u in self._points:
            chkdist = self._unit.distance_to(u)
            if chkdist < dclosest:
                dclosest = chkdist
                uclosest = u
        return uclosest

    def update_units(self, func=None):
        if func is None:
            func = lambda a: True
        units = [self._unit.mothership(), ]
        units = units + [a for a in self._unit.scene.asteroids if func(a)]
        units = units + [m for m in self._unit.scene.motherships if
                         not m.is_alive and m.team != self._unit.team and func(m)]
        units = units + [d for d in self._unit.scene.drones if not d.is_alive and func(d)]
        weights = [[0.0 for _ in range(len(units))] for _ in range(len(units))]
        self._weights, self._points = weights, units
        self._unit._path_closest = self._get_closest()

    def to_objects(self, indexes):
        return [self._points[n] for n in indexes]

    def weight_default_func(self, a, b):
        return float(a.distance_to(b))

    def calc_weights(self, func=None):
        if not self._unit.is_alive:
            return
        if func is None:
            func = self.weight_default_func
        # self._weights_range = [self.maxint, 0.0]
        for f, a in enumerate(self._points):
            for t, b in enumerate(self._points):
                if f == t:
                    self._weights[f][t] = float(0.0)
                else:
                    d = float(func(a, b))
                    self._weights[f][t] = d
                    # if self._weights_range[0]>d:
                    #    self._weights_range[0]=d
                    # if self._weights_range[1]<d:
                    #    self._weights_range[1]=d
            # print("%s "%(self._unit.id) + ",".join(["%8.2f"%d for d in self._weights[k]]))
            # print("")

    def find_path(self, pt_from, pt_to, as_objects=False, info=None):
        if not self._unit.is_alive:
            return
        if pt_from not in self._points or pt_to not in self._points:
            print(pt_from, pt_to, self._points)
        fi = self._points.index(pt_from)
        fo = self._points.index(pt_to)
        if fi == fo:
            if as_objects:
                return self.to_objects([fi, ])
            else:
                return [fi, ]

        visited = []
        unvisited = list(range(len(self._points)))

        FCOST=0
        FPREV=1
        table = [[self.maxint(), -1] for p in range(len(self._points))]
        table[fi][FCOST] = 0
        root = fi
        while len(unvisited):
            visited.append(root)
            # print(root, fi, fo, root in unvisited)
            unvisited.pop(unvisited.index(root))

            neighbors = [uv for uv in unvisited if self._weights[root][uv] < float("inf")]
            for n in neighbors:
                cost = table[root][FCOST] + self._weights[root][n]
                if table[n][FCOST] > cost:
                    table[n][FCOST] = cost
                    table[n][FPREV] = root
            shortest = self.maxint()
            lastroot = root
            for uv in unvisited:
                if uv == lastroot:
                    continue
                if table[uv][FCOST] < shortest:
                    shortest = table[uv][FCOST]
                    root = uv
            # FIXME
            if root == lastroot:
                if unvisited:
                    root = unvisited[0]
        # for k,t in enumerate(table):
        #    print(k, t)
        path = []
        root = fo
        while table[root][FPREV] > -1:
            path.insert(0, root)
            root = table[root][FPREV]
        path.insert(0, root)
        # print("Team {}:{} path[{}]: {}".format(self._unit.team, self._unit.id, info if info else "?", path))
        if as_objects:
            return self.to_objects(path)
        else:
            return path

