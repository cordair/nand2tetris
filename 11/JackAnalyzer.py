import os, re, sys, glob

# TODO handling objects, handling arrays

END_LINE = "\n"

keyword = ["class", "constructor", "function", "method", "field", "static", "var",          
            "int", "char", "boolean", "void", "true", "false", "null", "this", "let",          
            "do", "if", "else", "while", "return", ]

symbol = {"{", "}", "(", ")", "[", "]", ",", ".", ";", "+", "-", "*", 
          "/", "&", "|", "<", ">", "=", "~", }

KEYWORD_TOKEN           = 0
SYMBOL_TOKEN            = 1
START_STRING_TOKEN      = 2
END_STRING_TOKEN        = 3
INTEGER_TOKEN           = 4
IDENTIFIER_TOKEN        = 5
NESTED_WORD             = 6

ALL_CLASSES = []

kind = ["static", "field", "arg", "var"]

SEGMENT = ["const", "arg", "local", "static", "this", "that", "pointer", "temp"]
COMMAND = ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not", 
            "call Math.multiply 2", "call Math.divide 2"]

class Tokenizer:
    def __init__(self, jack_filename):
        self.read_filename = jack_filename
        
        self.tokens = []
        self.token_index = 0
        self.number_of_token = 0
        
        self.current_string = None
        self.in_string_flag = False
        self.in_comment_flag = False
        
    def parse(self):
        with open(self.read_filename) as read_file:
            self.writeInitialize()

            for line in read_file.readlines():
                # empty line
                if (self.isInvalidLine(line)):
                    continue
                words = line.split()
                for word in words:
                    if (self.isNestedComment(word)):
                        break
                    self.parseWord(word)
            self.writeEnd()
            self.number_of_token = len(self.tokens)
            read_file.close()

    def advance(self):
        if (self.token_index == self.number_of_token):
            return None
        token = self.tokens[self.token_index]
        self.token_index += 1
        return token

    def parseWord(self, word):
        if (self.in_string_flag):
            token_type = self.classifyToken(word)
            self.handleString(word, token_type)
        else:
            token_type = self.classifyToken(word)
            self.processToken(token_type, word)

    def classifyToken(self, word):
        if (self.in_string_flag):
            if ("\"" in word):
                self.in_string_flag = False
                return END_STRING_TOKEN
            return -1

        if (word in keyword):
            return KEYWORD_TOKEN
        elif (word in symbol):
            return SYMBOL_TOKEN
        elif (self.representInt(word)):
            wordInt = int(word)
            if ((wordInt >= 0) and (wordInt <= 32767)):
                return INTEGER_TOKEN
        elif (word[0] == "\"" and len(word) > 1):
            self.in_string_flag = True
            return START_STRING_TOKEN
        elif (self.isIdentifier(word)):
            return IDENTIFIER_TOKEN
        return NESTED_WORD

    def handleString(self, token, token_type):
        # "HOW MANY NUMBERS? ";
        # Keyboard.readInt("HOW MANY NUMBERS? ");
        if (token_type == END_STRING_TOKEN):
            if (token[-1] != "\""):
                i = 0
                j = 0
                while (i < len(token)):
                    token_type = self.classifyToken(token[i])
                    if (token[i] == "\""):
                        self.writeEndString(token[j:i])
                    if (token_type == SYMBOL_TOKEN):
                        self.processToken(token_type, token[i])
                    i += 1
            else:
                token = token.strip("\"")
                self.writeEndString(token)
            
        else:
            self.writeString(token)

    def processToken(self, token_type, word):
        if (token_type == KEYWORD_TOKEN):
            self.writeKeyword(word)
        elif (token_type == SYMBOL_TOKEN):
            self.writeSymbol(word)
        elif (token_type == INTEGER_TOKEN):
            self.writeInt(word)
        elif (token_type == START_STRING_TOKEN):
            word = word.strip("\"")
            self.writeStartString(word)
        elif (token_type == IDENTIFIER_TOKEN):
            self.writeIdentifier(word)
        elif (token_type == NESTED_WORD):
            self.handleNestedWord(word)

    def handleNestedWord(self, word):
        # (( "test machine" ));
        # screen.draw()
        # Keyboard.readInt("HOW MANY NUMBERS? ");
        i = 0
        j = 0
        write_stripped_word = False
        stripped_word = None

        while (i < len(word)):
            token_type = self.classifyToken(word[i])
            if (token_type == SYMBOL_TOKEN):
                if (write_stripped_word):
                    self.parseWord(stripped_word)
                    write_stripped_word = False
                self.processToken(token_type, word[i])
                j = i + 1
            else:
                stripped_word = word[j:i+1]
                write_stripped_word = True
            i += 1

        if (write_stripped_word):
            self.parseWord(stripped_word)

    def writeInitialize(self):
        self.tokens.append("<tokens>")

    def writeEnd(self):
        self.tokens.append("</tokens>")

    def writeKeyword(self, value):
        self.tokens.append("<keyword> {value} </keyword>".format(value=value))

    def writeSymbol(self, value):
        if (value == ">"):
            value = "&gt;"
        elif (value == "<"):
            value = "&lt;"
        elif (value == "&"):
            value = "&amp;"
        self.tokens.append("<symbol> {value} </symbol>".format(value=value))

    def writeIdentifier(self, value):
        self.tokens.append("<identifier> {value} </identifier>".format(value=value))
    
    def writeInt(self, value):
        self.tokens.append("<integerConstant> {value} </integerConstant>".format(value=value))

    def writeStartString(self, value):
        self.current_string = "<stringConstant> {value}".format(value=value)

    def writeString(self, value):
        self.current_string += " {value}".format(value=value)

    def writeEndString(self, value):
        self.current_string += " {value} </stringConstant>".format(value=value)
        self.tokens.append(self.current_string)

    def representInt(self, s):
        try: 
            int(s)
            return True
        except ValueError:
            return False

    def isIdentifier(self, word):
        for character in word:
            if (not (   (character >= 'a' and character <= 'z')
                    or  (character >= 'A' and character <= 'Z')
                    or  (character == '_'))):
                return False
        return True

    def isInvalidLine(self, line):
        # empty line
        if (not line.strip()):
            return True
        words = line.split()
        word = words[0]
        if (word[0] == "/" and word[1] == "/"):
            return True
        elif (word == "/**"):
            if (not("*/" in words)):
                self.in_comment_flag = True
            return True
        elif (word == "*" and self.in_comment_flag):
            return True
        elif (word == "*/"):
            self.in_comment_flag = False
            return True

    def isNestedComment(self, word):
        if (word == "//" ):
            return True
        return False

class CompilationEngine:
    def __init__(self, xml_file, tokenizer):
        self.vm_writer = VMWriter(xml_file)
        self.tokenizer = tokenizer
        self.current_line = None
        self.current_token = None
        self.current_token_type = None
        self.tabs = ""

        self.class_st = SymbolTable()
        self.subroutine_st = SymbolTable()

        self.class_names = ALL_CLASSES
        self.subroutine_names = []
        self.var_names = []

        self.class_var_dec = ["static", "field"]
        self.type = ["int", "char", "boolean", "String", "Array"]
        self.var_dec = ["static", "field"]
        self.subroutine = ["constructor", "function", "method"]
        self.subroutine_dec = ["void"]
        self.keyword_constant = ["this", "true", "false", "null"]
        self.statements = ["let", "if", "do", "while", "return"]
        self.expressions = ["integerConstant", "stringConstant", "keywordConstant", "expression", 
                            "identifier", "unaryOpTerm", "array", "sameClassCall", "diffClassCall"]
        self.op = ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="]
        self.unaryOp = ["-", "~"]
        self.type.extend(self.class_names)
        self.var_dec.extend(self.class_names)
        self.subroutine_dec.extend(self.type)
        self.subroutine_dec.extend(self.class_names)


    def compile(self):
        self.getNextLine()
        self.verifyOpeningToken()
        self.getNextLine()
        self.compileClass()
        self.verifyEndingToken()

    def compileClass(self):
        self.eat("class")
        self.eat(self.class_names)
        self.eat("{")
        self.class_st.startSubroutine()
        self.handleClassVarDec()
        self.subroutine_st.startSubroutine()
        self.handleSubroutineDec()
        self.eat("}")

    def handleClassVarDec(self):
        while (self.current_token in self.class_var_dec):
            kind = self.eat(self.var_dec)
            type = self.eat(self.type)
            name = self.eatType("identifier")
            self.class_st.define(name, type, kind)
            while(self.eat(",") != None):
                name = self.eatType("identifier")
                self.class_st.define(name, type, kind)
            self.eat(";")
            
    def handleSubroutineDec(self):
        while(self.current_token in self.subroutine):
            self.eat(self.subroutine)
            self.eat(self.subroutine_dec)
            self.eatType("identifier")
            self.eat("(")
            self.handleParameterList()
            self.eat(")")
            self.handleSubroutineBody()

    def handleParameterList(self):
        if (self.current_token in self.type):
            type = self.eat(self.type)
            name = self.eatType("identifier")
            kind = "argument"
            self.subroutine_st.define(name, type, kind)
            while (self.eat(",") != None):
                type = self.eat(self.type)
                name = self.eatType("identifier")
                self.subroutine_st.define(name, type, kind)

    def handleSubroutineBody(self):
        self.eat("{")
        self.handleVarDec()
        self.compileStatements()
        self.eat("}")

    def handleVarDec(self):
        while(self.current_token == "var"):
            self.eatType("keyword")
            type = self.eat(self.type)
            name = self.eatType("identifier")
            kind = "local"
            self.subroutine_st.define(name, type, kind)
            while (self.eat(",") != None):
                name = self.eatType("identifier")
                self.subroutine_st.define(name, type, kind)

    def compileStatements(self):
        prev_tabs = self.tabs
        self.write("<statements>")
        self.tabs += "  "
        while(self.current_token in self.statements):
            if (self.current_token == "let"):
                self.handleLet()
            elif (self.current_token == "if"):
                self.handleIf()
            elif (self.current_token == "do"):
                self.handleDo()
            elif (self.current_token == "while"):
                self.handleWhile()
            elif (self.current_token == "return"):
                self.handleReturn()
        self.tabs = prev_tabs
        self.write("</statements>")

    def handleIf(self):
        label0 = self.vm_writer.getLabel()
        label1 = self.vm_writer.getLabel()

        self.eat("if")
        self.eat("(")
        self.handleExpression()
        self.vm_writer.writeOperator("not")
        self.vm_writer.writeIf(label0)
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.vm_writer.writeGoto(label1)
        self.eat("}")
        self.vm_writer.writeLabel(label0)
        
        while (self.eat("else") != None):
            self.eat("{")
            self.compileStatements()
            self.vm_writer.writeLabel(label1)
            self.eat("}")

    def handleWhile(self):
        label0 = self.vm_writer.getLabel()
        label1 = self.vm_writer.getLabel()

        self.eat("while")
        self.eat("(")
        self.vm_writer.writeLabel(label0)
        self.handleExpression()
        self.vm_writer.writeOperator("not")
        self.vm_writer.writeIf(label1)
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.vm_writer.writeGoto(label0)
        self.eat("}")
        self.writeLabel(label1)
        
    def handleLet(self):
        self.write("<letStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat('let')
        kind = self.findKind(self.current_token)
        type = self.findIndex(self.current_token)
        self.eatType("identifier")
        if (self.eat('[')):
            self.handleExpression()
            self.eat(']')
        self.eat('=')
        self.handleExpression()
        self.eat(';')
        self.vm_writer.writePop(kind, type)
        self.tabs = prev_tabs
        self.write("</letStatement>")

    def handleDo(self):
        self.write("<doStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat("do")
        self.eatType("identifier")

        if (self.current_token == "."):
            self.eat(".")
            self.eatType("identifier")
        
        self.eat("(")
        self.compileExpressionList()
        self.eat(")")
        self.eat(";")

        self.tabs = prev_tabs
        self.write("</doStatement>")

    def handleReturn(self):
        self.write("<returnStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat("return")
        if (self.current_token != ";"):
            self.handleExpression()
        self.eat(";")

        self.tabs = prev_tabs
        self.write("</returnStatement>")

    def compileExpressionList(self):
        number_of_expression = 0
        if (self.current_token != ")"):
            self.handleExpression()
            number_of_expression += 1
            while (self.eat(",") != None):
                self.handleExpression()
                number_of_expression += 1
        return number_of_expression
        
    def handleExpression(self):
        self.handleTerm()
        operator = self.current_token
        while (self.eatOperator(self.op) != None):
            operator = self.convertOperator(operator)
            self.handleTerm()
            self.vm_writer.writeOperator(operator)
            operator = self.current_token
        
    def handleTerm(self):
        if (self.current_token_type == "integerConstant"):
            self.vm_writer.writePush("constant", self.current_token)
            self.eatType("integerConstant")
        elif (self.current_token_type == "stringConstant"):
            self.eatType("stringConstant")
        elif (self.current_token_type == "identifier"):
            identifier_name = self.current_token
            self.eatType("identifier")
            if (self.current_token == "["):
                self.eat("[")
                self.handleExpression()
                self.eat("]")
            elif (self.current_token == "("):
                self.eat("(")
                number_of_expression = self.compileExpressionList()
                self.vm_writer.writeFunction(identifier_name, number_of_expression)
                self.eat(")")
            elif (self.current_token == "."):
                self.eat(".")
                self.eatType("identifier")
                self.eat("(")
                number_of_expression = self.compileExpressionList()
                self.vm_writer.writeCall(identifier_name, number_of_expression)
                self.eat(")")
            else:
                segment = self.findKind(identifier_name)
                index = self.findIndex(identifier_name)
                self.vm_writer.writePush(segment, index)
        else:
            if (self.current_token in self.keyword_constant):
                self.eatType("keyword")
            elif (self.current_token in self.unaryOp):
                operator = self.convertUnaryOperator(self.current_token) 
                self.eat(self.unaryOp)
                self.handleTerm()
                self.vm_writer.writeOperator(operator)
            elif (self.current_token == "("):
                self.eat("(")
                self.handleExpression()
                self.eat(")")

    def eat(self, token_to_eat):
        line = None
        if (self.current_token in token_to_eat):
            self.getNextLine()
        return line
    
    def eatType(self, type):
        line = None
        if (self.current_token_type == type):
            self.getNextLine()
        else:
            print("ERROR! Eat type error!", end='')
            print("\t line: " + self.current_line + "\t type_to_eat: " + type)
        return line

    def eatOperator(self, token_to_eat):
        line = None
        if (self.current_token in token_to_eat):
            self.getNextLine()
        return line

    def getNextLine(self):
        line = self.tokenizer.advance()
        self.current_line = line

        if (line != "<tokens>" and line != "</tokens>"):
            token_type = line.split(" ")[0]
            self.current_token = line.split(" ")[1:-1]
            self.current_token_type = token_type[1:-1]

    def findKind(self, name):
        segment = self.subroutine_st.kindOf(name)
        if (segment == None):
            segment = self.class_st.kindOf(name)

    def findType(self, name):
        segment = self.subroutine_st.typeOf(name)
        if (segment == None):
            segment = self.class_st.typeOf(name)

    def findIndex(self, name):
        segment = self.subroutine_st.indexOf(name)
        if (segment == None):
            segment = self.class_st.indexOf(name)

    def convertOperator(self, operator):
        if (operator == "&lt;"):
            return "lt"
        elif (operator == "&gt;"):
            return "gt"
        elif (operator == "="):
            return "eq"
        elif (operator == "&amp;"):
            return "and"
        elif (operator == "|"):
            return "or"
        elif (operator == "+"):
            return "add"
        elif (operator == "-"):
            return "sub"
        elif (operator == "*"):
            return "call Math.multiply 2"
        elif (operator == "/"):
            return "call Math.divide 2"

    def convertUnaryOperator(self, operator):
        if (operator == "-"):
            return "neg"
        elif (operator == "~"):
            return "not"

    def write(self, line):
        self.file.write(line)
        self.file.write(END_LINE)

    def close(self):
        self.file.close()

    def verifyOpeningToken(self):
        if (self.current_line != "<tokens>"):
            print(self.current_line)
            print("ERROR! MISSING OPENING TOKEN")

    def verifyEndingToken(self):
        if (self.current_line != "</tokens>"):
            print(self.current_line)
            print("ERROR! MISSING ENDING TOKEN")

class VMWriter:
    def __init__(self, file):
        self.file = file
        self.label_number = 0

    def write(self, line):
        self.file.write("  " + line)
        self.file.write(END_LINE)

    def writeOperator(self, operator):
        if (operator in COMMAND):
            self.write(operator)
        else:
            print("WRITE OPERATOR ERROR!")

    def writePush(self, segment, index):
        if (segment in SEGMENT):
            self.write("push {segment} {index}".format(segment=segment, index=index))
        else:
            print("WRITE PUSH ERROR!")

    def writePushString(self, string_segments):
        print("WRITE PUSH STRING ERROR!")

    def writePop(self, segment, index):
        if (segment in SEGMENT):
            return "pop {segment} {index}".format(segment=segment, index=index)
        print("WRITE POP ERROR!")

    def writeArithmetic(self, command):
        if (command in COMMAND):
            self.write(command)
        print("WRITE ARITHMETIC ERROR!")
 
    def writeLabel(self, label):
        self.file.write(label)
        self.file.write(END_LINE)

    def getLabel(self):
        number = self.label_number
        self.label_number += 1
        return "L" + number

    def writeGoto(self, label):
        self.write("goto " + label)

    def writeIf(self, label):
        self.write("if-goto " + label)

    def writeCall(self, name, number_of_argument):
        self.write("call {name} {number}".format(name=name, number=number_of_argument))

    def writeFunction(self, name, number_of_local):
        self.write("call {name} {number}".format(name=name, number=number_of_local))

    def writeReturn(self):
        return

    def close(self):
        return

class SymbolTable:
    def __init__(self):
        self.st = None
        self.kind_count = None

    def startSubroutine(self):
        self.st = {}
        self.kind_count = {}

    def define(self, name, type, kind):
        index = self.varCount(kind) + 1
        self.kind_count[kind] = index
        self.st[name] = [type, kind, index]
    
    def varCount(self, kind):
        return self.kind_count.get(kind, -1)

    def typeOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[0]
        return None

    def kindOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[1]
        return None

    def indexOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[2]
        return None

class Main:
    def __init__(self, argv):
        if len(argv) != 0 and os.path.isdir(argv[0]):
            # Square
            self.translateDirectory(argv[0])
        elif len(argv) != 0 and os.path.splitext(argv[0])[1] == ".jack":
            # Square\Main.jack
            # Main.jack
            self.translateFile(argv[0])
        else:
            print("Command: python JackAnalyzer.py <directory name>.jack")
            sys.exit(1)

    def translateDirectory(self, directory):
        for jack_filename in glob.glob(directory + "/*.jack"):
            file_name = jack_filename.split('.')[0]
            class_name = file_name.split("\\")[1]
            ALL_CLASSES.append(class_name)
        
        for jack_filename in glob.glob(directory + "/*.jack"):
            xml_filename = jack_filename.split('.')[0] + ".xml"
            with open(xml_filename, "w") as xml_file:
                tokenizer = Tokenizer(jack_filename)
                tokenizer.parse()

                compilationEngine = CompilationEngine(xml_file, tokenizer)
                compilationEngine.compile()
                xml_file.close()

    def translateFile(self, file_name):
        prefix_filename = file_name.split('.')[0]
        jack_filename = prefix_filename + ".jack"
        xml_filename =  prefix_filename + ".xml"
        class_name = prefix_filename.split("\\")[1]
        ALL_CLASSES.append(class_name)

        with open(xml_filename, "w") as xml_file:
            tokenizer = Tokenizer(jack_filename)
            tokenizer.parse()
            compilationEngine = CompilationEngine(xml_file, tokenizer)
            compilationEngine.compile()
            xml_file.close()

if __name__ == '__main__':
    Main(sys.argv[1:])