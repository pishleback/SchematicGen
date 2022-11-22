BRANCH_CONDITIONS = {"I" : 0,
                     "!I" : 1,
                     "Z" : 2,
                     "!Z" : 3,
                     "N" : 4,
                     "!N" : 5,
                     "V" : 6,
                     "!V" : 7,
                     "C" : 8,
                     "!C" : 9,
                     "C&!Z" : 10,
                     "!Z&C" : 10,
                     "!C|Z" : 11,
                     "Z|!C" : 11,
                     "N=V" : 12,
                     "V=N" : 12,
                     "N!=V" : 13,
                     "V!=N" : 13,
                     "N=V&!Z" : 14,
                     "V=N&!Z" : 14,
                     "!Z&N=V" : 14,
                     "!Z&V=N" : 14,
                     "N!=V|Z" : 15,
                     "V!=N|Z" : 15,
                     "Z|N!=V" : 15,
                     "Z|V!=N" : 15}


ALM1 = {"ALU" : {"not" : 0,
                 "inc" : 4,
                 "cin" : 5,
                 "dec" : 6,
                 "dec_cin" : 7,
                 "dup" : 8,
                 "nop" : 9,
                 "stf" : 10,
                 "del" : 11,
                 "rsh" : 12,
                 "rsh_cin" : 13,
                 "rsh_1in" : 14,
                 "rsha" : 15},
        "RAM" : {"read" : 1,
                 "read_inc" : 2,
                 "read_dec" : 3}}



ALM2 = {"ALU" : {"sub" : 0,
                 "and" : 4,
                 "nand" : 5,
                 "or" : 6,
                 "nor" : 7,
                 "xor" : 8,
                 "nxor" : 9,
                 "rtf" : 10,
                 "cmp" : 11,
                 "sad" : 12,
                 "sas" : 13,
                 "add_cin" : 14,
                 "sub_cin" : 15},
        "RAM" : {"write" : 1,
                 "write_inc" : 2,
                 "write_dec" : 3}}


def parse_register(text):
    assert text != ""
    if text[0] != "r":
        raise Exception(f"P16 Syntax error: Registers must begin with an \"r\", for example \"r5\"")
    reg_num = parse_integer(text[1:])
    if reg_num < 0 or reg_num > 15:
        raise Exception(f"P16 Syntax error: register range from r0-r15, r{reg_num} is out of this range")
    return reg_num

def parse_integer(text):
    try:
        return int(text)
    except ValueError:
        raise Exception(f"P16 Syntax error: {text} is not an integer")

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
                raise Exception(f"P16 Syntax error: Oppcode {self.oppcode} has the wrong number of opperands, got {len(opperands)} but need {n}")
        if self.oppcode == "PASS":
            check_num_opperands(0)
        elif self.oppcode == "VALUE":
            check_num_opperands(1)
            self.value = parse_integer(opperands[0])
        elif self.oppcode == "JUMP":
            check_num_opperands(1)
            self.jumpto = opperands[0]
            self.jumpto_num = None
        elif self.oppcode == "BRANCH":
            check_num_opperands(2)
            condition = opperands[0]
            if not condition in BRANCH_CONDITIONS:
                raise Exception(f"P16 Syntax error: Unknown branch condition {condition}, must be one of " + ", ".join(cond for cond in BRANCH_CONDITIONS))
            self.condition = BRANCH_CONDITIONS[condition]
            assert type(self.condition) == int and 0 <= self.condition < 16
            self.jumpto = opperands[1]
            self.jumpto_num = None
        elif self.oppcode == "PUSH":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "POP":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "CALL":
            check_num_opperands(1)
            self.jumpto = opperands[0]
            self.jumpto_num = None
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
                    raise Exception(f"P16 Syntax error: {opperands[0]} is not a valid {self.oppcode} opperation with 1 opperand")
            elif len(opperands) == 2:
                if opperands[0] in ALM2[self.oppcode]:
                    self.aluram_type = 2
                    self.opperation = ALM2[self.oppcode][opperands[0]]
                    self.register = parse_register(opperands[1])
                else:
                    raise Exception(f"P16 Syntax error: {opperands[0]} is not a valid {self.oppcode} opperation with 2 opperands")
            else:
                raise Exception(f"P16 Syntax error: ALU/RAM oppcode has the wrong number of opperands, got {len(opperands)} but need either 1 or 2")
        elif self.oppcode == "PAGE":
            check_num_opperands(1)
            self.page = parse_integer(opperands[0])
            if self.page < 0 or self.page > 15:
                raise Exception(f"P16 Syntax error: Pages range from 0-15, {self.page} is out of this range")
        elif self.oppcode == "POPKEEP":
            check_num_opperands(1)
            self.register = parse_register(opperands[0])
        elif self.oppcode == "INPUT":
            check_num_opperands(0)
        elif self.oppcode == "OUTPUT":
            check_num_opperands(1)
            adr_oct_str = opperands[0]
            adr_oct = [parse_integer(n) for n in adr_oct_str.split(".")]
            for n in adr_oct:
                if n < 0 or n > 7:
                    raise Exception(f"P16 Syntax error: Octal output address values must range from 0-7 separated by dots, {adr_oct_str} is not of this form")
            self.address_octal = tuple(adr_oct)
        else:
            raise Exception(f"P16 Syntax error: Unknown oppcode {self.oppcode}")
        
        self.address = None

    def sets_flags(self):
        if self.oppcode == "ALU":
            return True
        return False

    def length(self):
        if self.oppcode in {"ALU", "RAM"}:
            return 1 + self.aluram_type
        elif self.oppcode in {"PASS", "RETURN", "INPUT"}:
            return 1
        elif self.oppcode in {"PUSH", "POP", "ADD", "PAGE", "POPKEEP"}:
            return 2
        elif self.oppcode in {"VALUE", "JUMP", "CALL", "ROTATE"}:
            return 3
        elif self.oppcode in {"BRANCH"}:
            return 4
        elif self.oppcode == "OUTPUT":
            return 1 + len(self.address_octal)
        else:
            raise NotImplementedError()

    def compile(self):
        if self.oppcode in {"ALU", "RAM"}:
            if self.aluram_type == 1:
                oppcode = "A"
            elif self.aluram_type == 2:
                oppcode = "B"
            else:
                assert False
        else:
            oppcode = {"PASS" : "0",
                       "VALUE" : "1",
                       "JUMP" : "2",
                       "BRANCH" : "3",
                       "PUSH" : "4",
                       "POP" : "5",
                       "CALL" : "6",
                       "RETURN" : "7",
                       "ADD" : "8",
                       "ROTATE" : "9",
                       "PAGE" : "C",
                       "POPKEEP" : "D",
                       "INPUT" : "E",
                       "OUTPUT" : "F"}[self.oppcode]

        if self.oppcode in {"ALU", "RAM"}:
            if self.aluram_type == 1:
                opperands = "0123456789ABCDEF"[self.opperation]
            elif self.aluram_type == 2:
                opperands = "0123456789ABCDEF"[self.opperation] + "0123456789ABCDEF"[self.register]
            else:
                assert False
        elif self.oppcode in {"PASS", "RETURN", "INPUT"}:
            opperands = ""
        elif self.oppcode in {"PUSH", "POP", "ADD", "POPKEEP"}:
            opperands = "0123456789ABCDEF"[self.register]
        elif self.oppcode == "PAGE":
            opperands = "0123456789ABCDEF"[self.page]
        elif self.oppcode == "VALUE":
            opperands = "0123456789ABCDEF"[self.value // 16] + "0123456789ABCDEF"[self.value % 16]
        elif self.oppcode in {"JUMP", "CALL"}:
            opperands = "0123456789ABCDEF"[self.jumpto_num // 16] + "0123456789ABCDEF"[self.jumpto_num % 16]
        elif self.oppcode == "ROTATE":
            opperands = "0123456789ABCDEF"[self.rot_num % 16] + "0123456789ABCDEF"[self.register]
        elif self.oppcode in {"BRANCH"}:
            opperands = "0123456789ABCDEF"[self.condition] + "0123456789ABCDEF"[self.jumpto_num // 16] + "0123456789ABCDEF"[self.jumpto_num % 16]
        elif self.oppcode == "OUTPUT":
            opperands = "".join(str(n) for n in self.address_octal[:-1]) + "89ABCDEF"[self.address_octal[-1]]
        else:
            assert False
        return oppcode + opperands
        
class DirLine(Line):
    def __init__(self, line):
        super().__init__(line)
        self.line_nodot = self.bare_line[1:]
        line_split = self.line_nodot.split(" ")
        self.cmd = line_split[0]
        def check_num_opperands(n):
            if len(opperands) != n:
                raise Exception(f"P16 Syntax error: Directive command .{self.cmd} has the wrong number of opperands, got {len(opperands)} but need {n}")
        opperands = line_split[1:]
        if self.cmd == "PAGE":
            check_num_opperands(1)
            self.page = parse_integer(opperands[0])
            if self.page != self.page % 16:
                raise Exception(f"P16 Syntax error: page numbers range from 0-15, {self.page} is out of this range")
        elif self.cmd == "LABEL":
            check_num_opperands(1)
            self.label = opperands[0]
        elif self.cmd == "WAITFLAG":
            #add pass so that 6 nibbles have passed sinse the last flag setting opperation
            check_num_opperands(0)
        else:
            raise Exception(f"P16 Syntax error: Unknown directive command .{self.cmd}")


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
    def __init__(self, page_num, lines):
        assert type(page_num) == int and 0 <= page_num < 16
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
                
        #2) find locations of labels
        label_dict = {}
        adr = 0
        for line in lines:
            if isinstance(line, DirLine):
                if line.cmd == "LABEL":
                    if line.label in label_dict:
                        raise Exception(f"P16 Syntax error: label \"{line.label}\" can only be assigned once per page")
                    else:
                        label_dict[line.label] = adr
            adr += line.length()
        self.length = adr
        
        #3) assign addresses to jump, branch and call address labels
        for line in lines:
            if isinstance(line, OppLine):
                if line.oppcode in {"JUMP", "BRANCH", "CALL"}:
                    if not line.jumpto in label_dict:
                        raise Exception(f"P16 Syntax error: line {line} refers to label \"{line.jumpto}\", but this label has not been assigned")
                    else:
                        line.jumpto_num = label_dict[line.jumpto]

        self.page_num = page_num
        self.lines = lines

    def compile(self):
        nibbles = " ".join(line.compile() for line in self.lines if isinstance(line, OppLine))
        assert len(nibbles.replace(" ", "")) == self.length
        return nibbles


class Assembly():
    def __init__(self, code):
        self.lines = [make_line(line) for line in code.split("\n")]
        pages = {p : [] for p in range(16)}

        current_page = None
        for line in self.lines:
            if isinstance(line, DirLine):
                if line.cmd == "PAGE":
                    current_page = line.page
            if current_page is None and type(line) != Line: #disregard blank lines before the first page setter
                raise Exception(f"P16 Syntax error: You need to specify a page before any other commands. You probably need to add \".PAGE 0\" as the first line of your code.")
            if not current_page is None:
                pages[current_page].append(line)

        self.pages = [Page(p, pages[p]) for p in range(16)]

    def compile(self):
        compiled_pages = {}
        for idx, page in enumerate(self.pages):
            compiled_page = page.compile()
            if (n := len(compiled_page.replace(" ", ""))) > 256:
                print(f"Warning: Page {idx} consists of {n} pages. This exceeds the maximum number of 256")
            compiled_pages[idx] = compiled_page
        return compiled_pages
        



def compile_print(path):
    with open("P16_source.txt") as f:
        c = Assembly(f.read()).compile()
        for i in range(16):
            if len(c[i]) != 0:
                print(f"Page {i}:" + c[i])


def compile_schem(source_path, target_path, active_pages = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}): #dont compile page 0 by default
    import schemgen
    compile_print(source_path)
    
    with open(source_path) as f:
        code = Assembly(f.read()).compile()
        code = {p : code[p].replace(" ", "") for p in range(16)}

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
                                m =  "0123456789ABCDEF".index(n)
                                if m == 0:
                                    yield schemgen.Block(x, y, z, "minecraft:glass")
                                else:
                                    yield schemgen.Signal(x, y, z, m)
                        

        file = schemgen.blocks_to_schem(gen_blocks(), 0, 0, 0)
        file.save(target_path)
        print("Schematic saved")



if __name__ == "__main__":
    compile_schem("P16_source.txt", "P16_output.schem") #ass -> schem
























