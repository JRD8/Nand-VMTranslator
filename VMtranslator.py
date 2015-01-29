#######################
## JRD VM TRANSLATOR ##
#######################


## PARSER MODULE ##

def input_eval(source_input):
    print "\nThis is the Source: " + source_input # Print the Source Input

    if source_input.find(".vm") == -1: # Directory input
        input_type = "directory"
        print " (Directory Input)\n"
        import os
        script_path = os.path.dirname(os.path.abspath(__file__))
        source_path = script_path + "/" + source_input + "/*.vm"
        print "Source Path = " + source_path + "\n"

    if source_input.find(".vm") != -1: # VM file Input
        input_type = "file"
        print " (VM File Input)\n"
        source_path = ""

    source_name = source_input
    out_file = codewriterConstructor(source_name)
    
    return input_type, out_file, source_path


def process_input(source_input, input_type, source_path):
    
    # COMMENT OUT THIS LINE IF NO BOOTSTRAP CODE
    writeInit() # Process bootstrap code

    if input_type == "file":
        process_file(source_input)

    if input_type == "directory":
        import glob
        path = source_path
        files=glob.glob(path)

        for file in files:
            process_file(file)
    return


def process_file(source_file):

    code_lines = parserConstructor(source_file)
    
    print "Processing: " + source_file + "\n"

    out_file.write("\n// ***********************************\n// SOURCE VM CODE FOR: " + source_file + "\n\n")
    for line in code_lines: # Write code lines as comments
        out_file.write("// " + line + "\n")
    out_file.write("\n") # ...And some carriage returns
    out_file.write("// OBJECT ASM CODE FOR: " + source_file + "\n")

    # Begin iterating through commands to translate
    line_number = 0

    global current_command
    global static_filename
    global input_type
    
    # Create static_filename variable
    if input_type == "file": # Use source_file as is for static_filename
        static_filename = source_file[0:source_file.find(".")]
    if input_type == "directory":
        search = True
        result = 0
        i = 0
        while search: # Extract more usable static_filename from source_file with full path
            result = source_file.find("/", i)
            if result != -1:
                i = result + 1
                search = True
            if result == -1:
                static_filename = source_file[i:source_file.find(".")]
                search = False

    while hasMoreCommands(line_number):
        current_command = advance(code_lines, line_number)
        print "Current Command: " + current_command
        print "Current Command Type: " + commandType(current_command)
        
        if commandType(current_command) != "C_RETURN": # "C_RETURN" has NO arguments
            print "Current Arg1: " + arg1(current_command)
            print "Current Arg2: " + arg2(current_command)
    
        if commandType(current_command) == "C_PUSH" or commandType(current_command) == "C_POP":
            writePushPop(commandType(current_command), arg1(current_command), arg2(current_command))
        if commandType(current_command) == "C_ARITHMETIC":
            writeArithmetic(arg1(current_command))
        if commandType(current_command) == "C_LABEL":
            writeLabel(arg1(current_command))
        if commandType(current_command) == "C_GOTO":
            writeGoto(arg1(current_command))
        if commandType(current_command) == "C_IF":
            writeIf(arg1(current_command))
        if commandType(current_command) == "C_FUNCTION":
            writeFunction(arg1(current_command), arg2(current_command))
        if commandType(current_command) == "C_RETURN":
            writeReturn()
        if commandType(current_command) == "C_CALL":
            writeCall(arg1(current_command), arg2(current_command))

        print "\n"
        line_number = line_number + 1

    return

def parserConstructor(source_file):
    
    global code_lines
    code_lines = []

    txt = open(source_file, 'r') # Open source_file to read
    initial_lines = txt.readlines() # Read the source file, by line, into initial_lines list

    # Convert initial_lines to usable code lines, stripping out \r\n and comments
    for line in initial_lines:
        line = line.replace("\r\n", "")
        line = line.replace("\n", "")
        if line.find("//") != -1:
            commentIndex = line.find("//")
            line = line[:commentIndex]
        line = line.replace("\t", "")
        
        while line.find("  ") != -1:
            line = line.replace("  ", "")
        
        if line.find("//") == -1 and line != "":
            code_lines.append(line)
    
    return code_lines


def hasMoreCommands(line_number):
    if line_number + 1 > len(code_lines):
        return False
    return True


def advance(code_lines, line_number):
    return code_lines[line_number]


def commandType(current_command):
    if current_command.find("push") != -1:
        return "C_PUSH"
    if current_command.find("pop") != -1:
        return "C_POP"
    if current_command.find("label") != -1:
        return "C_LABEL"
    if current_command.find("goto") != -1:
        if current_command.find("if") == -1: # then "goto" command
            return "C_GOTO"
        else: # then "if-goto" command
            return "C_IF"
    if current_command.find("function") != -1:
        return "C_FUNCTION"
    if current_command.find("return") != -1:
        return "C_RETURN"
    if current_command.find("call") != -1:
        return "C_CALL"

    return "C_ARITHMETIC" # If none of above, must be ARITHMETIC commandType


def arg1(current_command):
    if commandType(current_command) == "C_RETURN":
        return
    if commandType(current_command) == "C_ARITHMETIC":
        blank_space = current_command.find(" ")
        if blank_space != -1:
            return current_command[0:blank_space]
        else:
            return current_command
        return current_command
    start = current_command.find(" ")
    if current_command.find(" ", start + 1) != -1: # there IS an arg2
        end = current_command.find(" ", start + 1)
        return current_command[start + 1:end]
    else: # there is NO arg2
        return current_command[start + 1:]


def arg2(current_command):
    if commandType(current_command) == "C_RETURN" or commandType(current_command) == "C_ARITHMETIC" or commandType(current_command) == "C_LABEL" or commandType(current_command) == "C_GOTO" or commandType(current_command) == "C_IF":
        return ""
    temp = current_command.find(" ")
    start = current_command.find(" ", temp + 1)
    return current_command[start + 1:]



## CODEWRITER MODULE ##


def codewriterConstructor(source_name):
    
    if source_name.find(".") != -1: # source_name is a file name (.vm)
        out_filename = source_name[0:source_name.find(".")] + ".asm" # Extract and cat to create the Output Filename
    else:
        out_filename = source_name + ".asm" # Extract and cat to create the Output Filename

    out_file = open(out_filename, 'w') # Open the Output File to write
    
    print "Writing the Destination File (.asm): " + out_filename + "\n" # Print the Output Filename

    # Get date/time stamp
    from time import localtime, strftime
    temp = strftime("%a, %d %b %Y %X", localtime())

    #Write header  as comments
    out_file.write("// VM TRANSLATED FROM: " + source_name + "\n// ON: " + temp + "\n\n// ***************************\n")

    return out_file


def setFilename(out_file): ## NOT USED, although discussed in book
    return



# Chapter 7 Functions



def writeArithmetic(command):
    
    
    if command == "eq" or command == "gt" or command == "lt": # EQ, GT & LT routines
        loop1 = uniqueLabel()
        loop2 = uniqueLabel()
        if command == "eq":
            insert1 = "\n// eq\n" # Comment line
            insert2 = "D;JEQ"
        if command == "gt":
            insert1 = "\n// gt\n" # Comment line
            insert2 = "D;JGT"
        if command == "lt":
            insert1 = "\n// lt\n" # Comment line
            insert2 = "D;JLT"
        code_snippet = insert1 + "@SP\nA=M\nA=A-1\nA=A-1\nD=M\nA=A+1\nD=D-M\n@" + loop1 + "\n" + insert2 + "\n@SP\nA=M\nA=A-1\nM=0\nA=A-1\nM=0\nD=A+1\n@" + loop2 + "\n0;JMP\n(" + loop1 + ")\n@SP\nA=M\nA=A-1\nM=0\nA=A-1\nM=-1\nD=A+1\n(" + loop2 + ")\n@SP\nM=D\n"
        out_file.write(code_snippet)
        return

    if command == "neg": # NEG routine
        out_file.write("\n// neg\n") # Comment line
        out_file.write("@SP\nA=M\nA=A-1\nM=-M\n")
        return

    if command == "not": # NOT routine
        out_file.write("\n// not\n") # Comment line
        out_file.write("@SP\nA=M\nA=A-1\nM=!M\n")
        return

    if command == "add" or command == "sub" or command == "and" or command == "or": # ADD, SUB, AND & OR routines
        if command == "add":
            insert1 = "\n// add\n" # Comment line
            insert2 = "D=D+M"
        if command == "sub":
            insert1 = "\n// sub\n" # Comment line
            insert2 = "D=D-M"
        if command == "and":
            insert1 = "\n// and\n" # Comment line
            insert2 = "D=D&M"
        if command == "or":
            insert1 = "\n// or\n" # Comment line
            insert2 = "D=D|M"
        code_snippet = insert1 + "@SP\nA=M\nA=A-1\nA=A-1\nD=M\nA=A+1\n" + insert2 + "\nM=0\nA=A-1\nM=D\n@0\nM=M-1\n"
        out_file.write(code_snippet)
        return



def writePushPop (command, segment, index):
    
    global current_command

    if command != "C_PUSH" and command != "C_POP":
        return ""

    if command == "C_PUSH": # PUSH routines
        if segment == "constant": # CONSTANT routine
            out_file.write("\n// push constant " + arg2(current_command) + "\n") # Comment line
            code_snippet = "@" + arg2(current_command) + "\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            out_file.write(code_snippet)
            return
        
        if segment == "temp": # TEMP routine
            out_file.write("\n// push temp " + arg2(current_command) + "\n") # Comment line
            insert1 = str(5 + int(arg2(current_command)))
            code_snippet = "@" + insert1 + "\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            out_file.write(code_snippet)
            return

        if segment == "pointer": # POINTER routines
            out_file.write("\n// push pointer " + arg2(current_command) + "\n") # Comment line
            if arg2(current_command) == "0": # THIS subroutine
                insert1 = "THIS"
            if arg2(current_command) == "1": # THAT subroutine
                insert1 = "THAT"
            code_snippet = "@" + insert1 + "\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            out_file.write(code_snippet)
            return

        if segment == "static": # STATIC routine
            global static_filename # copy the global variable for static_filename
            out_file.write("\n// push static " + arg2(current_command) + "\n") # Comment line
            insert1 = static_filename + "." + str(arg2(current_command))
            code_snippet = "@" + insert1 + "\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
            out_file.write(code_snippet)
            return

        if segment == "local": # LOCAL routine
            out_file.write("\n// push local " + arg2(current_command) + "\n") # Comment line
            insert1 = "LCL"

        if segment == "argument": # ARGUMENT routine
            out_file.write("\n// push argument " + arg2(current_command) + "\n") # Comment line
            insert1 = "ARG"

        if segment == "this": # THIS routine
            out_file.write("\n// push this " + arg2(current_command) + "\n") # Comment line
            insert1 = "THIS"

        if segment == "that": # THAT routine
            out_file.write("\n// push that " + arg2(current_command) + "\n") # Comment line
            insert1 = "THAT"

        code_snippet = "@" + insert1 + "\nD=M\n@" + arg2(current_command) + "\nA=D+A\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n"
        out_file.write(code_snippet)
        return

    if command == "C_POP": # POP routines
        
        if segment == "temp": # TEMP routine
            out_file.write("\n// pop temp " + arg2(current_command) + "\n") # Comment line
            insert1 = str(5 + int(arg2(current_command)))
            code_snippet = "@" + insert1 + "\nD=A\n@5\nM=D\n@SP\nA=M-1\nD=M\nM=0\n@5\nA=M\nM=D\n@SP\nM=M-1\n"
            out_file.write(code_snippet)
            return
        
        if segment == "pointer": # POINTER routines
            out_file.write("\n// pop pointer " + arg2(current_command) + "\n") # Comment line
            if arg2(current_command) == "0 ": # THIS subroutine
                insert1 = "THIS"
            if arg2(current_command) == "1 ": # THAT subroutine
                insert1 = "THAT"
            code_snippet = "@SP\nA=M-1\nD=M\nM=0\n@" + insert1 + "\nM=D\n@SP\nM=M-1\n"
            out_file.write(code_snippet)
            return

        if segment == "static" : # STATIC routine
            global static_filename # copy the global variable for static_filename
            out_file.write("\n// pop static " + arg2(current_command) + "\n") # Comment line
            insert1 = static_filename + "." + str(arg2(current_command))
            code_snippet = "@SP\nA=M-1\nD=M\nM=0\n@" + insert1 + "\nM=D\n@SP\nM=M-1\n"
            out_file.write(code_snippet)
            return
        
        if segment == "local": # LOCAL routine
            out_file.write("\n// pop local " + arg2(current_command) + "\n") # Comment line
            insert1 = "LCL"

        if segment == "argument": # ARGUMENT routine
            out_file.write("\n// pop argument " + arg2(current_command) + "\n") # Comment line
            insert1 = "ARG"

        if segment == "this": # THIS routine
            out_file.write("\n// pop this " + arg2(current_command) + "\n") # Comment line
            insert1 = "THIS"

        if segment == "that": # THAT routine
            out_file.write("\n// pop that " + arg2(current_command) + "\n") # Comment line
            insert1 = "THAT"

        code_snippet = "@" + insert1 + "\nD=M\n@" + arg2(current_command) + "\nD=D+A\n@5\nM=D\n@SP\nA=M-1\nD=M\nM=0\n@5\nA=M\nM=D\n@SP\nM=M-1\n"
        out_file.write(code_snippet)
        return


# Chapter 8 Functions



def writeInit(): # Writes Bootstrap Code command
    
    print "Writing Bootstrap Code\n"
    
    out_file.write("\n// Bootstrap Code:\n") # Comment line
    code_snippet = "// SP = 256\n@256\nD=A\n@SP\nM=D\n\n// call Sys.init 0\n@Sys.init$return-address\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP\n@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP\nD=M\n@0\nD=D-A\n@5\nD=D-A\n@ARG\nM=D\n@SP\nD=M\n@LCL\nM=D\n@Sys.init\n0; JMP\n(Sys.init$return-address)\n"
    out_file.write(code_snippet)
    return



def writeLabel(label):
    
    global current_command
    global current_function_name
    
    out_file.write("\n// label " + arg1(current_command) + "\n") # Comment line
    insert1 = arg1(current_command)
    code_snippet = "(" + current_function_name + "$" + insert1 + ")\n"
    out_file.write(code_snippet)
    return



def writeGoto(label): # Writes C_GOTO (goto) command
    
    global current_command
    
    out_file.write("\n// goto " + arg1(current_command) + "\n") # Comment line
    insert1 = arg1(current_command)
    code_snippet = "@" + current_function_name + "$" + insert1 + "\n0;JMP\n"
    out_file.write(code_snippet)
    return



def writeIf(label): # Writes C_IF (if-goto) command
    
    global current_command
    
    out_file.write("\n// if-goto " + arg1(current_command) + "\n") # Comment line
    insert1 = arg1(current_command)
    code_snippet = "@SP\nA=M-1\nD=M\nM=0\n@SP\nM=M-1\n@" + current_function_name + "$" + insert1 + "\nD;JNE\n"
    out_file.write(code_snippet)
    return



def writeCall(functionName, numArgs): # Writes C_CALL command
    
    global current_command
    global current_function_name
    global numCalls
    
    current_function_name = functionName
    numCalls = numCalls + 1 # Increment counter for the number of program calls
    
    out_file.write("\n// call " + arg1(current_command) + " " + arg2(current_command) + "\n") # Comment line
    code_snippet = "@" + functionName + "$return-address" + str(numCalls) + "\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@LCL\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@ARG\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP\n@THIS\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@THAT\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n@SP\nD=M\n@" + numArgs +"\nD=D-A\n@5\nD=D-A\n@ARG\nM=D\n@SP\nD=M\n@LCL\nM=D\n@" + functionName  + "\n0; JMP\n(" + functionName + "$return-address" + str(numCalls) + ")\n"
    out_file.write(code_snippet)
    return



def writeReturn(): # Writes C_RETURN command

    out_file.write("\n// return\n") # Comment line
    code_snippet = "@LCL\nD=M\n@7\nM=D\n@7\nD=M\n@5\nD=D-A\nA=D\nD=M\n@8\nM=D\n@SP\nA=M-1\nD=M\nM=0\n@SP\nM=M-1\n@ARG\nA=M\nM=D\n@ARG\nD=M\nD=D+1\n@SP\nM=D\n@7\nD=M\n@1\nD=D-A\nA=D\nD=M\n@THAT\nM=D\n@7\nD=M\n@2\nD=D-A\nA=D\nD=M\n@THIS\nM=D\n@7\nD=M\n@3\nD=D-A\nA=D\nD=M\n@ARG\nM=D\n@7\nD=M\n@4\nD=D-A\nA=D\nD=M\n@LCL\nM=D\n@8\nA=M\n0;JMP\n"
    out_file.write(code_snippet)
    return


def writeFunction(functionName, numLocals): # Writes C_FUNCTION command
    
    global current_command
    global current_function_name
    
    current_function_name = functionName
    
    out_file.write("\n// function " + arg1(current_command) + " " + arg2(current_command) + "\n") # Comment line
    code_snippet = "(" + current_function_name + ")\n@" + numLocals + "\nD=A\n@5\nM=D\n@6\nM=0\n(" + current_function_name + "$InitLocals)\n@LCL\nD=M\n@6\nD=D+M\n@7\nM=D\nD=0\n@7\nA=M\nM=D\n@6\nM=M+1\nD=M\n@5\nD=M-D\n@" + current_function_name + "$InitLocals\nD;JGT\n"
    out_file.write(code_snippet)
    return


def close(out_file):
    out_file.write("\n// END OF FILE\n// ************\n")
    out_file.close() # close the Output File
    print "* VM to ASM Translation Complete *\n"
    return


# HELPER ROUTINES

def uniqueLabel():
    global call_counter # Needed to modify global copy of call_counter

    label = "L" + str(call_counter)
    call_counter = call_counter + 1 # Increment for each call to create a unique label
    return label


## MAIN MODULE ##

# Initalize global vars #
# Arrays
initial_lines = [] # Text directly from source file
code_lines = [] # Revised text, stripped and formatted

# Integers
call_counter = 1 # Counter for creating Unique Labels
line_number = 0
numCalls = 0 # Counter for number of program calls

# Strings
current_command = ""
static_filename = ""
current_function_name = "NULL"


# Import text from command line script
from sys import argv
print "JRD Nand-2-Tetris VM Translator, 2015\n"
print "Enter the Source File (.vm) or Source Directory (within this path) to be translated:"
source_input = raw_input(">") # input source name


## These are the test VM files.  Uncomment to substitute for Source Input ##

#source_input = "BasicTest.vm"
#source_input = "SimpleAdd.vm"
#source_input = "StackTest.vm"
#source_input = "PointerTest.vm"
#source_input = "StaticTest.vm"
#source_input = "BasicLoop.vm"
#source_input = "FibonacciSeries.vm"
#source_input = "SimpleFunction.vm"
#source_input = "FibonacciElement"
#source_input = "StaticsTest"


# Open Source File or Directory
input_type, out_file, source_path = input_eval(source_input)

# Process Main Routine
process_input(source_input, input_type, source_path)

# Close Output File
close(out_file) # Close .asm file
