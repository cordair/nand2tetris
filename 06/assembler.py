COMP = {
    "0" :   "0101010",
    "1" :   "0111111",
    "-1":   "0111010",
    "D" :   "0001100",
    "A" :   "0110000",   "M" :     "1110000",
    "!D":   "0001101",
    "!A":   "0110001",   "!M" :    "1110001",
    "-D":   "0001111",
    "-A":   "0110011",   "-M" :    "1110011", 
    "D+1":  "0011111",
    "A+1":  "0110111",   "M+1" :   "1110111", 
    "D-1":  "0001110",
    "A-1":  "0110010",   "M-1" :   "1110010",
    "D+A":  "0000010",   "D+M" :   "1000010",
    "D-A":  "0010011",   "D-M" :   "1010011",
    "A-D":  "0000111",   "M-D" :   "1000111",
    "D&A":  "0000000",   "D&M" :   "1000000",
    "D|A":  "0010101",   "D|M" :   "1010101",
}

DEST = {
    "null": "000",
    "M":    "001",
    "D":    "010",
    "MD":   "011",
    "A":    "100",
    "AM":   "101",   
    "AD":   "110",
    "AMD":  "111",
}

JUMP = {
    "null": "000",
    "JGT":  "001",
    "JEQ":  "010",
    "JGE":  "011",
    "JLT":  "100",
    "JNE":  "101",
    "JLE":  "110",
    "JMP":  "111",
}

class SymbolTable:
    def __init__(self):
        self.symbol_table = {
        "SP":    "0",
        "LCL":   "1",
        "ARG":   "2",
        "THIS":  "3",
        "THAT":  "4",
        "R0":    "0",   
        "R1":    "1",
        "R2":    "2",
        "R3":    "3",
        "R4":    "4",
        "R5":    "5",
        "R6":    "6",
        "R7":    "7",
        "R8":    "8",
        "R9":    "9",
        "R10":   "10",
        "R11":   "11",
        "R12":   "12",
        "R13":   "13",
        "R14":   "14",
        "R15":   "15",
        "SCREEN":"16384",
        "KBD":   "24567",
    }

    def getSymbolTable(self):
        return self.symbol_table

    def addEntry(self, entry, value):
        self.symbol_table[entry] = value
    
    def contains(self, entry):
        return (entry in self.symbol_table)

    def getAddress(self, entry):
        return self.symbol_table[entry]

class Code:
    def __init__(self, words):
        self.words = words
        if ('=' in words):
            word_list = words.split('=')
            self.dest = word_list[0]
            self.comp = word_list[1]
            self.jump = "null"
        elif (';' in words):
            word_list = words.split(';')
            self.dest = "null"
            self.comp = word_list[0]
            self.jump = word_list[1]

    def generateCode(self):
        return COMP[self.comp] + DEST[self.dest] + JUMP[self.jump]

class Parser:
    def __init__(self, read_file_name, write_file_name):
        self.read_file_name = read_file_name
        self.write_file_name = write_file_name
        self.symbolTable = SymbolTable()

    def parse(self):
        self.createSymbolTable()
        self.assignVariables()
        self.parsing()

    def createSymbolTable(self):
        with open(self.read_file_name, "r") as read_file:
            line_count = 0
            for line in read_file.readlines():
                words = ""
                for word in line.split():
                    if (word == "//"):
                        break
                    words = words + word
                if (len(words) == 0):
                    continue

                if (words[0] == '('):
                    self.symbolTable.addEntry(words[1:-1], line_count)
                    continue
                line_count += 1
            read_file.close()

    def assignVariables(self):
        with open(self.read_file_name, "r") as read_file:
            ram_index = 16
            for line in read_file.readlines():
                words = ""
                for word in line.split():
                    if (word == "//"):
                        break
                    words = words + word
                if (len(words) == 0):
                    continue
                if (words[0] == '@' and not (words[1:]).isnumeric()):
                    entry = words[1:]
                    if (not self.symbolTable.contains(entry)):
                        self.symbolTable.addEntry(entry, ram_index)
                        ram_index += 1
            read_file.close()

    def parsing(self):
        with open(self.read_file_name, "r") as read_file:
            write_file = open(self.write_file_name, 'w')
            for line in read_file.readlines():
                words = ""
                for word in line.split():
                    if (word == "//"):
                        break
                    words = words + word
                if (len(words) == 0):
                    continue
                
                if (words[0] == '('):
                    self.instructionType = "F_Instruction"
                    continue
                elif (words[0] == '@'):
                    if (self.symbolTable.contains(words[1:])):
                        address = self.symbolTable.getAddress(words[1:])
                    else:
                        address = words[1:]
                    self.instructionType = "A_Instruction"
                    self.currentInstruction = "{0:b}".format(int(address)).zfill(16)
                else:
                    self.instructionType = "C_Instruction"
                    code = Code(words)
                    self.currentInstruction = code.generateCode().rjust(16, '1')
                write_file.write(self.currentInstruction)
                write_file.write("\n")

            read_file.close()
            write_file.close()

    def commandType(self):
        return self.instructionType
    def instruction(self):
        return self.currentInstruction

if __name__ == "__main__":
    parser = Parser("06/max/MaxL.asm", "06/MaxL.hack")
    parser.parse()