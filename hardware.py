import dataclasses
import math


@dataclasses.dataclass(frozen = True)
class Pos():
    x : int
    z : int
    y : int
    def __repr__(self):
        return f"({self.x}, {self.z}; {self.y})"
    def is_even(self):
        return self.x % 2 == self.y % 2 == self.z % 2 == 0
    def above(self):
        return Pos(self.x, self.z, self.y + 1)


class Comp():
    @property
    def used(self):
        return set()


class Bus(Comp):
    def __init__(self, steps):
        super().__init__()
        steps = tuple(steps)
        for p in steps:
            assert p.is_even()
        for pos in steps:
            assert isinstance(pos, Pos)
        for i in range(len(steps) - 1):
            j = i + 1
            p1, p2 = steps[i],  steps[i + 1]
            assert abs(p1.y - p2.y) in {0, 2}
            assert abs(p1.x - p2.x) in {0, 2}
            assert abs(p1.z - p2.z) in {0, 2}
            assert abs(p1.x - p2.x) + abs(p1.z - p2.z) in {0, 2}
        self.steps = steps

    @property
    def triples(self):
        triples = []
        for i in range(len(self.steps) - 2):
            triples.append((self.steps[i], self.steps[i + 1], self.steps[i + 2]))
        return triples

    @property
    def pairs(self):
        pairs = []
        for i in range(len(self.steps) - 1):
            pairs.append((self.steps[i], self.steps[i + 1]))
        return pairs

    @property
    def used(self):
        used = set()
        for p in self.steps:
            used.add(p)
            used.add(p.above())
        for p1, p2 in self.pairs:
            m = Pos((p1.x + p2.x) // 2, (p1.z + p2.z) // 2, (p1.y + p2.y) // 2)
            used.add(m)
            used.add(m.above())

            if p2.y == p1.y + 2: #step up
                
                
        return used
            
##    @property
##    def extra_used(self):
##        used = set()
##        for p1, p2 in self.pairs:
##            if abs(p1.y - p2.y) == 0:
##                pass
##            elif p2.y == p1.y + 2: #step up
##                used.add(Pos(p1.x, p1.z, p2.y))
##            else: #step down
##                assert p2.y == p1.y - 2
##                used.add(Pos(p2.x, p2.z, p1.y))
##        return used
##
##    def is_legal(self):
##        #return true iff the bus does not cut itself off anywhere and there is room for repeaters somewhere with minimal delay
##
##        #cant repeat any poses
##        if len(self.steps) != len(set(self.steps)):
##            return False
##
##        #cant reverse direction in the x-z plane
##        for p1, p2, p3 in self.triples:
##            vec21 = (p1.x - p2.x, p1.z - p2.z)
##            vec23 = (p3.x - p2.x, p3.z - p2.z)
##            if vec21 == vec23:
##                return False
##
##        #cant cut ourselves off on a slope
##        extra = set()
##        for p1, p2 in self.pairs:
##            e = Bus([p1, p2]).used
##            e.remove(p1)
##            e.remove(p2)
##            extra |= e
##        for p in self.steps:
##            if p in extra:
##                return False
##        
##        return True
##                
        

    

class Group():
    def __init__(self, comps):
        comps = set(comps)
        for comp in comps:
            assert isinstance(comp, Comp)
        self.comps = comps

    @property
    def used(self):
        used = set()
        for comp in self.comps:
            used |= comp.used
        return used

    def add_bus(self, p1, p2):
        class AdjSteps():
            def __init__(self, used):
                self.used = used
                
            def __call__(self, p):
                for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    for dy in [-1, 0, 1]:
                        adj = Pos(p.x + dx, p.z + dz, p.y + dy)
                        if len(Bus([p, adj]).extra_used & self.used) == 0:
                            if not adj in self.used or adj in {p1, p2}:
                                yield adj
                            
        adj_steps = AdjSteps(self.used | {p1, p2})
    
        def a_star(p1, p2):
            def dist(a, b):
                return math.sqrt((a.x - b.x) ** 2 + (a.z - b.z) ** 2 + (a.y - b.y) ** 2)

            #g_cost : how costly is the path so far
            #h_cost : how far is the target point from here
            #f_cost : g_cost + h_cost; how promising is this point

            solid = {p1}
            poses = {} #pos -> (g_cost, h_cost, comes_from)
            for a in adj_steps(p1):
                poses[a] = (dist(p1, a), dist(a, p2), p1)
                
            while True:
                p = min([p for p in poses.keys() if not p in solid], key = lambda a : poses[a][0] + poses[a][1])
                solid.add(p)
                if p == p2:
                    break
                for a in adj_steps(p):
                    if not a in solid:
                        g = poses[p][0] + dist(p, a)
                        if a in poses:
                            if g < poses[a][0]:
                                poses[a] = (g, poses[a][1], p)
                        else:
                            poses[a] = (g, dist(a, p2), p)
            steps = [p2]
            while steps[-1] != p1:
                steps.append(poses[steps[-1]][2])
            steps = list(reversed(steps))
            return steps

        all_steps = [p1]
        while all_steps[-1] != p2:
            print(adj_steps.used)
            steps = a_star(all_steps[-1], p2)
            for i in reversed(range(len(steps))):
                sub_bus = Bus(steps[:i+1])
                if sub_bus.is_legal():
                    print("BOOP", sub_bus.steps)
                    all_steps = all_steps[:-1] + list(sub_bus.steps)
                    adj_steps.used |= sub_bus.used
                    break
                
        print(all_steps)

        
            

##        class NoRouteError(Exception):
##            pass
##        
##        def find_steps(used, p1, p2, length = 0):
##            #print("find_steps", p1, p2, length)
##            if p1 == p2:
##                return [p1]
##
##            def g_cost(p):
##                return (p.x - p1.x) ** 2 + (p.z - p1.z) ** 2 + (p.y - p1.y) ** 2
##            def h_cost(p):
##                return (p.x - p2.x) ** 2 + (p.z - p2.z) ** 2 + (p.y - p2.y) ** 2
##            def f_cost(p):
##                return g_cost(p) + h_cost(p)
##            
##
##            def heur(a):
##                return (a.x - p2.x) ** 2 + (a.z - p2.z) ** 2 + (a.y - p2.y) ** 2
##            
##            for adj in sorted(list(adj_steps(p1, used)), key = heur):                
##                try:
##                    return [p1] + find_steps(set(used) | Bus([p1, adj]).used, adj, p2, length + 1)
##                except NoRouteError:
##                    pass
##            raise NoRouteError()
##
##        used = set(self.used)
##        for x in range(-100, 100):
##            for z in range(-100, 100):
##                used.add(Pos(x, z, 1))
##
##        steps = find_steps(used, p1, p2)
##        print(f"PATH {p1} -> {p2}")
##        for p in steps:
##            print(p)
##        self.comps.add(Bus(steps))



if __name__ == "__main__":
    bus = Bus([Pos(0, 0, 0), Pos(2, 0, 0), Pos(2, 2, 2)])
    print(bus.used)

    input()

    
    g = Group([])
    g.add_bus(Pos(0, 0, 0), Pos(0, 0, 1))
    input("done")
    g.add_bus(Pos(-10, 0, 0), Pos(10, 0, 0))
    g.add_bus(Pos(0, -10, 0), Pos(0, 10, 0))
    print(g)




























