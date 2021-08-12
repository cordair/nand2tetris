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
    def __init__(self, xmlT_file, jack_filename):
        self.file = xmlT_file
        self.read_filename = jack_filename
        self.in_string_flag = False
        self.in_comment_flag = False
        self.debug = 0
        
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
            read_file.close()

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
        self.file.write("<tokens>")
        self.file.write(END_LINE)

    def writeEnd(self):
        self.file.write("</tokens>")

    def writeKeyword(self, value):
        self.file.write("<keyword> {value} </keyword>".format(value=value))
        self.file.write(END_LINE)

    def writeSymbol(self, value):
        if (value == ">"):
            value = "&gt;"
        elif (value == "<"):
            value = "&lt;"
        elif (value == "&"):
            value = "&amp;"
        self.file.write("<symbol> {value} </symbol>".format(value=value))
        self.file.write(END_LINE)

    def writeIdentifier(self, value):
        self.file.write("<identifier> {value} </identifier>".format(value=value))
        self.file.write(END_LINE)
    
    def writeInt(self, value):
        self.file.write("<integerConstant> {value} </integerConstant>".format(value=value))
        self.file.write(END_LINE)

    def writeStartString(self, value):
        self.file.write("<stringConstant> {value}".format(value=value))

    def writeString(self, value):
        self.file.write(" {value}".format(value=value))

    def writeEndString(self, value):
        self.file.write(" {value} </stringConstant>".format(value=value))
        self.file.write(END_LINE)

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
    def __init__(self, xml_file, xmlT_filename):
        self.file = xml_file
        self.read_filename = xmlT_filename
        self.current_line = 0
        self.lines = None
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
        with open(self.read_filename) as read_file:
            self.lines = read_file.readlines()
            self.verifyOpeningToken()
            self.getNextLine()
            self.compileClass()
            self.verifyEndingToken()
            read_file.close()

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
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            if (token in self.class_var_dec):
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
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            if (token in self.subroutine):
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
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        prev_tabs = self.tabs
        self.write("<parameterList>")
        self.tabs += "  "
        if (token in self.type):
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
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            if (token == "var"):
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
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            if (token in self.statements):
                if (token == "let"):
                    self.handleLet()
                elif (token == "if"):
                    self.handleIf()
                elif (token == "do"):
                    self.handleDo()
                elif (token == "while"):
                    self.handleWhile()
                elif (token == "return"):
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
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)

        if (token == "."):
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
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        if (token != ";"):
            self.handleExpression()
        self.eat(";")

        self.tabs = prev_tabs
        self.write("</returnStatement>")

    def compileExpressionList(self):
        self.write("<expressionList>")
        prev_tabs = self.tabs
        self.tabs += "  "

        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        if (token != ")"):
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
        line = self.lookCurrentLine()
        token_type = self.getTokenTypeFromLine(line)

        if (token_type == "integerConstant"):
            self.eatType("integerConstant")
        elif (token_type == "stringConstant"):
            self.eatType("stringConstant")
        elif (token_type == "identifier"):
            self.eatType("identifier")
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            if (token == "["):
                self.eat("[")
                self.handleExpression()
                self.eat("]")
            elif (token == "("):
                self.eat("(")
                self.compileExpressionList()
                self.eat(")")
            elif (token == "."):
                self.eat(".")
                self.eatType("identifier")
                self.eat("(")
                self.compileExpressionList()
                self.eat(")")
        else:
            token = self.getTokenFromLine(line)
            if (token in self.keyword_constant):
                self.eatType("keyword")
            elif (token in self.unaryOp):
                self.eat(self.unaryOp)
                self.handleTerm()
            elif (token == "("):
                self.eat("(")
                self.handleExpression()
                self.eat(")")
        self.tabs = prev_tabs
        self.write("</term>")

    def eat(self, token_to_eat):
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        if (token in token_to_eat):
            self.write(line)
            self.getNextLine()
            return True
        return False
    
    def eatType(self, type):
        line = self.lookCurrentLine()
        token_type = self.getTokenTypeFromLine(line)
        if (token_type == type):
            self.getNextLine()
            self.write(line)
        else:
            print("ERROR! Eat type error!", end='')
            print("\t line: " + line + "\t type_to_eat: " + type)

    def eatOperator(self, token_to_eat):
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        if (token in token_to_eat):
            self.getNextLine()
            if (token == "\""):
                self.write("<symbol> &quot; </symbol>")
                return True
            else:
                self.write(line)
                return True
        return False

    def getNextLine(self):
        self.current_line += 1

    def getTokenFromLine(self, line):
        return line.split(" ")[1]

    def getTokenTypeFromLine(self, line):
        token_type = line.split(" ")[0]
        return token_type[1:-1]

    def lookCurrentLine(self):
        current_line = self.lines[self.current_line]
        return current_line.strip()

    def write(self, line):
        self.file.write(self.tabs)
        self.file.write(line + END_LINE)

    def close(self):
        self.file.close()

    def verifyOpeningToken(self):
        line = self.lookCurrentLine()
        if (line != "<tokens>"):
            print("ERROR! MISSING OPENING TOKEN")

    def verifyEndingToken(self):
        if (self.lookCurrentLine() != "</tokens>"):
            print(self.lookCurrentLine())
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
            xmlT_filename = file_name + "T.xml"
            class_name = file_name.split("\\")[1]
            ALL_CLASSES.append(class_name)
            with open(xmlT_filename, "w") as xmlT_file:
                tokenizer = Tokenizer(xmlT_file, jack_filename)
                tokenizer.parse()
                xmlT_file.close()
        
        for xmlT_filename in glob.glob(directory + "/*T.xml"):
            xml_filename = xmlT_filename.split('.')[0][:-1] + ".xml"
            with open(xml_filename, "w") as xml_file:
                compilationEngine = CompilationEngine(xml_file, xmlT_filename)
                compilationEngine.compile()
                xml_file.close()

    def translateFile(self, file_name):
        prefix_filename = file_name.split('.')[0]
        jack_filename = prefix_filename + ".jack"
        xmlT_filename = prefix_filename + "T.xml"
        xml_filename =  prefix_filename + ".xml"
        class_name = prefix_filename.split("\\")[1]

        with open(xmlT_filename, "w") as xmlT_file:
            ALL_CLASSES.append(class_name)
            tokenizer = Tokenizer(xmlT_file, jack_filename)
            tokenizer.parse()
        xmlT_file.close()

        with open(xml_filename, "w") as xml_file:
            compilationEngine = CompilationEngine(xml_file, xmlT_filename)
            compilationEngine.compile()
        xml_file.close()

if __name__ == '__main__':
    Main(sys.argv[1:])