import os, re, sys

END_LINE = "\n"

TEMP = 5
THIS = 3
STATIC = "S"

class Parser:
    def __init__(self, vm_filename):
        self.vm_filename = vm_filename
        self.currentCommand = []

    def parse(self, codeWriter):
        with open(self.vm_filename, 'r') as read_file:
            for line in read_file.readlines():
                if (self.invalidLine(line)):
                    continue
                self.currentCommand = line.split()
                if (self.commandType() == "C_ARITHMETIC"):
                    codeWriter.writeArithmetic(self.arg1())
                elif (self.commandType() == "C_PUSH"):
                    codeWriter.writePush(self.arg2()[0], self.arg2()[1])
                elif (self.commandType() == "C_POP"):
                    codeWriter.writePop(self.arg2()[0], self.arg2()[1])
            read_file.close()


    def invalidLine(self, line):
        empty_line_regex = "^\s*$"
        comment_regex = "(?:(?<=^)|(?<=\n))\s*//.*"

        is_empty_line = re.match(empty_line_regex, line)
        is_comment = re.match(comment_regex, line)

        if (is_empty_line or is_comment):
            return True
        return False

    def commandType(self):
        if (len(self.currentCommand) == 1):
            return "C_ARITHMETIC"
        return "C_PUSH" if self.arg1() == "push" else "C_POP"
    
    def arg1(self):
        return self.currentCommand[0]

    def arg2(self):
        return self.currentCommand[1:]

class CodeWriter:
    def __init__(self, asm_file):
        self.file = asm_file
        self.label_number = 0

    def write(self, line):
        self.file.write(line + END_LINE)

    def getTwoValues(self):
        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")
        self.write("A=A-1")

    def performAdd(self):
        self.write("M=D+M")

    def performSub(self):
        self.write("MD=M-D")

    def performAnd(self):
        self.write("M=M&D")
        
    def performOr(self):
        self.write("M=M|D")
        
    def performNot(self):
        self.write("@SP")
        self.write("A=M-1")
        self.write("M=!M")

    def performNeg(self):
        self.write("@SP")
        self.write("A=M-1")
        self.write("M=-M")

    def performCompare(self, compareType):
        label = compareType + str(self.label_number)
        end = "end{label}".format(label=compareType) + str(self.label_number)
        self.getTwoValues()
        self.performSub()
        self.write("@{label}".format(label=label))
        self.write("D;J{compareType}".format(compareType=compareType))
        self.write("@SP")
        self.write("A=M-1")
        self.write("M=0")
        self.write("@{end}".format(end=end))
        self.write("0;JMP")
        self.write("({label})".format(label=label))
        self.write("@SP")
        self.write("A=M-1")
        self.write("M=-1")
        self.write("({end})".format(end=end))

    def writeArithmetic(self, arith):
        if (arith == "add"):
            self.getTwoValues()
            self.performAdd()
        elif (arith == "sub"):
            self.getTwoValues()
            self.performSub()
        elif (arith == "and"):
            self.getTwoValues()
            self.performAnd()
        elif (arith == "or"):
            self.getTwoValues()
            self.performOr()
        elif (arith == "not"):
            self.performNot()
        elif (arith == "neg"):
            self.performNeg()
        elif (arith == "eq"):
            self.performCompare("EQ")
            self.label_number += 1
        elif (arith == "lt"):
            self.performCompare("LT")
            self.label_number += 1
        elif (arith == "gt"):
            self.performCompare("GT")
            self.label_number += 1

    def storeSegmentAddress(self, segment, address):
        self.write("@{address}".format(address = address))
        self.write("D=A")
        self.write("@{segment}".format(segment = segment))
        self.write("D=M+D")
        self.write("@addr")
        self.write("M=D")

    def pushToStack(self):
        self.write("@SP")
        self.write("AM=M+1")
        self.write("A=A-1")
        self.write("M=D")

    def popFromStack(self):
        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")

    def pushToSegment(self):
        self.write("@addr")
        self.write("A=M")
        self.write("M=D")

    def popFromSegment(self, segment, address):
        self.write("@{address}".format(address = address))
        self.write("D=A")
        self.write("@{segment}".format(segment = segment))
        self.write("A=M+D")
        self.write("D=M")

    def pushToAddress(self, address):
        self.write("@{address}".format(address = address))
        self.write("M=D")
    
    def popFromAddress(self, address):
        self.write("@{address}".format(address = address))
        self.write("D=M")

    def popAddress(self, address):
        self.write("@{address}".format(address = address))
        self.write("D=A")

    def writePush(self, segment, address):
        if (segment == "local"):
            self.popFromSegment("LCL", address)
        elif (segment == "argument"):
            self.popFromSegment("ARG", address)
        elif (segment == "this"):
            self.popFromSegment("THIS", address)
        elif (segment == "that"):
            self.popFromSegment("THAT", address)
        elif (segment == "temp"):
            address = int(address) + TEMP
            self.popFromAddress(address)
        elif (segment == "constant"):
            self.popAddress(address)
        elif (segment == "static"):
            address = STATIC + address
            self.popFromAddress(address)
        elif (segment == "pointer"):
            address = int(address) + THIS
            self.popFromAddress(address)
        self.pushToStack()

    def writePop(self, segment, address):
        if (segment == "local"):
            self.storeSegmentAddress("LCL", address)
        elif (segment == "argument"):
            self.storeSegmentAddress("ARG", address)
        elif (segment == "this"):
            self.storeSegmentAddress("THIS", address)
        elif (segment == "that"):
            self.storeSegmentAddress("THAT", address)
        elif (segment == "temp"):
            address = int(address) + TEMP
            self.popFromStack()
            self.pushToAddress(address)
            return
        elif (segment == "static"):
            address = STATIC + address
            self.popFromStack()
            self.pushToAddress(address)
            return
        elif (segment == "pointer"):
            address = int(address) + THIS
            self.popFromStack()
            self.pushToAddress(address)
            return
        self.popFromStack()
        self.pushToSegment()

    def close(self):
        self.file.close()

class Main:
    def __init__(self, argv):
        if len(argv) != 0 and os.path.splitext(argv[0])[1] == ".vm":
            self.translateFile(argv[0])
        else:
            print("Command: python VMTranslator.py <filename>.vm")
            sys.exit(1)

    def translateFile(self, vm_filename):
        asm_filename = os.path.splitext(vm_filename)[0] + ".asm"
        with open(asm_filename, "w") as asm_file:
            parser = Parser(vm_filename)
            codeWriter = CodeWriter(asm_file)
            parser.parse(codeWriter)
            codeWriter.close()
            
if __name__ == '__main__':
    Main(sys.argv[1:])