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
    def __init__(self, xml_file, tokenizer):
        self.file = xml_file
        self.tokenizer = tokenizer
        self.current_line = None
        self.current_token = None
        self.current_token_type = None
        self.tabs = ""

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
        self.op = ["+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "=", "\""]
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
        self.write("<class>")
        prev_tabs = self.tabs
        self.tabs += "  "
        
        self.eat("class")
        self.eat(self.class_names)
        self.eat("{")
        self.handleClassVarDec()
        self.handleSubroutineDec()
        self.eat("}")
        
        self.tabs = prev_tabs
        self.write("</class>")

 
    def handleClassVarDec(self):
        while (True):
            if (self.current_token in self.class_var_dec):
                self.write("<classVarDec>")
                prev_tabs = self.tabs
                self.tabs += "  "
            
                self.eat(self.var_dec)
                self.eat(self.type)
                self.eatType("identifier")
                while(self.eat([","])):
                    self.eatType("identifier")
                self.eat([";"])

                self.tabs = prev_tabs
                self.write("</classVarDec>")
            else:
                break
            
    def handleSubroutineDec(self):
        while(True):
            if (self.current_token in self.subroutine):
                self.write("<subroutineDec>")
                prev_tabs = self.tabs
                self.tabs += "  "

                self.eat(self.subroutine)
                self.eat(self.subroutine_dec)
                self.eatType("identifier")
                self.eat("(")
                self.handleParameterList()
                self.eat(")")
                self.handleSubroutineBody()

                self.tabs = prev_tabs
                self.write("</subroutineDec>")
            else:
                break

    def handleParameterList(self):
        prev_tabs = self.tabs
        self.write("<parameterList>")
        self.tabs += "  "
        if (self.current_token in self.type):
            self.eat(self.type)
            self.eatType("identifier")
            while (self.eat(",")):
                self.eat(self.type)
                self.eatType("identifier")
        self.tabs = prev_tabs
        self.write("</parameterList>")

    def handleSubroutineBody(self):
        self.write("<subroutineBody>")
        prev_tabs = self.tabs
        self.tabs += "  "
        self.eat("{")
        self.handleVarDec()
        self.compileStatements()
        self.eat("}")
        self.tabs = prev_tabs
        self.write("</subroutineBody>")

    def handleVarDec(self):
        while(True):
            if (self.current_token == "var"):
                self.write("<varDec>")
                prev_tabs = self.tabs
                self.tabs += "  "

                self.eatType("keyword")
                self.eat(self.type)
                self.eatType("identifier")
                while (self.eat(",")):
                    self.eatType("identifier")
                self.eat(";")
                self.tabs = prev_tabs
                self.write("</varDec>")
            else:
                break

    def compileStatements(self):
        prev_tabs = self.tabs
        self.write("<statements>")
        self.tabs += "  "
        while(True):
            if (self.current_token in self.statements):
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
            else:
                break
        self.tabs = prev_tabs
        self.write("</statements>")

    def handleLet(self):
        self.write("<letStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat('let')
        self.eatType("identifier")
        if (self.eat('[')):
            self.handleExpression()
            self.eat(']')
        self.eat('=')
        self.handleExpression()
        self.eat(';')

        self.tabs = prev_tabs
        self.write("</letStatement>")

    def handleIf(self):
        self.write("<ifStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat("if")
        self.eat("(")
        self.handleExpression()
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.eat("}")
        
        while (self.eat("else")):
            self.eat("{")
            self.compileStatements()
            self.eat("}")

        self.tabs = prev_tabs
        self.write("</ifStatement>")

    def handleWhile(self):
        self.write("<whileStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat("while")
        self.eat("(")
        self.handleExpression()
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.eat("}")
        
        self.tabs = prev_tabs
        self.write("</whileStatement>")

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
        self.write("<expressionList>")
        prev_tabs = self.tabs
        self.tabs += "  "

        if (self.current_token != ")"):
            self.handleExpression()
            while (self.eat(",")):
                self.handleExpression()
        self.tabs = prev_tabs
        self.write("</expressionList>")
        
    def handleExpression(self):
        self.write("<expression>")
        prev_tabs = self.tabs
        self.tabs += "  "
    
        self.handleTerm()
        while (self.eatOperator(self.op)):
            self.handleTerm()

        self.tabs = prev_tabs
        self.write("</expression>")
        
    def handleTerm(self):
        self.write("<term>")
        prev_tabs = self.tabs
        self.tabs += "  "

        if (self.current_token_type == "integerConstant"):
            self.eatType("integerConstant")
        elif (self.current_token_type == "stringConstant"):
            self.eatType("stringConstant")
        elif (self.current_token_type == "identifier"):
            self.eatType("identifier")
            if (self.current_token == "["):
                self.eat("[")
                self.handleExpression()
                self.eat("]")
            elif (self.current_token == "("):
                self.eat("(")
                self.compileExpressionList()
                self.eat(")")
            elif (self.current_token == "."):
                self.eat(".")
                self.eatType("identifier")
                self.eat("(")
                self.compileExpressionList()
                self.eat(")")
        else:
            if (self.current_token in self.keyword_constant):
                self.eatType("keyword")
            elif (self.current_token in self.unaryOp):
                self.eat(self.unaryOp)
                self.handleTerm()
            elif (self.current_token == "("):
                self.eat("(")
                self.handleExpression()
                self.eat(")")
        self.tabs = prev_tabs
        self.write("</term>")

    def eat(self, token_to_eat):
        if (self.current_token in token_to_eat):
            self.write(self.current_line)
            self.getNextLine()
            return True
        return False
    
    def eatType(self, type):
        if (self.current_token_type == type):
            self.write(self.current_line)
            self.getNextLine()
        else:
            print("ERROR! Eat type error!", end='')
            print("\t line: " + self.current_line + "\t type_to_eat: " + type)
        

    def eatOperator(self, token_to_eat):
        if (self.current_token in token_to_eat):
            if (self.current_token == "\""):
                self.write("<symbol> &quot; </symbol>")
            else:
                self.write(self.current_line)
            self.getNextLine()
            return True
        return False

    def getNextLine(self):
        line = self.tokenizer.advance()
        self.current_line = line

        if (line != "<tokens>" and line != "</tokens>"):
            token_type = line.split(" ")[0]
            self.current_token = line.split(" ")[1]
            self.current_token_type = token_type[1:-1]

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