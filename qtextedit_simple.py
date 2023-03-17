from PyQt5 import QtGui


class TxtBoxPrinter():
    def __init__(self, QtWidgets_QTextEdit_object: object, use_txt_box_printer_formating: object = None):
        """Prints the text in the Text Box using method TxtBoxPrinter.print_text
        Default behavior: Prints one line of text and moves to a new line, placing the cursor at the end of the printout.
        Args:
            QtWidgets_QTextEdit_object (QTextEdit): The object in which the text is printed
            use_txt_box_writer_formating (TxtBoxPrinter)(optional): TxtBoxPrinter object from which text formatting will be downloaded
        """
        # QTextEdit object to print in
        self.box = QtWidgets_QTextEdit_object
        # Define global formating objects
        self.global_font = QtGui.QFont()
        self.global_color = QtGui.QColor()
        self.global_text_char_format = QtGui.QTextCharFormat()
        self.cursor = QtWidgets_QTextEdit_object.textCursor()
        self.no_new_line = False
        self.errors = []
        # Get formating
        if use_txt_box_printer_formating is not None:
            self._setup_global_formating(use_txt_box_printer_formating)
        # Load Roboto Mono Font
        roboto_mono_font_idx =  QtGui.QFontDatabase.addApplicationFont("RobotoMono-Regular.ttf")
        result = QtGui.QFontDatabase.applicationFontFamilies(roboto_mono_font_idx)
        if len(result) > 0:
            self.roboto_mono_font = result[0]
        else:
            self.roboto_mono_font = ""

    def _setup_global_formating(self, self_class: object):
        self.global_font = self_class.get_font()
        self.global_color = self_class.get_color()
        self.global_text_char_format = self_class.get_text_char_format()

    def get_font(self) -> object:
        """Returns current QFont object
        """
        return self.global_font

    def get_color(self) -> object:
        """Returns current QColor object
        """
        return self.global_color

    def get_text_char_format(self) -> object:
        """Returns current QTextCharFormat object
        """
        return self.global_text_char_format

    def print_button(self, button_type: str, button_text: str, button_data: str, font_size: int = 12):
        """Prints Button in the Text Box.
        Args:
            button_type (str): String that represent type of Button to print
                'link' - '|^L|text|^L|data - Opens link (data) in browser
                'code' - '|^C|text|^C|data - Shows example code from url (data)
            button_text (str): Button text
            button_data (str): Usually some url that should be opened or display data from it
            font_size (int)(optional): Font size
        """
        if button_type.lower() == "link":
            type_string = "|^L|"
        elif button_type.lower() == "code":
            type_string = "|^C|"
        else:
            type_string = "|^?|"
        self.print_text(type_string, f"size={font_size}, n=false, font_name=Arial, fg=#ffff00, bc=#00007f, invisible=true")
        self.print_text(button_text, f"size={font_size}, n=false, font_name=Arial, fg=yellow, bc=#00007f")
        self.print_text(type_string, f"size={font_size}, n=false, font_name=Arial, fg=#ffff00, bc=#00007f, invisible=true")
        self.print_text(button_data + type_string, "size=1, font_name=Arial, fg=#ffff00, bc=#00007f, invisible=true, n=false")
        end_position = self.print_text("", "size=1, n=false")
        end_string = str(end_position + 11)
        end_string = "0"*(10-len(end_string)) + end_string
        self.print_text(end_string, "size=1, invisible=true")

    def get_button_info(self) -> list:
        """Returns a list with information about the button for current cursor position.
        If no button is found at the current cursor position, it returns an empty list.
        Returns:
            list: [button_signature( |^?| ), button_text, button_data]
        """
        cursor = self.box.textCursor()
        block = cursor.block()
        block_text = block.text()
        cursor_position_in_block = cursor.position() - block.position()
        button_position = block_text.find("|^")
        if button_position < 0:
            return []
        
        button_signature = block_text[button_position:button_position+4]
        elements = block_text.split(button_signature)
        elements_len = len(elements)
        button_data = elements[elements_len-2]
        button_text = elements[elements_len-3]
        # button_end_string = elements(elements_len-1)

        button_end_position = block_text.find("|^", button_position+1) + 8 + len(button_data)
        
        # Check if cursor is on button
        if cursor_position_in_block < button_position or cursor_position_in_block > button_end_position:
            return []

        # Move cursor to end of block
        # cursor.setPosition(int(button_end_string))
        
        # Delete button if button_type is 'code'
        if button_signature == "|^C|":
            cursor.select(QtGui.QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()

        return [button_signature, button_text, button_data]

    def print_code(self, code_text: str, code_title: str = "Code Example:"):
        """Prints the code example.
        """
        # Set print format
        cursor_position = self.print_text("", "@font_name=Source Code Pro, @color=white, @bc=black, @size=10")
        # Transform text into lines
        code_body = code_text.split("\n")
        # Get max lenght
        max_len = len(code_title)
        for code_line in code_body:
            if len(code_line) > max_len:
                max_len = len(code_line)
        max_len = max_len + 2  # addig 2 for blank space left and right
        font = QtGui.QFont("Source Code Pro", 10)
        fm = QtGui.QFontMetrics(font)
        char_width = fm.widthChar("H")
        char_num = int(self.box.contentsRect().width() / char_width) - 6
        if max_len > char_num:
            max_len = char_num
        # Print Title
        code_title = " " + code_title + " "*(max_len-len(code_title)+1)
        self.print_text(code_title, "wrap_mode=false, color=black, bc=dark grey")
        # Print Code
        for code_line in code_body:
            code_line_text = " " + code_line + " "*(max_len-len(code_line)+1)
            self.print_text(code_line_text, "wrap_mode=false")
        self.box.textCursor().setPosition(cursor_position, QtGui.QTextCursor.MoveAnchor)
        self.box.ensureCursorVisible()

    def print_text(self, text_to_print: str = "`None|Ignore`", formating_flags: str = ""):
        """Prints the text in the Text Box.
        Default behavior: Prints one line of text and moves to a new line, placing the cursor at the end of the printout.
        Args:
            text_to_print (str)(optional): Text to be printed
            formating_flags (str)(optional): Formating flags (font, color, etc.)
            use_txt_box_writer_formating (TxtBoxPrinter)(optional): TxtBoxPrinter object from which text formatting will be downloaded
        Flags:
            "cls": ["cls", "clear"]: Clear content of text box (No value needed)
            "color": ["color", "fc", "c", "foreground", "foreground_color", "fore_color", "fg"]: Sets the foreground text color (String)
            "background": ["background", "background_color", "back_color", "bc", "background color"]: Sets the background text color (String)
            "font_size": ["font_size", "size", "fs", "font size"]: Sets font size (Integer)
            "font_name": ["font_name", "fn", "font name", "font"]: Sets font name (String), if font name=fixed then is system fixed size font used
            "font_bold": ["font_bold", "fb", "font bold", "bold"]: Sets font to bold (True/False)
            "font_italic": ["font_italic", "fi", "font italic", "italic", "i"]: Sets font to italic (True/False)
            "font_underline": ["font_underline", "fu", "font underline", "underline", "font_under", "font under", "under"]: Sets font to underline (True/False)
            "new_line": ["new_line", "nl", "new_l", "n", "new line"]: Default is 'True', if 'False' cursor will not go in new line
            "Move": ["move", "position", "@move", "@position"]: Move cursor in beginning or end of text (Beginning/End)
            "Invisible": ["invisible", "ghost", "silent"]: Sets font forecolor=background color
        """
        # Make variables for text and flags
        txt = text_to_print
        self.flags = formating_flags
        # Create a dictionary of synonyms for commands and values
        comm_syn = {
            "cls": ["cls", "clear"],
            "color": ["color", "fc", "c", "foreground", "foreground_color", "fore_color", "fore", "fg"],
            "@color": ["@color", "@fc", "@c", "@foreground", "@foreground_color", "@fore_color", "@fore", "@fg"],
            "background": ["background", "background_color", "back_color", "bc", "background color", "back"],
            "@background": ["@background", "@background_color", "@back_color", "@bc", "@background color", "@back"],
            "font_size": ["font_size", "size", "fs", "font size"],
            "@font_size": ["@font_size", "@size", "@fs", "@font size"],
            "font_name": ["font_name", "fn", "font name", "font"],
            "@font_name": ["@font_name", "@fn", "@font name", "@font"],
            "font_bold": ["font_bold", "fb", "font bold", "bold"],
            "@font_bold": ["@font_bold", "@fb", "@font bold", "@bold"],
            "font_italic": ["font_italic", "fi", "font italic", "italic", "i"],
            "@font_italic": ["@font_italic", "@fi", "@font italic", "@italic", "@i"],
            "font_underline": ["font_underline", "fu", "font underline", "underline", "font_under", "font under", "under"],
            "@font_underline": ["@font_underline", "@fu", "@font underline", "@underline", "@font_under", "@font under", "@under"],
            "new_line": ["new_line", "nl", "new_l", "n", "new line"],
            "@new_line": ["@new_line", "@nl", "@new_l", "@n", "@new line"],
            "Move": ["move", "position", "@move", "@position"],
            "Invisible": ["invisible", "ghost", "silent"],
            "wrap_mode": ["wrap_mode", "wrap mode", "wrap", "word_wrap", "word wrap"]
        }
        val_syn = {
            "True": ["true", "1", "yes", "ok"],
            "False": ["false", "0", "no"],
            "Start": ["start", "beginning", "begining", "in start", "in beginning", "in begining", "in the beginning", "in the begining", "0", "top"],
            "End": ["end", "bottom", "botom", "at end", "at bottom", "at botom", "the end", "1"],
            "Fixed_Font": ["fixed_font", "fixed", "fix", "fixed font", "fixed_size", "fixed size", "fixed_width", "fixed width", "f"]
        }
        # Create list [flag, value, error]
        commands = self._parse_flag_string(formating_flags, comm_syn)
        # Define local formating objects
        char_format = QtGui.QTextCharFormat(self.global_text_char_format)
        text_option = QtGui.QTextOption()
        text_option.setWrapMode(QtGui.QTextOption.NoWrap)
        color = QtGui.QColor(self.global_color)
        font = QtGui.QFont(self.global_font)
        # Set default values for variables
        no_new_line = self.no_new_line
        cursor = self.box.textCursor()
        # Execute flags
        for i in range(0, len(commands)):
            cl = commands[i][1].lower()
            if cl in val_syn["True"] or cl in val_syn["False"] or cl in val_syn["Start"] or cl in val_syn["End"]:
                commands[i][1] = cl
            if commands[i][0] in comm_syn["cls"]:
                self.box.setText("")
            elif commands[i][0] in comm_syn["color"]:
                val = commands[i][1]
                if val.find("rgb") >= 0:
                    v = self._rgb_values(val)
                    color.setRgb(v[0], v[1], v[2])
                else:
                    color.setNamedColor(val)
                char_format.setForeground(color)
            elif commands[i][0] in comm_syn["@color"]:
                val = commands[i][1]
                if val.find("rgb") >= 0:
                    v = self._rgb_values(val)
                    color.setRgb(v[0], v[1], v[2])
                else:
                    color.setNamedColor(val)
                char_format.setForeground(color)
                self.global_color.setNamedColor(val)
                self.global_text_char_format.setForeground(color)
            elif commands[i][0] in comm_syn["Invisible"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    char_format.setForeground(char_format.background())
            elif commands[i][0] in comm_syn["background"]:
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setBackground(color)
            elif commands[i][0] in comm_syn["@background"]:
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setBackground(color)
                self.global_color.setNamedColor(val)
                self.global_text_char_format.setBackground(self.global_color)
            elif commands[i][0] in comm_syn["font_size"]:
                try:
                    val = int(commands[i][1])
                except ValueError:
                    val = self.global_font.pointSize()
                char_format.setFontPointSize(val)
            elif commands[i][0] in comm_syn["@font_size"]:
                try:
                    val = int(commands[i][1])
                except ValueError:
                    val = self.global_font.pointSize()
                char_format.setFontPointSize(val)
                self.global_text_char_format.setFontPointSize(val)
            # elif commands[i][0] in comm_syn["wrap_mode"]:
            #     val = commands[i][1]
            #     if val in val_syn["False"]:
            #         char_format.setProperty(1, text_option.wrapMode())
            elif commands[i][0] in comm_syn["font_name"]:
                val = commands[i][1]
                if commands[i][1] in val_syn["Fixed_Font"]:
                    char_format.setFontFamily(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont).family())
                elif commands[i][1].lower() == "roboto mono":
                    char_format.setFontFamily(self.roboto_mono_font)
                else:
                    char_format.setFontFamily(val)
            elif commands[i][0] in comm_syn["@font_name"]:
                val = commands[i][1]
                if commands[i][1] in val_syn["Fixed_Font"]:
                    char_format.setFontFamily(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont).family())
                    self.global_text_char_format.setFontFamily(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont).family())
                elif commands[i][1].lower() == "roboto mono":
                    char_format.setFontFamily(self.roboto_mono_font)
                    self.global_text_char_format.setFontFamily(self.roboto_mono_font)
                else:
                    char_format.setFontFamily(val)
                    self.global_text_char_format.setFontFamily(val)
            elif commands[i][0] in comm_syn["font_bold"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setBold(True)
                    char_format.setFontWeight(QtGui.QFont.Bold)
                elif val in val_syn["False"]:
                    font.setBold(False)
                    char_format.setFontWeight(QtGui.QFont.Normal)
            elif commands[i][0] in comm_syn["font_italic"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setItalic(True)
                    char_format.setFontItalic(True)
                elif val in val_syn["False"]:
                    font.setItalic(False)
                    char_format.setFontItalic(False)
            elif commands[i][0] in comm_syn["@font_bold"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setBold(True)
                    char_format.setFontWeight(QtGui.QFont.Bold)
                    self.global_font.setBold(True)
                    self.global_text_char_format.setFontWeight(QtGui.QFont.Bold)
                elif val in val_syn["False"]:
                    font.setBold(False)
                    char_format.setFontWeight(QtGui.QFont.Normal)
                    self.global_font.setBold(False)
                    self.global_text_char_format.setFontWeight(QtGui.QFont.Normal)
            elif commands[i][0] in comm_syn["@font_italic"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setItalic(True)
                    char_format.setFontItalic(True)
                    self.global_font.setItalic(True)
                    self.global_text_char_format.setFontItalic(True)
                elif val in val_syn["False"]:
                    font.setItalic(False)
                    char_format.setFontItalic(False)
                    self.global_font.setItalic(False)
                    self.global_text_char_format.setFontItalic(False)
            elif commands[i][0] in comm_syn["font_underline"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setUnderline(True)
                    char_format.setFontUnderline(True)
                elif val in val_syn["False"]:
                    font.setUnderline(False)
                    char_format.setFontUnderline(False)
            elif commands[i][0] in comm_syn["@font_underline"]:
                val = commands[i][1]
                if val in val_syn["True"]:
                    font.setUnderline(True)
                    char_format.setFontUnderline(True)
                    self.global_font.setUnderline(True)
                    self.global_text_char_format.setFontUnderline(True)
                elif val in val_syn["False"]:
                    font.setUnderline(False)
                    char_format.setFontUnderline(False)
                    self.global_font.setUnderline(False)
                    self.global_text_char_format.setFontUnderline(False)
            elif commands[i][0] in comm_syn["new_line"]:
                if commands[i][1] in val_syn["True"]:
                    no_new_line = False
                elif commands[i][1] in val_syn["False"]:
                    no_new_line = True
            elif commands[i][0] in comm_syn["@new_line"]:
                if commands[i][1] in val_syn["True"]:
                    no_new_line = False
                    self.no_new_line = False
                elif commands[i][1] in val_syn["False"]:
                    no_new_line = True
                    self.no_new_line = True
            elif commands[i][0] in comm_syn["Move"]:
                if commands[i][1] in val_syn["Start"]:
                    cursor.movePosition(QtGui.QTextCursor.Start)
                    self.box.moveCursor(QtGui.QTextCursor.Start)
                    cursor_freeze = True
                elif commands[i][1] in val_syn["End"]:
                    cursor.movePosition(QtGui.QTextCursor.End)
                    self.box.moveCursor(QtGui.QTextCursor.End)
                    cursor_freeze = True
        # Add text to txt_info
        if not no_new_line:
            txt = txt + "\n"
        if txt.rstrip() != "`None|Ignore`":
            cursor.insertText(txt, char_format)
        self.box.textCursor().setPosition(cursor.position())
        self.box.ensureCursorVisible()
        return cursor.position()

    def _rgb_values(self, rgb_string: str) -> tuple:
        a = rgb_string.replace("(", "").lower()
        b = a.replace(")", "")
        a = b.replace("rgb", "")
        b = a.split(",")
        try:
            a = (int(b[0]), int(b[1]), int(b[2]))
        except ValueError or IndexError:
            a = (0,0,0)
        return a

    def _parse_flag_string(self, flags_string: str, flag_names_dict: dict) -> list:
        """Handles the flags.
        Args:
            flags_string (str): String with user flags
            flag_names_dict (dict): Valid flag commands
        Returns:
            list: List of commands, values and Errors
        """
        result = []
        indicator = False
        new_string = ""
        for i in range(len(flags_string)):
            if flags_string[i] == "(":
                indicator = True
            elif flags_string[i] == ")":
                indicator = False
            if indicator:
                if flags_string[i] == ",":
                    new_string = new_string + "~"
                else:
                    new_string = new_string + flags_string[i]
            else:
                new_string = new_string + flags_string[i]
        flag_list = new_string.split(",")
        for idx, i in enumerate(flag_list):
            flag_list[idx] = flag_list[idx].replace("~", ",")

        for i in flag_list:
            flag_and_value = i.split("=")
            if len(flag_and_value) == 1:
                result.append([flag_and_value[0].strip().lower(), "", ""])
            elif len(flag_and_value) == 2:
                result.append([flag_and_value[0].strip().lower(), flag_and_value[1].strip(), ""])
            elif len(flag_and_value) > 2:
                result.append(["", "", "The number of assigned values ​​has been exceeded"])
            elif len(flag_and_value) == 0:
                result.append(["", "", ""])

        for idx, i in enumerate(result):
            has_error = True
            if i[0] != "" and i[1] != "":
                for key, value in flag_names_dict.items():
                    if i[0] in value:
                        has_error = False
                        break
                if has_error:
                    result[idx][2] = "Unrecognized command"
                    result[idx][1] = flag_list[idx]
                    result[idx][0] = ""
        for i in result:
            if i[2] != "":
                self.errors.append([i[1], i[2]])

        return result

    def flags_has_errors(self):
        """Returns True if the Flag string had an errors
        """
        if len(self.errors) > 0:
            return True
        else:
            return False

    def get_flag_error_list(self):
        """List of errors found in the Flags string.
        """
        return self.errors        

    def clear_flag_error_list(self):
        self.errors = []

