import nbtlib
from nbtlib.tag import String, List, Compound, IntArray, Int, ByteArray, Byte, Short


#general minecraft block
#x, y, z is the positions of the block
#ident is the type of block, e.g. "minecraft:barrel"
#extra is anything that comes after the type of block, eg "[facing=up,open=false]"
class Block():
    def __init__(self, x, y, z, ident, extra = ""):
        assert type(x) == type(y) == type(z) == int
        assert type(ident) == str
        assert type(extra) == str
        if len(extra) != 0:
            assert extra[0] == "[" and extra[-1] == "]"
        self.ident = ident
        self.extra = extra
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"Block({self.x}, {self.y}, {self.z}, {self.ident + self.extra})"

    @property
    def pos(self):
        return (self.x, self.y, self.z)

    def block_entities(self):
        return
        yield

#a barrel containing some items
#items should be a dict whose keys are slots from 0-26 and whose values are tuples of (item name, quantity) e.g. {7 : ("minecraft:redstone", 64)}
class Barrel(Block):
    def __init__(self, x, y, z, items):
        for slot in items:
            item, quant = items[slot]
            assert type(slot) == int and 0 <= slot < 27
            assert type(item) == str
            assert 0 <= quant <= 64
        super().__init__(x, y, z, "minecraft:barrel", "[facing=up,open=false]")
        self.items = items #dict of {slot : (item, quant)}

    def block_entities(self):
        def gen_sid():
            for slot, info in self.items.items():
                ident, count = info
                yield slot, ident, count
        yield Compound({"Items" : List[Compound]([Compound({"Slot" : Byte(slot), "id" : String(ident), "Count" : Byte(count)}) for slot, ident, count in gen_sid()])})


#a barrel which contains enough redstone to emit a signal of ss when read by a comparator
def Signal(x, y, z, ss):
    n = [0, 123, 246, 370, 493, 617, 740, 863, 987, 1110, 1234, 1357, 1481, 1604, 1727, 1728][ss]
    items = []
    while n >= 64:
            items.append(64)
            n -= 64
    if n != 0:
        items.append(n)
        n = 0
    return Barrel(x, y, z, {idx : ("minecraft:redstone", count) for idx, count in enumerate(items)})
    
    
#make a schematic out of a list of blocks. The origin for //paste is given by (x, y, z)
def blocks_to_schem(mblocks, x, y, z):
    assert type(x) == type(y) == type(z) == int

    blocks = {}
    for block in mblocks:
        blocks[block.pos] = block
    
    assert len(blocks) != 0
    min_x = min(p[0] for p in blocks)
    min_y = min(p[1] for p in blocks)
    min_z = min(p[2] for p in blocks)
    we_x = x - min_x
    we_y = y - min_y
    we_z = z - min_z
    blocks = {(p[0] - min_x, p[1] - min_y, p[2] - min_z) : blocks[p] for p in blocks}
    width = max(p[0] for p in blocks) + 1
    height = max(p[1] for p in blocks) + 1
    length = max(p[2] for p in blocks) + 1

    def t31(x, y, z):
        assert 0 <= x < width
        assert 0 <= y < height
        assert 0 <= z < length
        idx = x + z * width + y * width * length
        assert 0 <= idx < width * height * length
        return idx
    
##    def t13(idx):
##        assert 0 <= idx < width * height * length
##        yz, x = divmod(idx, width)
##        y, z = divmod(yz, length)
##        assert 0 <= x < width
##        assert 0 <= y < height
##        assert 0 <= z < length
##        return x, y, z

    for x in range(width):
        for y in range(height):
            for z in range(length):
                if not (x, y, z) in blocks:
                    blocks[(x, y, z)] = Block(min_x + x, min_y + y, min_z + z, "minecraft:air")

    palette = {ident : idx for idx, ident in enumerate(set(block.ident + block.extra for block in blocks.values()))}

    block_data = [None] * (width * height * length)
    for p in blocks:
        block = blocks[p]
        block_data[t31(*p)] = palette[block.ident + block.extra]
        
    def gen_ents():
        for p in blocks:
            block = blocks[p]
            for ent in block.block_entities():
                ent["Id"] = String(block.ident)
                ent["Pos"] = IntArray([Int(p[0]), Int(p[1]), Int(p[2])])
                yield ent
    
    comp = Compound({})
    comp["Version"] = Int(2)
    comp["DataVersion"] = Int(2584)
    comp["PaletteMax"] = Int(len(palette))
    comp["Palette"] = Compound({ident : Int(idx) for ident, idx in palette.items()})
    comp["Width"] = Short(width)
    comp["Height"] = Short(height)
    comp["Length"] = Short(length)
    comp["BlockData"] = ByteArray(block_data)
    comp["BlockEntities"] = List[Compound](list(gen_ents()))
    comp["Metadata"] = Compound({"WEOffsetX" : Int(-we_x), "WEOffsetY" : Int(-we_y), "WEOffsetZ" : Int(-we_z)})
    comp["Offset"] = ByteArray([0, 0, 0])
    return nbtlib.File(Compound({"Schematic" : comp}), gzipped = True)


def schem_to_blocks(file):
    comp = file.root

    width = int(comp["Width"])
    height = int(comp["Height"])
    length = int(comp["Length"])
    
    def t13(idx):
        assert 0 <= idx < width * height * length
        yz, x = divmod(idx, width)
        y, z = divmod(yz, length)
        assert 0 <= x < width
        assert 0 <= y < height
        assert 0 <= z < length
        return x, y, z

    block_data = [int(x) for x in comp["BlockData"]]
    palette_max = comp["PaletteMax"]
    palette = {int(idx) : ident for ident, idx in comp["Palette"].items()}

    we_x = -int(comp["Metadata"]["WEOffsetX"])
    we_y = -int(comp["Metadata"]["WEOffsetY"])
    we_z = -int(comp["Metadata"]["WEOffsetZ"])

    for idx in range(width * height * length):
        x, y, z = t13(idx)
        ident_extra = palette[block_data[idx]]
        if "[" in ident_extra:
            k = ident_extra.index("[")
            ident, extra = ident_extra[:k], ident_extra[k:]
        else:
            ident, extra = ident_extra, ""
        yield Block(x - we_x, y - we_y, z - we_z, ident, extra)

    
    

def print_nbt(file):
    print(f"gzipped = {file.gzipped}")
    print()
    print(f"byteorder = {file.byteorder}")
    for key in file.root.keys():
        print()
        print(f"{key} = {file.root[key]}")
    



def make_schem():
    #yield all the blocks you want in the schematic
    #if multiple blocks are yielded to the same location, the last one is the chosen one
    def gen_blocks():
        for x in range(-2, 16):
            for y in range(-2, 8):
                for z in range(-2, 4):
                    if x == 0:
                        yield Block(x, y, z, "minecraft:dirt")
                    elif y == 0:
                        yield Block(x, y, z, "minecraft:stone")
                    elif z == 0:
                        yield Block(x, y, z, "minecraft:barrel", extra = "[facing=north]")
                    elif x == y == z == 2:
                        yield Signal(x, y, z, 13)
        return
        yield
        
    file = blocks_to_schem(gen_blocks(), 16, 8, 4)
    #print_nbt(file)
    file.save("output.schem")





def make_schem():
    def gen_blocks():
        yield Block(0, 1, 0, "minecraft:light_blue_wool")
        yield Block(1, 0, 0, "minecraft:light_blue_wool")
        yield Block(1, 0, 1, "minecraft:light_blue_wool")
        yield Block(0, 0, 1, "minecraft:light_blue_wool")

        yield Block(0, 1, 1, "minecraft:redstone_wire", extra = "[power=3,east=side,west=side,north=none,south=none]")
        yield Block(1, 1, 1, "minecraft:comparator", extra = "[mode=subtract,powered=true,facing=south]")
        yield Block(1, 1, 0, "minecraft:comparator", extra = "[mode=subtract,powered=true,facing=east]")
        yield Block(1, 1, 2, "minecraft:redstone_block")
        yield Block(2, 1, 0, "minecraft:redstone_block")
    
        
    file = blocks_to_schem(gen_blocks(), 0, 3, 0)
    #print_nbt(file)
    file.save("output.schem")
    



if __name__ == "__main__":
    make_schem()






















