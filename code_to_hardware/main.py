import functools

#levels of abstraction
#algorithm : what shall the components compute
#connectivity : abstract connectivity of components with best-case timings
#layout : placement of components in mc world & retiming
#schem : placement of blocks in a schematic file

#example algorithms to run:
#fib
#multiplication
#division
#gcd
#brezenham
#brezenham circles
#mandelbrot
#floating point opperations

class DataInput():
    def __init__(self):
        pass

class DataOutput():
    def __init__(self):
        pass

class FlagInput():
    def __init__(self):
        pass

class FlagOutput():
    def __init__(self):
        pass




class Kind():
    pass

@functools.cache
def IntegerKind(bits):
    class Integer(Kind):
        def __init__(self, value):
            assert type(value) == int
            self.value = value % (2 ** bits)
    return Integer
            

class Declare():
    def __init__(self, kind, name):
        assert issubclass(kind, Kind)
        assert type(name) == str
        self.kind = kind
        self.name = name

class Assign():
    def __init__(self, var, value):
        assert isinstance(var, Declare)
        assert isinstance(value, var.kind)
        self.var = var
        self.value = value

class CodeBlock():
    @classmethod
    def parse(cls, code):
        def parse_block(code):
            while True:
                new_code = code.replace("\n", " ").replace("  ", " ").strip(" ")
                new_code = new_code.replace("{ ", "{").replace(" }", "}")
                new_code = new_code.replace("( ", "(").replace(" )", ")")
                new_code = new_code.replace("; ", ";").replace(" ;", ";")
                if new_code == code:
                    break
                code = new_code

            
            print(code)

        parse_block(code)
            


    def __init__(self):
        pass



if __name__ == "__main__":
    code = """
    int16 a = 7;
    int16 b = 12;

    int16 c;
    c = a + b;

    if (a == c) {
        b = b + 1;
    }

    output a, b, c;
    """

    code_block = CodeBlock.parse(code)

    print(code_block)



