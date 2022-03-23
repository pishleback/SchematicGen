#P32 program schematic generator

#instruction format:
#oooo aaaa bbbb cccc

#oooo : opp code
#aaaabbbbcccc : branch/jump destination

import schemgen


def validate(code):
    assert type(code) == list
    assert len(code) == 2 ** 12
    for nibs in code:
        #nibs = [oooo,aaaa,bbbb,cccc]
        for x in nibs:
            assert type(x) == int
            assert 0 <= x < 16

def code_to_schem(code):
    validate(code)

    def get_hex(x, y, z):
        assert 0 <= x < 16
        assert 0 <= y < 32
        assert 0 <= z < 32
        #need to turn x,y,z into i,n where
        #i is the index of the instruction from 0 <= i < 2^12-1
        #n is the nibble of the instruction oooo/aaaa/bbbb/cccc

        i = x + 2**4 * (y % 2 + (z // 2) * 2) + 2**9 * (y // 4)
        n = {(0, 0) : 0, (1, 0) : 3, (0, 1) : 2, (1, 1) : 1}[((y // 2) % 2, z % 2)]
        if (z // 2) % 2 == 1:
            n = [2, 3, 0, 1][n]
        return code[i][n]

    def gen_blocks():
        for x in range(16):
            for y in range(32):
                for z in range(32):
                    h = get_hex(x, y, z)
                    if h == 0:
                        yield schemgen.Block(2 * x, 2 * y, 2 * z, "minecraft:brown_wool")
                    else:
                        yield schemgen.Signal(2 * x, 2 * y, 2 * z, h)
        
    return schemgen.blocks_to_schem(gen_blocks(), 0, 63, 0)
    


code = [[0, 0, 0, 0] for _ in range(2 ** 12)]


for i in range(16):
    code[i] = [i, 0, 0, 15]
for i in range(16):
    code[i + 16] = [i, 1, 5, 15]
for i in range(16):
    code[i + 32] = [i, 2, 7, 15]



schem = code_to_schem(code)
schem.save("p32_code.schem")

