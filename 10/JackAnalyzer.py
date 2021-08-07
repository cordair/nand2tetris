import os, re, sys, glob

END_LINE = "\n"

keyword = {
    "class":        True,
    "constructor":  True,
    "function":     True,
    "method":       True,
    "field":        True,
    "static":       True,
    "var":          True,
    "int":          True,
    "char":         True,
    "boolean":      True,
    "void":         True,
    "true":         True,
    "false":        True,
    "null":         True,
    "this":         True,
    "let":          True,
    "do":           True,
    "if":           True,
    "else":         True,
    "while":        True,
    "return":       True,
}

symbol = {
    "{": True,
    "}": True,
    "(": True,
    ")": True,
    "[": True,
    "]": True,
    ",": True,
    ".": True,
    ";": True,
    "+": True,
    "-": True,
    "*": True,
    "/": True,
    "&": True,
    "|": True,
    "<": True,
    ">": True,
    "=": True,
    "~": True,
}

KEYWORD_TOKEN           = 0
SYMBOL_TOKEN            = 1
START_STRING_TOKEN      = 3
END_STRING_TOKEN        = 4
INTEGER_TOKEN           = 5
IDENTIFIER_TOKEN        = 6
NESTED_TOKEN            = 7

ALL_FILES = []

class Tokenizer:
    def __init__(self, xmlT_file, jack_filename):
        self.file = xmlT_file
        self.read_filename = jack_filename
        

    def parse(self):
        with open(self.read_filename) as read_file:
            self.writeInitialize()

            for line in read_file.readlines():
                # empty line
                if (not line.strip()):
                    continue

                is_string = False
                words = line.split()
                for word in words:
                    if (self.isComment(word)):
                        break
                    token_type = self.classifyToken(word)
                    is_string = self.processToken(token_type, word, is_string)

            self.writeEnd()
            read_file.close()

    def processToken(self, token_type, word, is_string):
        if (is_string):
            if (token_type == END_STRING_TOKEN):
                self.writeEndString(word)
                is_string = False
            return is_string

        if (token_type == KEYWORD_TOKEN):
            self.writeKeyword(word)
        elif (token_type == SYMBOL_TOKEN):
            self.writeSymbol(word)
        elif (token_type == INTEGER_TOKEN):
            self.writeInt(word)
        elif (token_type == START_STRING_TOKEN):
            self.writeStartString(word)
            is_string = True
        elif (token_type == IDENTIFIER_TOKEN):
            self.writeIdentifier(word)
        elif (token_type == NESTED_TOKEN):
            i = 0
            j = -1
            
            while (i < len(word)):
                typei = self.classifyToken(word[i])
                if (typei == SYMBOL_TOKEN):
                    sub_string = word[j+1:i]
                    typej = self.classifyToken(sub_string)
                    if (typej != None):
                        self.processToken(typej, sub_string, False)
                    self.writeSymbol(word[i])
                    j = i
                i += 1
            
            sub_string = word[j+1:i]
            typej = self.classifyToken(sub_string)
            if (typej != None):
                self.processToken(typej, sub_string, False)

        return is_string

    def classifyToken(self, word):
        if (word == ""):
            return None
        elif (keyword.get(word, False)):
            return KEYWORD_TOKEN
        elif (symbol.get(word, False)):
            return SYMBOL_TOKEN
        elif (self.representInt(word)):
            wordInt = int(word)
            if ((wordInt >= 0) and (wordInt <= 32767)):
                return INTEGER_TOKEN
            else:
                print("Too big to be integer")
        elif (word[0] == "\""):
            return START_STRING_TOKEN
        elif (word[-1] == "\""):
            return END_STRING_TOKEN
        elif (self.isIdentifier(word)):
            return IDENTIFIER_TOKEN
        else:
            return NESTED_TOKEN

    def writeInitialize(self):
        self.file.write("<tokens>")
        self.file.write(END_LINE)

    def writeEnd(self):
        self.file.write("</tokens>")

    def writeKeyword(self, value):
        self.file.write("<keyword> {value} </keyword>".format(value=value))
        self.file.write(END_LINE)

    def writeSymbol(self, value):
        self.file.write("<symbol> {value} </symbol>".format(value=value))
        self.file.write(END_LINE)

    def writeIdentifier(self, value):
        if (value == ">"):
            value = "&gt"
        elif (value == "<"):
            value = "&lt"
        elif (value == "="):
            value = "&eq"
        self.file.write("<identifier> {value} </identifier>".format(value=value))
        self.file.write(END_LINE)
    
    def writeInt(self, value):
        self.file.write("<integerConstant> {value} </integerConstant>".format(value=value))
        self.file.write(END_LINE)

    def writeStartString(self, value):
        self.file.write("<stringConstant> {value}".format(value=value))
        self.file.write(END_LINE)

    def writeString(self, value):
        self.file.write(" {value}".format(value=value))
        self.file.write(END_LINE)

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

    def isComment(self, word):
        if (word == "//" or word == "/**" or word == "*" or word == "*/"):
            return True
        return False

class CompilationEngine:
    def __init__(self, xml_file, xmlT_filename):
        self.file = xml_file
        self.read_filename = xmlT_filename
        self.current_line = 0
        self.lines = None
        self.tabs = ""

        self.class_names = ALL_FILES
        self.subroutine_names = []
        self.var_names = []

        self.class_var_dec = ["static", "field"]
        self.type = ["int", "char", "boolean"]
        self.var_dec = ["static", "field"]
        self.subroutine = ["constructor", "function", "method"]
        self.subroutine_dec = ["void"]
        self.keyword_constant = ["this", "true", "false", "null"]
        self.statements = ["let", "if", "do", "while", "return"]
        self.expressions = ["integerConstant", "stringConstant", "keywordConstant", "expression", 
                            "identifier", "unaryOpTerm", "array", "sameClassCall", "diffClassCall"]
        self.op = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
        self.unaryOp = ["-", "~"]
        self.type.extend(self.class_names)
        self.var_dec.extend(self.class_names)
        self.subroutine_dec.extend(self.type)


    def compile(self):
        with open(self.read_filename) as read_file:
            self.lines = read_file.readlines()
            self.verifyOpeningToken()
            self.compileClass()
            self.verifyEndingToken()
            read_file.close()

    def compileClass(self):
        self.write("<class>")
        prev_tabs = self.tabs
        self.tabs += "  "
        
        self.eat(["class"])
        self.eat(self.class_names)
        self.eat(["{"])
        self.handleClassVarDec()
        self.handleSubroutineDec()
        self.eat(["}"])
        
        self.tabs = prev_tabs
        self.write("</class>")

    def eat(self, token_to_eat):
        line = self.getNextLine()
        token = self.getTokenFromLine(line)
        if (token in token_to_eat):
            self.write(line)
            return True
        self.getPreviousLine()
        return False
    
    def eatType(self, type):
        line = self.getNextLine()
        token_type = self.getTokenTypeFromLine(line)
        if (token_type == type):
            self.write(line)
        else:
            print("ERROR! Eat type error!", end='')
            print("\t line: " + line + "\t type_to_eat: " + type)

    def eatVariableName(self):
        line = self.getNextLine()
        token = self.getTokenFromLine(line)
        self.var_names.append(token)
        self.write(line)

    def eatSubroutineName(self):
        line = self.getNextLine()
        token = self.getTokenFromLine(line)
        self.write(line)
        self.subroutine_names.append(token)

    def handleClassVarDec(self):
        while (True):
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            self.write("<classVarDec>")
            if (token in self.class_var_dec):
                prev_tabs = self.tabs
                self.tabs += "  "
            
                self.eat(self.var_dec)
                self.eat(self.type)
                self.eatVariableName()
                while(self.eat([","])):
                    self.eatVariableName()
                self.eat([";"])

                self.tabs = prev_tabs
                self.write("</classVarDec>")
            else:
                self.write("</classVarDec>")
                break
            
    def handleSubroutineDec(self):
        while(True):
            line = self.lookCurrentLine()
            token = self.getTokenFromLine(line)
            self.write("<subroutineDec>")
            if (token in self.subroutine):
                prev_tabs = self.tabs
                self.tabs += "  "

                self.eat(self.subroutine)
                self.eat(self.subroutine_dec)
                self.eatSubroutineName()
                self.eat("(")
                self.handleParameterList()
                self.eat(")")
                self.handleSubroutineBody()

                self.tabs = prev_tabs
                self.write("</subroutineDec>")
            else:
                self.write("</subroutineDec>")
                break

    def handleParameterList(self):
        line = self.lookCurrentLine()
        token = self.getTokenFromLine(line)
        prev_tabs = self.tabs
        if (token in self.type):
            self.write("<parameterList>")
            self.tabs += "  "
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
            self.write("<varDec>")
            if (token == "var"):
                prev_tabs = self.tabs
                self.tabs += "  "

                self.eat("var")
                self.eat(self.type)
                self.eatType("identifier")
                while (self.eat(",")):
                    self.eatType("identifier")
                self.eat(";")
                self.tabs = prev_tabs
                self.write("</varDec>")
            else:
                self.write("</varDec>")
                break

    def compileStatements(self):
        prev_tabs = self.tabs
        self.tabs += "  "
        self.write("<statements>")
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

        self.eat(['let'])
        self.eatType("identifier")
        if (self.eat(['['])):
            self.handleExpression()
            self.eat([']'])
        self.eat(['='])
        self.handleExpression()
        self.eat([';'])

        self.tabs = prev_tabs
        self.write("</letStatement>")

    def handleIf(self):
        self.write("<ifStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat(["if"])
        self.eat(["("])
        self.handleExpression()
        self.eat([")"])
        self.eat(["{"])
        self.compileStatements()
        self.eat(["}"])
        
        while (self.eat(["else"])):
            self.eat(["{"])
            self.compileStatements()
            self.eat(["}"])

        self.tabs = prev_tabs
        self.write("</ifStatement>")

    def handleWhile(self):
        self.write("<whileStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat(["while"])
        self.eat(["("])
        self.handleExpression()
        self.eat([")"])
        self.eat(["{"])
        self.compileStatements()
        self.eat(["}"])
        
        self.tabs = prev_tabs
        self.write("</whileStatement>")

    def handleDo(self):
        self.write("<doStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat(["do"])
        self.eat
        line = self.lookForwardOneLine()
        token = self.getTokenFromLine(line)

        subroutine = ""
        if (token == "("):
            subroutine = "sameClassCall"
        elif (token == "."):
            subroutine = "diffClassCall"
        self.handleSpecificTerm(subroutine)
        self.eat([";"])

        self.tabs = prev_tabs
        self.write("</doStatement>")

    def handleReturn(self):
        self.write("<returnStatement>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.eat(["return"])
        self.handleExpression()
        self.eat([";"])

        self.tabs = prev_tabs
        self.write("</returnStatement>")

    def compileExpressionList(self):
        self.write("<expressionList>")
        prev_tabs = self.tabs
        self.tabs += "  "

        self.handleExpression()
        while (self.eat([","])):
            self.handleExpression()

        self.tabs = prev_tabs
        self.write("</expressionList>")
        
    def handleExpression(self):
        self.handleTerm()
        while (self.eat(self.op)):
            self.handleTerm()
        
    def handleTerm(self):
        line = self.lookCurrentLine()
        token_type = self.getTokenTypeFromLine(line)
        term_type = None

        if (token_type == "integerConstant"):
            term_type = "integerConstant"
        elif (token_type == "stringConstant"):
            term_type = "stringConstant"
        elif (token_type == "keyword"):
            term_type = "keywordConstant"
        elif (token_type == "identifier"):
            term_type = "identifier"
        elif (token_type in self.unaryOp):
            term_type = "unaryOpTerm"
        elif (token_type == "("):
            term_type = "expression"
        else:
            line = self.lookForwardOneLine()
            token = self.getTokenFromLine(line)
            if (token == "["):
                term_type = "array"
            elif (token == "("):
                term_type = "sameClassCall"
            elif (token == "."):
                term_type = "diffClassCall"

        if (term_type in self.expressions):
            self.write("<expression>")
            prev_tabs = self.tabs
            self.tabs += "  "
            
            if (term_type != None):
                self.write("<term>")
                prev_tabs_2 = self.tabs
                self.tabs += "  "
                self.handleSpecificTerm(term_type)
                self.tabs = prev_tabs_2
                self.write("</term>")

            self.tabs = prev_tabs
            self.write("</expression>")
        
    def handleSpecificTerm(self, term_type):
        if (term_type == "integerConstant"):
            self.eatType("integerConstant")
        elif (term_type == "stringConstant"):
            self.eatType("stringConstant")
        elif (term_type == "keywordConstant"):
            self.eatType("keyword")
        elif (term_type == "identifier"):
            self.eatType("identifier")
        elif (term_type == "expression"):
            self.eat("(")
            self.handleExpression()
            self.eat(")")
        elif (term_type == "array"):
            self.eatType("identifier")
            self.eat("[")
            self.handleExpression()
            self.eat("]")
        elif (term_type == "unaryOpTerm"):
            self.eat(self.unaryOp)
            self.handleTerm()
        elif (term_type == "expression"):
            self.eat("(")
            self.handleExpression()
            self.eat(")")
        elif (term_type == "sameClassCall"):
            self.eatType("identifier")
            self.eat("(")
            self.compileExpressionList()
            self.eat(")")
        elif (term_type == "diffClassCall"):
            self.eatType("identifier")
            self.eat(".")
            self.eatType("identifier")
            self.eat("(")
            self.compileExpressionList()
            self.eat(")")

    def getNextLine(self):
        next_line = self.lines[self.current_line]
        self.current_line += 1
        return next_line.strip()

    def getPreviousLine(self):
        self.current_line -= 1
        return self.lines[self.current_line] 

    def getTokenFromLine(self, line):
        return line.split(" ")[1]

    def getTokenTypeFromLine(self, line):
        token_type = line.split(" ")[0]
        return token_type[1:-1]

    def lookCurrentLine(self):
        return self.lines[self.current_line]

    def lookForwardOneLine(self):
        self.current_line += 1
        next_line = self.lines[self.current_line]
        self.current_line -= 1
        return next_line
    
    def lookForwardTwoLine(self):
        self.current_line += 2
        next_line = self.lines[self.current_line]
        self.current_line -= 2
        return next_line

    def write(self, line):
        self.file.write(self.tabs)
        self.file.write(line + END_LINE)

    def close(self):
        self.file.close()

    def verifyOpeningToken(self):
        if (self.getNextLine() != "<tokens>"):
            print("ERROR! MISSING OPENING TOKEN")

    def verifyEndingToken(self):
        if (self.getNextLine() != "</tokens>"):
            print("ERROR! MISSING ENDING TOKEN")


class Main:
    def __init__(self, argv):
        if len(argv) != 0 and os.path.isdir(argv[0]):
            self.translateDirectory(argv[0])
        elif len(argv) != 0 and os.path.splitext(argv[0])[1] == ".jack":
            self.translateFile(argv[0])
        else:
            print("Command: python JackAnalyzer.py <filename>.jack")
            sys.exit(1)

    def translateDirectory(self, directory):
        for jack_filename in glob.glob(directory + "/*.jack"):
            file_name = jack_filename.split('.')[0]
            file_name = file_name.split("\\")[1]
            ALL_FILES.append(file_name)

            xmlT_filename = file_name + "T.xml"
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
        jack_filename = file_name + ".jack"
        xmlT_filename = file_name + "T.xml"
        xml_filename =  file_name + ".xml"

        with open(xmlT_filename, "w") as xmlT_file:
            ALL_FILES.append(file_name)
            tokenizer = Tokenizer(xmlT_file, jack_filename)
            tokenizer.parse()
        xmlT_file.close()

        with open(xml_filename, "w") as xml_file:
            compilationEngine = CompilationEngine(xml_file, xmlT_filename)
            compilationEngine.compile()
        xml_file.close()

if __name__ == '__main__':
    Main(sys.argv[1:])