#P32 program schematic generator

#instruction format:
#oooo aaaa bbbb cccc

#oooo : opp code
#aaaabbbbcccc : branch/jump destination



#0  pass
#1  ??
#2  ??
#3  ??
#4  jump
#5  branch
#6  call
#7  return
#8  ??
#9  ??
#10 ??
#11 ??
#12 ??
#13 ??
#14 ??
#15 ??

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
        n = {(0, 0) : 2, (1, 0) : 3, (0, 1) : 0, (1, 1) : 1}[((y // 2) % 2, z % 2)]
        if (z // 2) % 2 == 1:
            n = [2, 3, 0, 1][n]
        return code[i][n]

    def gen_blocks():
        for x in range(16):
            for y in range(32):
                for z in range(32):
                    h = get_hex(x, y, z)
                    yield schemgen.Signal(2 * x, 2 * y, 2 * z, h)
        
    return schemgen.blocks_to_schem(gen_blocks(), 0, 63, 0)
    


code = [[0, 0, 0, 0] for _ in range(2 ** 12)]

import random
for i in range(2 ** 12):
    code[i] = [random.randint(0, 15), (i // 256) % 16, (i // 16) % 16, i % 16]
##
##code[0][0] = 0
##code[1][0] = 4
##code[2][0] = 4
##code[3][0] = 7
##code[4][0] = 4
##code[5][0] = 0
##code[7][0] = 0
##code[8][0] = 0
##code[9][0] = 0
##code[10][0] = 0
##code[11][0] = 0
##code[12][0] = 0
##code[13][0] = 0
##code[14][0] = 0
##code[15][0] = 0

##
##for i in range(16):
##    code[i] = [i, 0, 0, 15]
##for i in range(16):
##    code[i + 16] = [i, 1, 5, 15]
##for i in range(16):
##    code[i + 32] = [i, 2, 7, 15]


schem = code_to_schem(code)
schem.save("p32_code.schem")

quit()

