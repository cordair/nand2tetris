import os, re, sys, glob

END_LINE = "\n"

TEMP = 5
THIS = 3

class Parser:
    def __init__(self, codeWriter):
        self.codeWriter = codeWriter
        self.currentCommand = []

    def parse(self, vm_filename):
        with open(vm_filename, 'r') as read_file:
            for line in read_file.readlines():
                if (self.invalidLine(line)):
                    continue
                self.currentCommand = line.split()
                if (self.commandType() == "C_ARITHMETIC"):
                    self.codeWriter.writeArithmetic(self.arg0())
                elif (self.commandType() == "C_PUSH"):
                    self.codeWriter.writePush(self.arg1()[0], self.arg1()[1])
                elif (self.commandType() == "C_POP"):
                    self.codeWriter.writePop(self.arg1()[0], self.arg1()[1])
                elif (self.commandType() == "C_LABEL"):
                    self.codeWriter.writeLabel(self.arg1()[0])
                elif (self.commandType() == "C_IF"):
                    self.codeWriter.writeIf(self.arg1()[0])
                elif (self.commandType() == "C_GOTO"):
                    self.codeWriter.writeGoto(self.arg1()[0])
                elif (self.commandType() == "C_FUNCTION"):
                    self.codeWriter.writeFunction(self.arg1()[0], self.arg1()[1])
                elif (self.commandType() == "C_CALL"):
                    self.codeWriter.writeCall(self.arg1()[0], self.arg1()[1])
                elif (self.commandType() == "C_RETURN"):
                    self.codeWriter.writeReturn()
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
        switcher = {
            "label":    "C_LABEL",
            "return":   "C_RETURN",
            "goto":     "C_GOTO",
            "if-goto":  "C_IF",
            "function": "C_FUNCTION",
            "call":     "C_CALL",
            "push":     "C_PUSH",
            "pop":      "C_POP",
            "add":      "C_ARITHMETIC",
            "sub":      "C_ARITHMETIC",
            "not":      "C_ARITHMETIC",
            "neg":      "C_ARITHMETIC",
            "or":       "C_ARITHMETIC",
            "and":      "C_ARITHMETIC",
            "lt":       "C_ARITHMETIC",
            "gt":       "C_ARITHMETIC",
            "eq":       "C_ARITHMETIC",
        }
        return switcher.get(self.arg0(), "Not a command!")

    def arg0(self):
        return self.currentCommand[0]

    def arg1(self):
        return self.currentCommand[1:]

class CodeWriter:
    def __init__(self, asm_file):
        self.file = asm_file
        self.label_number = 0
        self.function_number = 0
        self.file_name = ""

    def setFileName(self, vm_filename):
        self.file_name = os.path.basename(vm_filename).split('.')[0]

    def write(self, line):
        self.file.write(line + END_LINE)

# ------------------------ARITHMETIC + MEMORY implementation---------------------------

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
            self.increaseLabelNumber()
        elif (arith == "lt"):
            self.performCompare("LT")
            self.label_number += 1
        elif (arith == "gt"):
            self.performCompare("GT")
            self.label_number += 1

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

    def storeSegmentAddress(self, segment, address):
        self.write("@{address}".format(address = address))
        self.write("D=A")
        self.write("@{segment}".format(segment = segment))
        self.write("D=M+D")
        self.write("@addr")
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
            address = self.file_name + address
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
            address = self.file_name + address
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


# ------------------------GOTO + FUNCTION implementation---------------------------
    def writeInit(self):
        self.write("@256")
        self.write("D=A")
        self.write("@SP")
        self.write("M=D")
        self.writeCall("Sys.init", 0)
        
    def writeLabel(self, label):
        self.write("({label})".format(label=label))

    def writeGoto(self, label):
        self.write("@{label}".format(label=label))
        self.write("0;JMP")

    def writeIf(self, label):
        self.popFromStack()
        self.write("@{label}".format(label=label))
        self.write("D;JNE")

    def writeFunction(self, function_name, num_local):
        self.write("({function_name})".format(function_name=function_name))
        for i in range(int(num_local)):
            self.write("D=0")
            self.pushToStack()

    def writeCall(self, function_name, num_var):
        # save address, LCL, ARG, THIS, THAT
        self.write("@{function_name}$ret.{i}".format(function_name=function_name, i=self.function_number))
        self.write("D=A")
        self.pushToStack()
        self.popFromAddress("LCL")
        self.pushToStack()
        self.popFromAddress("ARG")
        self.pushToStack()
        self.popFromAddress("THIS")
        self.pushToStack()
        self.popFromAddress("THAT")
        self.pushToStack()

        # reposition ARG
        self.write("@{x}".format(x=5+int(num_var)))
        self.write("D=A")
        self.write("@SP")
        self.write("D=M-D")
        self.pushToAddress("ARG")
        
        # reposition LCL
        self.popFromAddress("SP")
        self.pushToAddress("LCL")
        
        # jump to desination function
        self.write("@{function_name}".format(function_name=function_name))
        self.write("0;JMP")

        # write return label
        self.write("({function_name}$ret.{i})".format(function_name=function_name, i=self.function_number))
        self.function_number += 1

    def writeReturn(self):
        # end_frame = LCL
        self.popFromAddress("LCL")
        self.pushToAddress("R13")

        # ret_addr = *(end_frame - 5)
        self.write("@5")
        self.write("A=D-A")
        self.write("D=M")
        self.pushToAddress("R14")

        # *ARG = pop()
        self.popFromStack()
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")

        # SP = ARG + 1
        self.write("@ARG")
        self.write("D=M")
        self.write("@SP")
        self.write("M=D+1")

        # THAT = *(end_frame - 1)
        self.write("@R13")
        self.write("AM=M-1")
        self.write("D=M")
        self.pushToAddress("THAT")

        # THIS = *(end_frame - 2)
        self.write("@R13")
        self.write("AM=M-1")
        self.write("D=M")
        self.pushToAddress("THIS")

        # ARG =  *(end_frame - 3)
        self.write("@R13")
        self.write("AM=M-1")
        self.write("D=M")
        self.pushToAddress("ARG")

        # LCL =  *(end_frame - 4)
        self.write("@R13")
        self.write("AM=M-1")
        self.write("D=M")
        self.pushToAddress("LCL")

        # goto ret_addr
        self.popFromAddress("R14")
        self.write("A=D")
        self.write("0;JMP")


    def close(self):
        self.file.close()

class Main:
    def __init__(self, argv):
        if len(argv) != 0 and os.path.isdir(argv[0]):
            self.translateDirectory(argv[0])
        elif len(argv) != 0 and os.path.splitext(argv[0])[1] == ".vm":
            self.translateFile(argv[0])
        else:
            print("Command: python VMTranslator.y <filename>.vm")
            sys.exit(1)

    def translateDirectory(self, directory):
        asm_filename = directory + '/' + os.path.basename(directory) + '.asm'
        with open(asm_filename, "w") as asm_file:
            codeWriter = CodeWriter(asm_file)
            codeWriter.writeInit()
            parser = Parser(codeWriter)
            for vm_filename in glob.glob(directory + "/*.vm"):
                codeWriter.setFileName(vm_filename)
                parser.parse(vm_filename)
            codeWriter.close()

    def translateFile(self, vm_filename):
        asm_filename = os.path.splitext(vm_filename)[0] + ".asm"
        with open(asm_filename, "w") as asm_file:
            codeWriter = CodeWriter(asm_file)
            parser = Parser(codeWriter)
            parser.parse(vm_filename)
            codeWriter.close()
            
if __name__ == '__main__':
    Main(sys.argv[1:])