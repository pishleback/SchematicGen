


class P16SyntaxError(Exception):
    def __str__(self):
        return "P16 Syntax error: " + super().__str__()


def parse_register(text):
    assert text != ""
    if text[0] != "r":
        raise P16SyntaxError(f"Registers must begin with an \"r\", for example \"r5\"")
    reg_num = parse_integer(text[1:])
    if reg_num < 0 or reg_num > 15:
        raise P16SyntaxError(f"Register range from r0-r15, r{reg_num} is out of this range")
    return reg_num

def parse_integer(text):
    try:
        return int(text)
    except ValueError:
        raise P16SyntaxError(f"{text} is not an integer")

class Line():
    def __init__(self, line):
        self.line = line
        self.bare_line = remove_comments(line)

    def length(self):
        return 0

    def __str__(self):
        return f"{type(self).__name__}({self.line})"

class OppLine(Line):
    def __init__(self, line):
        super().__init__(line)
        line_split = self.bare_line.split(" ")
        self.oppcode = line_split[0]
        opperands = line_split[1:]
        def check_num_opperands(n):
            if len(opperands) != n:
                raise P16SyntaxError(f"Oppcode {self.oppcode} has the wrong number of opperands, got {len(opperands)} but need {n}")
        if self.oppcode == "PASS":
            check_num_opperands(0)
        elif self.oppcode == "VALUE":
            check_num_opperands(1)
            self.value = parse_integer(opperands[0]) % (2 ** 16)
        elif self.oppcode == "JUMP":
            check_num_opperands(1)
            self.jumpto_label = opperands[0]
            self.jumpto_local = None
        elif self.oppcode == "BRANCH":
            check_num_opperands(2)
            condition = opperands[0]
            if not condition in BRANCH_CONDITIONS:
                raise P16SyntaxError(f"Unknown branch condition {condition}, must be one of " + ", ".join(cond for cond in BRANCH_CONDITIONS))
            self.condition = BRANCH_CONDITIONS[condition]
            assert type(self.condition) == int and 0 <= self.condition < 16
            self.jumpto_label = opperands[1]
            self.jumpto_local = None
        elif self.oppcode == "PUSH":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "POP":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "CALL":
            check_num_opperands(1)
            self.jumpto_label = opperands[0]
            self.jumpto_local = None
            #jumpto_page is set to:
            #("INTERNAL", None) for local calls
            #("ROM", page : int) for prom
            #("RAM", addr : int) for pram
            self.jumpto_page = None
            #the length depends on the value of jumpto_page, so we need to figure it out before finding exact addresses
        elif self.oppcode == "RETURN":
            check_num_opperands(0)
        elif self.oppcode == "ADD":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "ROTATE":
            check_num_opperands(2)
            self.rot_num = parse_integer(opperands[0])
            self.register = parse_register(opperands[1])
        elif self.oppcode in {"ALU", "RAM"}:
            if len(opperands) == 1:
                if opperands[0] in ALM1[self.oppcode]:
                    self.aluram_type = 1
                    self.opperation = ALM1[self.oppcode][opperands[0]]
                else:
                    raise P16SyntaxError(f"{opperands[0]} is not a valid {self.oppcode} opperation with 1 opperand")
            elif len(opperands) == 2:
                if opperands[0] in ALM2[self.oppcode]:
                    self.aluram_type = 2
                    self.opperation = ALM2[self.oppcode][opperands[0]]
                    self.register = parse_register(opperands[1])
                else:
                    raise P16SyntaxError(f"{opperands[0]} is not a valid {self.oppcode} opperation with 2 opperands")
            else:
                raise P16SyntaxError(f"ALU/RAM oppcode has the wrong number of opperands, got {len(opperands)} but need either 1 or 2")
        elif self.oppcode == "PAGERETURN":
            check_num_opperands(0)
        elif self.oppcode == "INPUT":
            check_num_opperands(0)
        elif self.oppcode == "OUTPUT":
            check_num_opperands(1)
            adr_oct_str = opperands[0]
            adr_oct = [parse_integer(n) for n in adr_oct_str.split(".")]
            for n in adr_oct:
                if n < 0 or n > 7:
                    raise P16SyntaxError(f"Octal output address values must range from 0-7 separated by dots, {adr_oct_str} is not of this form")
            self.address_octal = tuple(adr_oct)
        else:
            raise P16SyntaxError(f"Unknown oppcode {self.oppcode}")
        
        self.address = None

    def sets_flags(self):
        if self.oppcode == "ALU":
            return True
        return False

    def length(self):
        return len(self.compile())

    def compile(self):
        def int8_to_nibbles(val):
            if val is None:
                return "XX"
            else:
                return "0123456789ABCDEF"[val // 16] + "0123456789ABCDEF"[val % 16]

        alm1_opps = ["PASS", "NOT", "PREAD", "KREAD", "INC", "CIN", "DEC", "CDEC", "PTF", "DUP", "KTF", "DEL", "RSH", "CRSH", "IRSH", "ARSH"]
        alm2_opps = ["SWAP", "SUB", "KWRITE", "PWRITE", "AND", "NAND", "OR", "NOR", "XOR", "NXOR", "RTF", "CMP", "SADD", "SSUB", "CADD", "CSUB"]
        branch_conditions = {"I" : 0, "!I" : 1,
                             "Z" : 2, "=" : 2, "!Z" : 3, "!=" : 3,
                             "N" : 4, "!N" : 5,
                             "V" : 6, "!V" : 7,
                             "C" : 8, "u>=" : 8, "!C" : 9, "u<" : 9,
                             "u>" : 10, "u<=" : 11,
                             "s>=" : 12, "<" : 13,
                             "s>" : 14, "s<=" : 15}

        if self.oppcode == "PASS":
            return "0"
        elif self.oppcode == "VALUE":
            return "1" + "0123456789ABCDEF"[(self.value // (2 ** 12)) % 16] + "0123456789ABCDEF"[(self.value // (2 ** 8)) % 16] + "0123456789ABCDEF"[(self.value // (2 ** 4)) % 16] + "0123456789ABCDEF"[self.value % 16]
        elif self.oppcode == "JUMP":
            return "2" + int8_to_nibbles(self.jumpto_local)
        elif self.oppcode == "BRANCH":
            return "3" + "0123456789ABCDEF"[self.condition] + int8_to_nibbles(self.jumpto_local)
        elif self.oppcode == "PUSH":
            return "4" + "0123456789ABCDEF"[self.register]
        elif self.oppcode == "POP":
            return "5" + "0123456789ABCDEF"[self.register]
        elif self.oppcode == "CALL":
            medium, location = self.jumpto_page
            if medium == "INTERNAL":
                return "6" + int8_to_nibbles(self.jumpto_local)
            elif medium == "ROM":
                return "C" + "0123456789ABCDEF"[location] + int8_to_nibbles(self.jumpto_local)
            elif medium == "RAM":
                #push address
                ans = "1" + "0123456789ABCDEF"[(location // (2 ** 12)) % 16] + "0123456789ABCDEF"[(location // (2 ** 8)) % 16] + "0123456789ABCDEF"[(location // (2 ** 4)) % 16] + "0123456789ABCDEF"[location % 16]
                #then call ram
                ans += "D" + int8_to_nibbles(self.jumpto_local)
                return ans
            else:
                assert False
        elif self.oppcode == "RETURN":
            return "7"
        elif self.oppcode == "ADD":
            return "8" + "0123456789ABCDEF"[self.register]
        elif self.oppcode == "ROTATE":
            return "9" + "0123456789ABCDEF"[self.rot_num % 16] + "0123456789ABCDEF"[self.register]
        elif self.oppcode in alm1_opps:
            return "A" + "0123456789ABCDEF"[alm1_opps.index(self.oppcode)]
        elif self.oppcode in alm2_opps:
            return "B" + "0123456789ABCDEF"[alm2_opps.index(self.oppcode)] + "0123456789ABCDEF"[self.register]
        elif self.oppcode == "INPUT":
            return "E"
        elif self.oppcode == "OUTPUT":
            return "F" + "".join(str(n) for n in self.address_octal[:-1]) + "89ABCDEF"[self.address_octal[-1]]
        else:
            raise P16SyntaxError(f"Unknown oppcode \"{self.oppcode}\"")
                                
class DirLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.line_nodot = self.bare_line[1:]
        line_split = self.line_nodot.split(" ")
        self.cmd = line_split[0]
        def check_num_opperands(n):
            if len(opperands) != n:
                raise P16SyntaxError(f"Directive command .{self.cmd} has the wrong number of opperands, got {len(opperands)} but need {n}")
        opperands = line_split[1:]
        if self.cmd == "PROM":
            check_num_opperands(1)
            self.page = parse_integer(opperands[0])
            if self.page != self.page % 16:
                raise P16SyntaxError(f"rom page numbers range from 0-15, {self.page} is out of this range")
        elif self.cmd == "LABEL":
            check_num_opperands(1)
            self.label = opperands[0]
        elif self.cmd == "WAITFLAG":
            #add pass so that 6 nibbles have passed sinse the last flag setting opperation
            check_num_opperands(0)
        elif self.cmd == "PRAM":
            check_num_opperands(1)
            self.address = parse_integer(opperands[0])
            if not (0 <= self.address < 2 ** 12):
                raise P16SyntaxError(f"ram page addresses range from 0 to {2**12-1}, {self.address} is out of this range")
        else:
            raise P16SyntaxError(f"Unknown directive command .{self.cmd}")


def remove_comments(line):
    if "#" in line:
        idx = line.index("#")
        return line[:idx].strip()
    return line.strip()
        


def make_line(line):
    bare_line = remove_comments(line)
    if bare_line == "":
        return Line(line)
    elif bare_line[0] == ".":
        return DirLine(line)
    else:
        return OppLine(line)


class Page():
    def __init__(self, ident, lines):
        #1) convert directives into opperations
        new_lines = []
        last_flag_setter = 0
        for line in lines:
            if isinstance(line, OppLine):
                if line.sets_flags():
                    last_flag_setter = 0

            elif isinstance(line, DirLine):
                if line.cmd == "WAITFLAG":
                    while last_flag_setter < 6:
                        new_lines.append(make_line("PASS"))
                        last_flag_setter += 1
                    continue
                
            new_lines.append(line)
            last_flag_setter += line.length()
        lines = new_lines
                        
        self.lines = lines

    @property
    def length(self):
        return sum(line.length() for line in self.lines)

    def compile(self):
        nibbles = " ".join(line.compile() for line in self.lines if isinstance(line, OppLine))
        assert len(nibbles.replace(" ", "")) == self.length
        return nibbles






def compile_assembly(code):
    lines = [make_line(line) for line in code.split("\n")]
    pages = {} #page ident -> instructions
    
    current_page = None
    for line in lines:
        if isinstance(line, DirLine):
            if line.cmd in {"PROM", "PRAM"}:
                if line.cmd == "PROM":
                    current_page = ("ROM", line.page)
                elif line.cmd == "PRAM":
                    current_page = ("RAM", line.address)

                medium, location = current_page
                if medium == "ROM":
                    assert type(location) == int and 0 <= location < 16
                elif medium == "RAM":
                    assert type(location) == int and 0 <= location < 2 ** 12
                    
                if current_page in pages:
                    raise P16SyntaxError(f".PROM and .PRAM can be called at most once for each address")

                pages[current_page] = []
                
        if current_page is None and type(line) != Line: #disregard blank lines before the first page setter
            raise P16SyntaxError(f"You need to specify a page before any other commands. You probably need to add \".PROM 0\" as the first line of your code.")
        if not current_page is None:
            pages[current_page].append(line)

    #first we compute which page each label belongs to
    label_page_lookup = {}
    for ident, page in pages.items():
        for line in page:
            if isinstance(line, DirLine):
                if line.cmd == "LABEL":
                    if line.label in label_page_lookup:
                        raise P16SyntaxError(f"Label \"{line.label}\" cannot be used more than once")
                    label_page_lookup[line.label] = ident

    #now we can set the CALL instructions' jumpto_page
    for ident in pages:
        for line in pages[ident]:
            if isinstance(line, OppLine):
                if line.oppcode == "CALL":
                    if not line.jumpto_label in label_page_lookup:
                        raise P16SyntaxError(f"line {line} refers to label \"{line.jumpto_label}\", but this label has not been assigned anywhere.")
                    call_ident = label_page_lookup[line.jumpto_label]
                    if call_ident == ident:
                        line.jumpto_page = ("INTERNAL", None)
                    elif call_ident[0] == "ROM":
                        line.jumpto_page = call_ident
                    elif call_ident[0] == "RAM":
                        line.jumpto_page = call_ident
                    else:
                        assert False

    #then we compute the actual address. This is needed becasue the length of a CALL instruction depends on the type of page it is calling
    label_local_lookup = {} #label -> local_addr
    for ident, page in pages.items():
        local_addr = 0
        for line in page:
            if isinstance(line, DirLine):
                if line.cmd == "LABEL":
                    if line.label in label_local_lookup:
                        raise P16SyntaxError(f"Label \"{line.label}\" cannot be used more than once")
                    label_local_lookup[line.label] = local_addr
            local_addr += line.length()

    assert label_page_lookup.keys() == label_local_lookup.keys()

    #now we can compute local jump/branch/call addresses
    for ident in pages:
        for line in lines:
            if isinstance(line, OppLine):
                if line.oppcode in {"JUMP", "BRANCH", "CALL"}:
                    if not line.jumpto_label in label_local_lookup:
                        raise P16SyntaxError(f"line {line} refers to label \"{line.jumpto_label}\", but this label has not been assigned anywhere.")
                    goto_ident = label_page_lookup[line.jumpto_label]
                    if line.oppcode in {"JUMP", "BRANCH"} and ident != goto_ident:
                        raise P16SyntaxError(f"line {line} refers to label \"{line.jumpto_label}\". This label has been defined, but it must be defined in the current page for this opperation.")
                    line.jumpto_local = label_local_lookup[line.jumpto_label]

    pages = {ident : Page(ident, lines) for ident, lines in pages.items()}
    compiled_rom = {}
    compiled_ram = {}
    for ident in pages:
        medium, location = ident
        if medium == "ROM":
            compiled_rom[location] = pages[ident].compile()
        elif medium == "RAM":
            compiled_ram[location] = pages[ident].compile()
        else:
            assert False
    
    used_ram = set() #store the used ram locations in nibbles
    for addr, nibbles in compiled_ram.items():
        for offset, nibble in enumerate(nibbles):
            i = 4 * addr + offset #4* here becasue there are 4 nibbles per 16 bit ram location
            if i in used_ram:
                raise P16SyntaxError(f"RAM address {i} is used for more than one thing")
            elif i >= 2 ** 12:
                raise P16SyntaxError(f"RAM address {i} is out of range")
            else:
                used_ram.add(i)

    for page, nibbles in compiled_rom.items():
        for n in nibbles:
            assert n in "0123456789ABCDEF "
    for addr, nibbles in compiled_ram.items():
        for n in nibbles:
            assert n in "0123456789ABCDEF "
                
    return compiled_rom, compiled_ram
        



def compile_print(path):
    with open("P16_source.txt") as f:
        rom, ram = compile_assembly(f.read())
        for idx, page in rom.items():
            print(f"Rom {idx}: " + page)
        for idx, page in ram.items():
            print(f"Ram {idx}: " + page)


def compile_schem(source_path, active_pages = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}):
    import schemgen
    
    with open(source_path) as f:
        code, ram = compile_assembly(f.read())
        code = {p : code.get(p, "").replace(" ", "") for p in range(16)}

        ram_nibbles = {}
        for start_addr, nibbles in ram.items():
            for offset, nibble in enumerate(nibbles.replace(" ", "")):
                ram_nibbles[4 * start_addr + offset] = nibble #4* becasue each 16 bit ram location holds 4 nibbles

        def ram_adr_to_block_pos(i):
            n = [3, 2, 1, 0, 7, 6, 5, 4][i % 8] #which nibble in the block of 8
            xi = (i // (2 ** 10)) % 16
            yi = (i // (2 ** 3)) % 4 #which vertical block of 8 nibbles
            zi = (i // (2 ** 5)) % 32
            x_dir = [1, -1][xi % 2]

            x = 17 - 6 * xi - 3 * x_dir
            y = -119 + 18 * yi + 2 * n
            z = 29 - 4 * zi

            return x, y, z, x_dir

        def gen_blocks():            
            for page in range(16):
                if page in active_pages:
                    if page == 0:
                        for i in range(256):
                            if i < len(code[page]):
                                n = code[page][i]
                            else:
                                n = "0"

                            for b in range(4):
                                x, y, z = -5 - 2 * (3 - b) - 8 * (i // 32), 0, -5 -2 * (i % 32)
                                if ("0123456789ABCDEF".index(n) & 2 ** b):
                                    yield schemgen.Block(x, y, z, "minecraft:lever", extra = "[facing=east,face=floor,powered=true]")
                                else:
                                    yield schemgen.Block(x, y, z, "minecraft:lever", extra = "[facing=east,face=floor,powered=false]")
                    
                    
                    elif page in {1, 2, 3}:
                        for i in range(256):
                            if i < len(code[page]):
                                n = code[page][i]
                            else:
                                n = "0"
                            
                            for b in range(4):
                                x, y, z = -5 - 2 * (3 - b) - 8 * (i // 32), -5 - 5 * page, -5 -2 * (i % 32)
                                if ("0123456789ABCDEF".index(n) & 2 ** b):
                                    yield schemgen.Block(x, y, z, "minecraft:redstone_wall_torch", extra = "[facing=north,lit=false]")
                                else:
                                    yield schemgen.Block(x, y, z, "minecraft:glass")
                    
                    elif page in {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}:
                        p = page - 4
                        xo = -13
                        yo = -27 + (p % 2) * 16
                        zo = 13 + 4 * (p // 2)
                        
                        for i in range(256):
                            if i < len(code[page]):
                                n = code[page][i]
                            else:
                                n = "0"
                            
                            for b in range(4):
                                x, y, z = xo - 2 * (i % 32), yo - 2 * (i // 32), zo
                                m = "0123456789ABCDEF".index(n)
                                if m == 0:
                                    yield schemgen.Block(x, y, z, "minecraft:glass")
                                else:
                                    yield schemgen.Signal(x, y, z, m)
        
        
        file = schemgen.blocks_to_schem(gen_blocks(), 0, 0, 0)
        file.save("rom.schem")
        print(f"PROM schematic saved. \"//paste -a\" on the start button.")
        
        def gen_blocks():            
            for i, n in ram_nibbles.items():
                x, y, z, x_dir = ram_adr_to_block_pos(i)
                yield schemgen.Block(x + 2 * x_dir, y, z - 1, "minecraft:glass")
                if ram_nibbles[i] == "0":
                    yield schemgen.Block(x + x_dir, y, z, "minecraft:brown_wool")
                else:
                    yield schemgen.Signal(x + x_dir, y, z, "0123456789ABCDEF".index(n))
        
        file = schemgen.blocks_to_schem(gen_blocks(), 0, 0, 0)
        file.save("ram.schem")
        print(f"PRAM schematic saved. \"//paste -a\" on the start button and then \"//undo\".")


        



if __name__ == "__main__":
    compile_print("P16_source.txt") #ass -> schem
    compile_schem("P16_source.txt") #ass -> schem
























