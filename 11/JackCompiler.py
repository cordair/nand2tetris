import os, re, sys, glob

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
    def __init__(self, vm_file, tokenizer):
        self.file = vm_file
        self.vm_writer = VMWriter(vm_file)
        self.tokenizer = tokenizer
        self.current_line = None
        self.current_token = None
        self.current_token_type = None
        self.current_class = None
        self.current_function = None
        self.current_function_type = None
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
        self.current_class = self.eat(self.class_names)
        self.eat("{")
        self.handleClassVarDec()
        self.handleSubroutineDec()
        self.eat("}")
 
    def handleClassVarDec(self):
        self.class_st.startSubroutine()
        while (self.current_token in self.class_var_dec):
            kind = self.eat(self.var_dec)
            type = self.eat(self.type)
            name = self.eatType("identifier")
            self.class_st.define(kind, type, name)
            while(self.eat(",") != None):
                name = self.eatType("identifier")
                self.class_st.define(kind, type, name)
            self.eat(";")
            
    def handleSubroutineDec(self):
        while(self.current_token in self.subroutine):
            self.subroutine_st.startSubroutine()
            self.current_function_type = self.eat(self.subroutine)
            self.eat(self.subroutine_dec)
            self.current_function = self.eatType("identifier")
            self.eat("(")
            self.handleParameterList()
            self.eat(")")
            self.eat("{")
            self.handleSubroutineBody()
            self.eat("}")

    def handleParameterList(self):
        if (self.current_token in self.type):
            if (self.current_function_type == "method"):
                self.subroutine_st.define("argument", "null", "null")
            kind = "argument"
            type = self.eat(self.type)
            name = self.eatType("identifier")
            self.subroutine_st.define(kind, type, name)
            while (self.eat(",") != None):
                type = self.eat(self.type)
                name = self.eatType("identifier")
                self.subroutine_st.define(kind, type, name)

    def handleVarDec(self):
        while(self.current_token == "var"):
            self.eatType("keyword")
            kind = "local"
            type = self.eat(self.type)
            name = self.eatType("identifier")
            self.subroutine_st.define(kind, type, name)
            while (self.eat(",") != None):
                name = self.eatType("identifier")
                self.subroutine_st.define(kind, type, name)
            self.eat(";")

    def handleSubroutineBody(self):
        self.handleVarDec()
        self.vm_writer.resetLabel()
        var_count = self.subroutine_st.getVarCount()
        subroutine_name = self.current_class + "." + self.current_function
        self.vm_writer.writeFunction(subroutine_name, var_count)
        if (self.current_function_type == "constructor"):
            field_count = self.class_st.getFieldCount()
            self.vm_writer.writePush("constant", field_count)
            self.vm_writer.writeCall("Memory.alloc", 1)
            self.vm_writer.writePop("pointer", 0)
        elif(self.current_function_type == "method"):
            self.vm_writer.writePush("argument", 0)
            self.vm_writer.writePop("pointer", 0)
        self.compileStatements()

    def compileStatements(self):
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

    def handleIf(self):
        if_true     = self.vm_writer.getLabel0("IF_TRUE")
        if_false    = self.vm_writer.getLabel1("IF_FALSE")

        self.eat("if")
        self.eat("(")
        self.handleExpression()
        self.vm_writer.writeOperator("not")
        self.vm_writer.writeIfGoto(if_false)
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.vm_writer.writeGoto(if_true)
        self.eat("}")
        self.vm_writer.writeLabel(if_false)
        
        while (self.eat("else")):
            self.eat("{")
            self.compileStatements()
            self.eat("}")
        self.vm_writer.writeLabel(if_true)

    def handleWhile(self):
        while_expression    = self.vm_writer.getLabel0("WHILE_EXP")
        while_end           = self.vm_writer.getLabel1("WHILE_END")

        self.eat("while")
        self.eat("(")
        self.vm_writer.writeLabel(while_expression)
        self.handleExpression()
        self.vm_writer.writeOperator("not")
        self.vm_writer.writeIfGoto(while_end)
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.vm_writer.writeGoto(while_expression)
        self.vm_writer.writeLabel(while_end)
        self.eat("}")

    def handleLet(self):
        self.eat('let')
        name = self.eatType("identifier")
        kind = self.stFindKind(name)
        index = self.stFindIndex(name)
        if (kind == "field"):
            kind = "this"
        if (self.current_token == "["):
            self.eat('[')
            self.vm_writer.writePush(kind, index)
            self.handleExpression()
            self.vm_writer.writeOperator("add")
            self.eat(']')
            self.eat('=')
            self.handleExpression()
            self.vm_writer.writePop("temp", 0)
            self.vm_writer.writePop("pointer", 1)
            self.vm_writer.writePush("temp", 0)
            self.vm_writer.writePop("that", 0)
            self.eat(';')
        else:
            self.eat('=')
            self.handleExpression()
            self.vm_writer.writePop(kind, index)
            self.eat(';')

    def handleDo(self):
        self.eat("do")
        self.handleExpression()
        self.vm_writer.writePop("temp", 0)
        self.eat(";")

    def handleReturn(self):
        self.eat("return")
        if (self.current_token != ";"):
            self.handleExpression()
        else:
            self.vm_writer.writePush("constant", 0)
        self.vm_writer.writeReturn()
        self.eat(";")

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
            self.handleTerm()
            if (operator == "*"):
                self.vm_writer.writeCall("Math.multiply", 2)
            elif (operator == "/"):
                self.vm_writer.writeCall("Math.divide", 2)
            else:
                operator = self.convertOperator(operator)
                self.vm_writer.writeOperator(operator)
            operator = self.current_token
        
    def handleTerm(self):
        if (self.current_token in self.unaryOp):
            operator = self.convertUnaryOperator(self.current_token) 
            self.eat(self.unaryOp)
            self.handleTerm()
            self.vm_writer.writeOperator(operator)
        elif (self.current_token == "("):
            self.eat("(")
            self.handleExpression()
            self.eat(")")
        elif (self.current_token_type == "integerConstant"):
            self.vm_writer.writePush("constant", self.current_token)
            self.eatType("integerConstant")
        elif (self.current_token_type == "stringConstant"):
            self.handleTermString()
        elif (self.current_token in self.keyword_constant):
            if (self.current_token == "this"):
                self.vm_writer.writePush("pointer", 0)
            elif (self.current_token == "true"):
                self.vm_writer.writePush("constant", 1)
                self.vm_writer.writeOperator("neg")
            elif (self.current_token == "false"):
                self.vm_writer.writePush("constant", 0)
            elif (self.current_token == "null"):
                self.vm_writer.writePush("constant", 0)
            self.eatType("keyword")
        elif (self.current_token_type == "identifier"):
            name = self.eatType("identifier")

            if (self.current_token == "["):
                kind = self.stFindKind(name)
                index = self.stFindIndex(name)
                if (kind == "field"):
                    kind = "this"
                self.vm_writer.writePush(kind, index)
                self.eat("[")
                self.handleExpression()
                self.eat("]")
                self.vm_writer.writeOperator("add")
                self.vm_writer.writePop("pointer", 1)
                self.vm_writer.writePush("that", 0)
                
            elif (self.current_token == "("):
                self.handleTermSameClassCall(name)
            elif (self.current_token == "."):
                self.handleTermDiffClassCall(name)
            else:
                kind = self.stFindKind(name)
                index = self.stFindIndex(name)
                if (kind == "field"):
                    kind = "this"
                self.vm_writer.writePush(kind, index)

    def handleTermString(self):
        string_name = self.current_token
        self.vm_writer.writePush("constant", len(string_name))
        self.vm_writer.writeCall("String.new", 1)
        for i in range(len(string_name)):
            self.vm_writer.writePush("constant", ord(string_name[i]))
            self.vm_writer.writeCall("String.appendChar", 2)
        self.eatType("stringConstant")

    def handleTermSameClassCall(self, name):
        self.eat("(")
        self.vm_writer.writePush("pointer", 0)
        name = (self.current_class + "." + name)
        number_of_expression = self.compileExpressionList() + 1
        self.vm_writer.writeCall(name, number_of_expression)
        self.eat(")")

    def handleTermDiffClassCall(self, name):
        self.eat(".")
        kind = self.stFindKind(name)
        type = self.stFindType(name)
        index = self.stFindIndex(name)
        number_of_expression = 0
        if (kind != None):
            if (kind == "field"):
                kind = "this"
            self.vm_writer.writePush(kind, index)
            number_of_expression = 1
            name = type
        name += "."
        name += self.eatType("identifier")
        self.eat("(")
        number_of_expression += self.compileExpressionList()
        self.vm_writer.writeCall(name, number_of_expression)
        self.eat(")")

    def eat(self, token_to_eat):
        if (self.current_token in token_to_eat):
            token = self.current_token
            self.getNextLine()
            return token
        return None
    
    def eatType(self, type):
        if (self.current_token_type == type):
            token = self.current_token
            self.getNextLine()
            return token
        else:
            print("ERROR! Eat type error!", end='')
            print("\t line: " + self.current_line + "\t type_to_eat: " + type)
        return None

    def eatOperator(self, token_to_eat):
        if (self.current_token in token_to_eat):
            token = self.current_token
            self.getNextLine()
            return token
        return None

    def getNextLine(self):
        line = self.tokenizer.advance()
        self.current_line = line

        if (line != "<tokens>" and line != "</tokens>"):
            left_index = 0
            right_index = len(line) - 1
            while (left_index < len(line)):
                if (line[left_index] == " "):
                    break
                left_index += 1
            self.current_token_type = line[1:left_index-1]
            while (line[right_index] != " "):
                right_index -= 1
            self.current_token = line[left_index+1:right_index]

    def write(self, line):
        self.file.write(self.tabs)
        self.file.write(line + END_LINE)

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

    def convertUnaryOperator(self, operator):
        if (operator == "-"):
            return "neg"
        elif (operator == "~"):
            return "not"

    def stFindKind(self, name):
        segment = self.subroutine_st.kindOf(name)
        if (segment == None):
            segment = self.class_st.kindOf(name)
        return segment

    def stFindType(self, name):
        type = self.subroutine_st.typeOf(name)
        if (type == None):
            type = self.class_st.typeOf(name)
        return type

    def stFindIndex(self, name):
        kind = self.subroutine_st.indexOf(name)
        if (kind == None):
            kind = self.class_st.indexOf(name)
        return kind

class VMWriter:
    def __init__(self, file):
        self.file = file
        self.label0_number = -1
        self.label1_number = -1

    def getLabel0(self, label_name):
        self.label0_number += 1
        number = self.label0_number
        return "{name}{number}".format(name=label_name, number=number)
    
    def getLabel1(self, label_name):
        self.label1_number += 1
        number = self.label1_number
        return "{name}{number}".format(name=label_name, number=number)

    def resetLabel(self):
        self.label0_number = -1
        self.label1_number = -1

    def writeOperator(self, operator):
        self.write(operator)

    def writePush(self, segment, index):
        if (segment == None):
            print("PUSH ERROR! segment is None")
        self.write("push {segment} {index}".format(segment=segment, index=index))

    def writePop(self, segment, index):
        if (segment == None):
            print("POP ERROR! segment is None")
        self.write("pop {segment} {index}".format(segment=segment, index=index))

    def writeArithmetic(self, command):
        self.write(command)

    def writeCall(self, name, number_of_argument):
        self.write("call {name} {number}".format(name=name, number=number_of_argument))

    def writeFunction(self, name, number_of_local):
        self.write("function {name} {number}".format(name=name, number=number_of_local))

    def writeReturn(self):
        self.write("return")

    def writeGoto(self, label):
        self.write("goto " + label)

    def writeIfGoto(self, label):
        self.write("if-goto " + label)

    def write(self, line):
        self.file.write(line)
        self.file.write(END_LINE)
 
    def writeLabel(self, label):
        self.file.write("label {L}".format(L=label))
        self.file.write(END_LINE)

class SymbolTable:
    def __init__(self):
        self.st = None
        self.kind_count = None
        self.field_count = None
        self.var_count = None

    def startSubroutine(self):
        self.st = {}
        self.kind_count = {}
        self.field_count = 0
        self.var_count = 0

    def define(self, kind, type, name):
        index = self.kind_count.get(kind, -1) + 1
        if (kind == "field"):
            self.field_count += 1
        elif (kind == "local"):
            self.var_count += 1
        self.kind_count[kind] = index
        self.st[name] = [kind, type, index]

    def kindOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[0]
        return None

    def typeOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[1]
        return None

    def indexOf(self, name):
        values = self.st.get(name)
        if (values != None):
            return values[2]
        return None
    
    def getFieldCount(self):
        return self.field_count

    def getVarCount(self):
        return self.var_count

    def print(self):
        for key, value in self.st.items():
            print("key: ", key, "   value:", value)

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
            class_name = file_name.split("\\")[-1]
            ALL_CLASSES.append(class_name)
        
        for jack_filename in glob.glob(directory + "/*.jack"):
            vm_filename = jack_filename.split('.')[0] + ".vm"
            with open(vm_filename, "w") as vm_file:
                tokenizer = Tokenizer(jack_filename)
                tokenizer.parse()

                compilationEngine = CompilationEngine(vm_file, tokenizer)
                compilationEngine.compile()
                vm_file.close()

    def translateFile(self, file_name):
        prefix_filename = file_name.split('.')[0]
        jack_filename = prefix_filename + ".jack"
        vm_filename =  prefix_filename + ".vm"
        ALL_CLASSES.append(prefix_filename)

        with open(vm_filename, "w") as vm_file:
            tokenizer = Tokenizer(jack_filename)
            tokenizer.parse()
            compilationEngine = CompilationEngine(vm_file, tokenizer)
            compilationEngine.compile()
            vm_file.close()

if __name__ == '__main__':
    Main(sys.argv[1:])