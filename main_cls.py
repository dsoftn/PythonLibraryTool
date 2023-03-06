from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QCoreApplication
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
import sys
import os
import sqlite3
import importlib
import json

import main_ui


class Analyzer(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_txt = []
        self.last_txt_idx = 0
        self.drag_mode = False  # If true then user resize widgets in progress
        self.object_list = []  # Lista objekata
        # Setup GUI
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # Load connection to database
        self.conn = Database()
        # Hide progress bar !!! ABANDONED - now hide lbl_items_analyzed
        # self.ui.prb_lib.setVisible(False)
        self.ui.lbl_items_analyzed.setVisible(False)

    def start_me(self):
        # Load settings (window position and size)
        self.load_setting()
        self.create_custom_menu()
        # Connect events with slots
        self.closeEvent = self.save_setting
        self.ui.txt_lib.returnPressed.connect(self.txt_lib_return_pressed)
        self.ui.txt_find.returnPressed.connect(self.txt_find_return_pressed)
        self.ui.btn_analyze.clicked.connect(self.txt_lib_return_pressed)
        self.ui.tree_lib.currentChanged = self.tree_lib_current_changed
        self.ui.tree_lib.itemExpanded.connect(self.tree_lib_item_expanded)
        self.ui.tree_lib.customContextMenuRequested.connect(self.tree_custom_menu_request)
        # Update tree
        self.update_tree()
        # Show window
        self.show()

    def tree_custom_menu_request(self, pos):
        self.mnu_tree_menu.exec_(self.ui.tree_lib.mapToGlobal(pos))

    def create_custom_menu(self):
        self.ui.tree_lib.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # Create menu and actions
        self.mnu_tree_menu = QtWidgets.QMenu(self.ui.tree_lib)
        self.mnu_tree_delete_act = QtWidgets.QAction("Delete object and all sub objects")
        self.mnu_tree_analyze_all = QtWidgets.QAction("Analyze all sub objects !")
        self.mnu_tree_search_object = QtWidgets.QAction("Search in this object")
        # Add actions
        self.mnu_tree_menu.addAction(self.mnu_tree_delete_act)
        self.mnu_tree_menu.addAction(self.mnu_tree_analyze_all)
        self.mnu_tree_menu.addAction(self.mnu_tree_search_object)
        # Connect actions withs slots
        self.mnu_tree_delete_act.triggered.connect(self.mnu_delete_triggered)
        self.mnu_tree_analyze_all.triggered.connect(self.mnu_analyze_all_triggered)
        self.mnu_tree_search_object.triggered.connect(self.mnu_search_triggered)

    def mnu_search_triggered(self):
        msg_title = "Search"
        msg_text = f"Search in {self.ui.tree_lib.currentItem().text(0)} for string: "
        msg_def_text = self.ui.txt_find.text()
        result, ok = QtWidgets.QInputDialog.getText(self, msg_title, msg_text, text=msg_def_text)
        if ok and result != "":
            self.txt_find_return_pressed(search_text=result, object_id=self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole))

    def mnu_delete_triggered(self):
        obj_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        rslt = self.conn.get_full_name(obj_id)
        msg_title = "Delete"
        msg_text = f"Are you sure that you want to delete {rslt} and all subobjects ?"
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            self.update_progress(f"Deleting object '{rslt}' ... ", "color=blue, size=12, n=False")
            affected = self.conn.delete_object_and_subobjects(obj_id)
            self.update_progress("done.  ", "color=green, size=12, n=false")
            self.update_progress(f"{str(affected)}  objects deleted !", "color=red, size=12")
        self.update_tree()

    def mnu_analyze_all_triggered(self):
        item = self.ui.tree_lib.currentItem()
        if item == None:
            return
        msg_title = "Warning"
        msg_text = "This operation may take a long time, are you sure you want to continue?"
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        self.update_progress("Started, please wait...", "bold=True, size=20, color=red")
        self.ui.lbl_items_analyzed.setVisible(True)
        obj_id = self.ui.tree_lib.currentItem().data(0,QtCore.Qt.UserRole)
        self._analize_object(obj_id, True)
        self.add_tree_items(item)
        self.update_progress("Finished !!!", "bold=True, size=60, color=red")
        self.ui.lbl_items_analyzed.setVisible(False)

    def _analize_object(self, obj_id, recursion=False):
        objects = self.conn.get_objects_for_parent(obj_id)
        for i in objects:
            if i[6] == 0:
                obj_full_name = self.conn.get_full_name(i[0])
                process = CalculateAndSave()
                process.update_progress.connect(self.update_progress)
                result, r1, r2 = process.calculate_and_save_all_data(False, obj_full_name, parent=i[0])
            else:
                if recursion:
                    children = self.conn.get_objects_for_parent(i[0])
                    for j in children:
                        self._analize_object(j[0])
        self.conn.populate_children()

    def last_text_manager(self, text="", txt_box_to_modify=None):
        if text == "":
            if len(self.last_txt) == 0:
                return ""
            if self.last_txt_idx < 0:
                self.last_txt_idx = 0
                if txt_box_to_modify != None:
                    txt_box_to_modify.setText(self.last_txt[self.last_txt_idx])
                return ""
            elif self.last_txt_idx > (len(self.last_txt)-1):
                self.last_txt_idx = len(self.last_txt)
                if txt_box_to_modify != None:
                    txt_box_to_modify.setText("")
                return ""
        if text == "":
            if txt_box_to_modify == None:
                return self.last_txt[self.last_txt_idx]
            else:
                txt_box_to_modify.setText(self.last_txt[self.last_txt_idx])
        else:
            self.last_txt.append(text)
            if len(self.last_txt) > 200:
                self.last_txt.pop(0)
            self.last_txt_idx = len(self.last_txt)

    def txt_find_return_pressed(self, search_text="", object_id=0):
        if self.ui.txt_find.text() != "":
            self.last_text_manager(self.ui.txt_find.text())
        if search_text == "":
            txt = self.ui.txt_find.text()
        else:
            txt = search_text
        self.update_progress("", "move=end")
        self.update_progress("Search in ", "move=end, size=12, color=red, n=False")
        if object_id == 0:
            search_in = "ALL"
        else:
            search_in = self.conn.get_full_name(object_id)
        self.update_progress(search_in, "size=12, color=#005500, n=false")
        self.update_progress(" for ", "move=end, size=12, color=red, n=False")
        self.update_progress(txt, "size=12, color=#005500")
        if len(txt) < 2:
            self.update_progress("Minimum 2 character for search !", "color=#aa0000, size=12")
            return
        stop_chars = """` ' " | \ %"""
        chrs = stop_chars.split(" ")
        for i in stop_chars:
            if i in txt and i != " ":
                self.update_progress("Folowing characters are not allowed in search [ ", "color=#aa0000, size=12, n=false")
                self.update_progress(stop_chars, "color=#00007f, size=12, n=false, bold=true")
                self.update_progress(" ] !", "color=#aa0000, size=12")
                return
        result = self.conn.find_text(txt, object_id)
        find_list = []
        find_txt = ""
        for i in result:
            find_txt = find_txt + self.conn.get_full_name(i[0]).replace(".", " . ") + "  "
            self.update_progress(find_txt, "size=12, color=#00007f, n=false")
            if i[3] != "":
                find_txt = "Value: " + i[3]
                self.update_progress(find_txt, "size=12, color=#005500, n=false")
            if i[4] != "":
                find_txt = "Arguments: " + i[4]
                self.update_progress(find_txt, "size=12, color=#005500, n=false")
            self.update_progress("", "n=true")
            find_txt = ""
        if len(result) == 0:
            self.update_progress("No matching object found.", "size=12, color=red")
        else:
            self.update_progress(f"Found {str(len(result))} matching objects.", "size=12, color=red")
        cursor = self.ui.txt_info.document().find(txt)
        while not cursor.isNull():
            format =QtGui.QTextCharFormat()
            format.setBackground(QtGui.QColor("yellow"))
            cursor.mergeCharFormat(format)
            cursor = self.ui.txt_info.document().find(txt, cursor)
        

    def tree_lib_item_expanded(self, item):
        self.add_tree_items(item)

    def tree_lib_current_changed(self, cur_index, prev_index):
        if self.ui.tree_lib.currentItem() == None:
            return
        self.ui.tree_lib.scrollToItem(self.ui.tree_lib.currentItem(), QTreeWidget.EnsureVisible)
        self.update_progress("", "cls, n=False")
        item_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        has_children = self.conn.get_objects_for_parent(item_id)
        # has_children, full_name = self.show_item()
        full_name = self.conn.get_full_name(item_id)
        if len(has_children) == 0:
            # Process the data
            self.update_progress("Analyze object:", "color=#00699a, size=8, cursor_freeze=True")
            self.ui.lbl_items_analyzed.setVisible(True)
            process = CalculateAndSave()
            process.update_progress.connect(self.update_progress)
            result, r1, r2 = process.calculate_and_save_all_data(False, full_name, parent=item_id)
            self.conn.populate_children()
            children = self.conn.get_objects_for_parent(item_id)
            self.ui.lbl_items_analyzed.setVisible(False)
            self.update_progress("Finished.", "color=#00699a, size=8, cursor_freeze=True")
            if len(children) > 0:
                result = result - 1
                self.update_progress(f"{result} new children found.", "color=#215541, size=8, cursor_freeze=True")
                self.update_current_item(children)
                self.update_progress("", "new_line=False, cursor=Start")
                self.update_progress(f"Total: {result} new items added to database.", "color=#3a3d0a")
                self.update_progress("", "move=start")
            else:
                self.update_progress("No new children found.", "color=#215541, size=8, cursor_freeze=True")
        self.show_item(no_clear_text=True, at_begining=True)
            
    def update_current_item(self, children=[]):
        item_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        if len(children) == 0:
            children = self.conn.get_objects_for_parent(item_id)
        item = self.ui.tree_lib.currentItem()
        for i in children:
            child = QTreeWidgetItem()
            child.setText(0, i[2])
            child.setData(0, QtCore.Qt.UserRole, i[0])
            item.addChild(child)

    def show_item(self, item_id=0, no_clear_text=False, at_end=True, at_begining=False):
        if item_id == 0:
            item_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        # Get item from database
        item = self.conn.get_object_all(item_id)
        # Show item in txt_info
        if not no_clear_text:
            self.update_progress("", "cls, n=False")
        if at_end:
            self.update_progress("", "move=end, n=false, freeze=True")
        if at_begining:
            self.update_progress("", "move=start, n=false, freeze=True")
        self.update_progress("-"*80, "color=#00557f, size=10, cursor_freeze=True")
        # Name
        size = 30
        if len(item[0][2]) > 24:
            size = 26
        elif len(item[0][2]) > 29:
            size=18
        elif len(item[0][2]) > 34:
            size=14
        elif len(item[0][2]) < 14:
            size = 46
        self.update_progress(item[0][2], f"color=#aa0000, size={size}, bold=True, cursor_freeze=True, new_line=False")
        self.update_progress("", "cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Full name
        self.update_progress("Full object name:", "cursor_freeze=True")
        full_name = self.conn.get_full_name(item_id)
        self.update_progress(full_name, "color=#00007f, size=12, cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Type
        self.update_progress("Type: ", "size=10, n=False, cursor_freeze=True")
        self.update_progress(item[0][5], "color=#0000ff, size=10, cursor_freeze=True")
        # Parent
        self.update_progress("Parent: ", "size=10, n=False, cursor_freeze=True")
        if item[0][1] == 0:
            parent_name = "None"
        else:
            parent_name = self.conn.get_object_all(item[0][1])[0][2]
        self.update_progress(parent_name, "color=red, size=10, cursor_freeze=True")
        # Value
        if item[0][3] != "":
            self.update_progress("Value: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][3], "color=#329649, size=10, cursor_freeze=True")
        # Arguments
        if item[0][4] != "":
            self.update_progress("Arguments: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][4], "color=#329649, size=10, cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Children
        children = self.conn.get_objects_for_parent(item_id)
        if len(children) == 0:
            children_count = "no"
        else:
            children_count = str(len(children))
        self.update_progress(f"Object has {(children_count)} children.", "color=#005500, size=10, cursor_freeze=True")
        txt = ""
        for i in children:
            txt = txt + f"{i[2]}, "
        txt = txt[:-2]
        self.update_progress(txt, "cursor_freeze=True")
        self.update_progress("-"*80, "color=#00557f, size=10, cursor_freeze=True")
        self.update_progress("", "move=start, n=false")
        return children_count, full_name

    def update_tree(self):
        # Clear tree
        self.ui.tree_lib.clear()
        # Populate children 
        self.conn.populate_children()
        root_objects = self.conn.get_objects_for_parent(0)
        parent = self.ui.tree_lib.invisibleRootItem()
        parent.setData(0, QtCore.Qt.UserRole, 0)
        for i in root_objects:
            item = QTreeWidgetItem()
            item.setText(0, i[2])
            item.setData(0, QtCore.Qt.UserRole, i[0])
            parent.addChild(item)
        self.add_tree_items()
        
    def add_tree_items(self, tree_item=None):
        if tree_item is None:
            tree_item = self.ui.tree_lib.invisibleRootItem()
            parent_id = 0
        else:
            parent_id = tree_item.data(0, QtCore.Qt.UserRole)
        objects = self.conn.get_objects_for_parent(parent_id)
        count = 0
        for i in objects:
            if i[0] == tree_item.child(count).data(0, QtCore.Qt.UserRole):
                cur_idx = count
            else:
                print ("Error !")
                for j in range(tree_item.childCount()):
                    if i[0] == tree_item.child(j).data(0, QtCore.Qt.UserRole):
                        cur_idx = j
                        break
            if i[6] != 0:
                self._add_children(tree_item.child(cur_idx))
            count += 1

    def _add_children(self, tree_item):
        if tree_item.childCount() > 0:
            return
        parent_id = tree_item.data(0, QtCore.Qt.UserRole)
        objects = self.conn.get_objects_for_parent(parent_id)
        for i in objects:
            item = QTreeWidgetItem()
            item.setText(0, i[2])
            item.setData(0, QtCore.Qt.UserRole, i[0])
            tree_item.addChild(item)
    
    # def _add_tree_items_OLD_ABANDONED(self, object_list, children_sum, parent=None):
    #     if parent is None:
    #        parent = self.ui.tree_lib.invisibleRootItem()
    #     if type(children_sum) is None or children_sum == 0:
    #         for i in object_list:
    #             main_item = QTreeWidgetItem()
    #             main_item.setText(0, i[2])
    #             main_item.setData(0, QtCore.Qt.UserRole, i[0])
    #             parent.addChild(main_item)
    #         return

    #     for i in object_list:
    #         if i[6] != 0:
    #             main_item = QTreeWidgetItem()
    #             main_item.setText(0, i[2])
    #             main_item.setData(0, QtCore.Qt.UserRole, i[0])
    #             parent.addChild(main_item)
    #             items = self.conn.get_objects_for_parent(i[0])
    #             sum_chld = self.conn.get_sum_childrens_children_for_parent(i[0])
    #             self._add_tree_items(items, sum_chld, main_item)
    #         else:
    #             main_item = QTreeWidgetItem()
    #             main_item.setText(0, i[2])
    #             main_item.setData(0, QtCore.Qt.UserRole, i[0])
    #             parent.addChild(main_item)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == QtCore.Qt.Key_Up:
            self.last_txt_idx = self.last_txt_idx - 1
            if self.ui.txt_lib.hasFocus():
                self.last_text_manager(txt_box_to_modify=self.ui.txt_lib)
            elif self.ui.txt_find.hasFocus():
                self.last_text_manager(txt_box_to_modify=self.ui.txt_find)
        if a0.key() == QtCore.Qt.Key_Down:
            self.last_txt_idx = self.last_txt_idx + 1
            if self.ui.txt_lib.hasFocus():
                self.last_text_manager(txt_box_to_modify=self.ui.txt_lib)
            elif self.ui.txt_find.hasFocus():
                self.last_text_manager(txt_box_to_modify=self.ui.txt_find)
        elif a0.key() == QtCore.Qt.Key_Escape:
            self.ui.txt_info.setText("")
        elif a0.key() == QtCore.Qt.Key_Return and a0.modifiers() == QtCore.Qt.ControlModifier:
            self._show_readme_file()
        return super().keyPressEvent(a0)

    def update_progress(self, event_data_list, t1="", t2=""):
        """event_data is list that contains following string elements:
            ["text for txt_info", "txt_info flags", "progress bar flags"]

        1. text for txt_info widget
            - this is not a required element, it can be blank ("")
            - passed string will be added to text in txt_info
        2. string with flags for txt_info
            - this is a required element, it can be blank ("")
            - flags can be delimited with comma, and here is available flags:
            - 'cls' or 'clear' - clears txt_info text
            - color=hex - text color, if omitted, black color is used (color=#000000)
            - size=integer - font size, if omitted, point size 8 is used (size=8)
            - new_line - True/False, if True go to new line after inserting text (type 'new_line' or just 'n')
            - cursor_freeze - True/False if True do not move cursor after inserting text (type 'cursor_freeze' or 'freeze' or just 'f')
            - cursor - Start/End move cursor to start or end of document after inserting text (type 'cursor' or just 'c')
            - move - Start/End move cursor to start or end and move document view to ensure cursor visibile
            EXAMPLE: "clear, color=#aa0000, size=14" - clear text box, use red color with font size 14
            Note, color can be also in rgb: color=rgb(190,100,200)
        3. ABANDONED string with flags for progress bar (prb_lib)
            - this is not a required element, it can be blank ("")
            - flags can be delimited with comma, and here is available flags:
            - max=integer - maximum value of progress bar, if omitted, value 100 will be used (max=100)
            - val=integer - current value of progress bar, if omitted, value do not change
            - add=integer - increment value, it will increment current value by add value
            - max_add=integer - increment value, it will increment current maximum value by max_add value
            EXAMPLE: "max=150, val=0, add=1" - set maximum to 150 and value to 0, then increase value by 1
        !!! 3. Progress bar is now abandoned, max flag is used to display total analyzed items in label

            Note, if you want, you can put all flags for txt_info and progress bar in one string. EXAMPLE:["info txt", "clear, size=10, max=150, val=0, add=1]
        """
        commands = []
        event_data = []
        # Check if event_data type is string or list
        if type(event_data_list) == str:
            event_data.append(event_data_list)
            if t1 != "":
                event_data.append(t1)
            if t2 != "":
                event_data.append(t2)
        else:
            event_data = event_data_list
        commands.append(["text", event_data[0]])
        # Add flags to commands list
        for i in range(1, len(event_data)):
            comd_list = self._parse_flag_string(event_data[i])
            for j in comd_list:
                commands.append(j)
        # Execute flags
        char_format = QtGui.QTextCharFormat()
        color = QtGui.QColor()
        font = QtGui.QFont()
        no_new_line = False
        cursor_freeze = False
        cursor = self.ui.txt_info.textCursor()
        for i in range(1, len(commands)):
            if commands[i][0] == "color":
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setForeground(color)
            elif commands[i][0] == "size":
                val = int(commands[i][1])
                char_format.setFontPointSize(val)
            elif commands[i][0] == "bold":
                val = commands[i][1]
                if val == "1" or val=="True":
                    font.setBold(True)
                    char_format.setFontWeight(QtGui.QFont.Bold)
            elif commands[i][0] == "cls" or commands[i][0] == "clear":
                self.ui.txt_info.setText("")
            elif commands[i][0] == "max":
                val = commands[i][1]
                # self.ui.prb_lib.setMaximum(val)
                self.ui.lbl_items_analyzed.setText(f"{val} items analyzed.")
            elif commands[i][0] == "max_add":
                val = int(commands[i][1])
                prev_val = self.ui.lbl_items_analyzed.text()
                prev_val = prev_val[:prev_val.find(" ")]
                x = int(prev_val) + val
                # self.ui.prb_lib.setMaximum(x)
                self.ui.lbl_items_analyzed.setText(f"{str(x)} items analyzed.")
            elif commands[i][0] == "val":
                val = int(commands[i][1])
                # self.ui.prb_lib.setValue(val)
            elif commands[i][0] == "add":
                val = int(commands[i][1])
                # val = val + self.ui.prb_lib.value()
                # self.ui.prb_lib.setValue(val)
            elif commands[i][0] == "new_line" or commands[i][0] == "n":
                if commands[i][1].lower() == "false" or commands[i][1] == 0:
                    no_new_line = True
            elif commands[i][0] == "cursor_freeze" or commands[i][0] == "freeze" or commands[i][0] == "f":
                if commands[i][1].lower() == "true" or commands[i][1] == 1:
                    cursor_freeze = True
            elif commands[i][0] == "cursor" or commands[i][0] == "c":
                if commands[i][1].lower() == "begining" or commands[i][1].lower() == "start":
                    cursor.movePosition(QtGui.QTextCursor.Start)
                    cursor_freeze = True
                elif commands[i][1].lower() == "bottom" or commands[i][1].lower() == "end":
                    cursor.movePosition(QtGui.QTextCursor.End)
                    cursor_freeze = True
            elif commands[i][0] == "move":
                if commands[i][1].lower() == "begining" or commands[i][1].lower() == "start":
                    cursor.movePosition(QtGui.QTextCursor.Start)
                    self.ui.txt_info.moveCursor(QtGui.QTextCursor.Start)
                    cursor_freeze = True
                elif commands[i][1].lower() == "bottom" or commands[i][1].lower() == "end":
                    cursor.movePosition(QtGui.QTextCursor.End)
                    self.ui.txt_info.moveCursor(QtGui.QTextCursor.End)
                    cursor_freeze = True
        # Add text to txt_info
        txt = commands[0][1]
        if not no_new_line:
            txt = txt + "\n"
        if not cursor_freeze:
            cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(txt, char_format)
        if not cursor_freeze:
            self.ui.txt_info.moveCursor(QtGui.QTextCursor.End)
        self.ui.txt_info.textCursor().setPosition(cursor.position())
        self.ui.txt_info.ensureCursorVisible()
    
    def _parse_flag_string(self, flag_string):
        result = []
        flag_list = flag_string.split(",")
        for i in flag_list:
            flag_and_value = i.split("=")
            flag_and_value[0] = flag_and_value[0].lower()
            if len(flag_and_value) == 1:
                result.append([flag_and_value[0].strip(), ""])
            else:
                result.append([flag_and_value[0].strip(), flag_and_value[1].strip()])
        return result

    def txt_lib_return_pressed(self):
        # Move cursor in txt_info at end
        self.ui.txt_info.moveCursor(QtGui.QTextCursor.End)
        # Save text in txt_lib. User can repeat this text by pressing arrow UP/DOWN
        if self.ui.txt_lib.text() != "":
            self.last_text_manager(self.ui.txt_lib.text())
        # Check is there text in txt_lib
        if self.ui.txt_lib.text().strip() == "":
            self.ui.txt_lib.setText("")
            return
        # Make progress bar visible and hide checkbox
        # UPDATE: checkbox and progress abandoned, lbl_analyze added
        # self.ui.prb_lib.setVisible(True)
        # self.ui.chk_sub_lib.setVisible(False)
        self.ui.lbl_items_analyzed.setVisible(True)
        # Process the data
        process = CalculateAndSave()
        process.update_progress.connect(self.update_progress)
        # result = process.calculate_and_save_all_data(self.ui.chk_sub_lib.isChecked(), self.ui.txt_lib.text())
        result = process.calculate_and_save_all_data(False, self.ui.txt_lib.text())
        # Set widgets back to normal
        if result[0] != "(C)":
            self.ui.txt_lib.setText(result[0])
        if result[1] != "(C)":
            self.ui.txt_lib.setPlaceholderText(result[1])
        if result[2] != "(C)":
            self.update_progress([result[2], "color=#aa0000"])
        self.ui.txt_lib.setText("")
        self.ui.txt_lib.setPlaceholderText(self.ui.lbl_items_analyzed.text())
        # self.ui.chk_sub_lib.setVisible(True)
        # self.ui.prb_lib.setVisible(False)
        self.ui.lbl_items_analyzed.setVisible(False)
        # Refresh tree
        self.update_tree()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.resize_widgets()
        return super().resizeEvent(a0)

    def resize_widgets(self, x=0):
        # Resize widgets with window
        if self.drag_mode:
            self.ui.ln_sep.move(int(x), self.ui.ln_sep.pos().y())
            self.conn.set_setting_data("main_win_delimiter_line", value_integer=self.ui.ln_sep.pos().x())
        else:
            self.ui.ln_sep.move(int(self.width()*self.scale), self.ui.ln_sep.pos().y())
        self.ui.lbl_lib.resize(self.width(), self.ui.lbl_lib.height())
        self.ui.txt_lib.resize(self.width(), self.ui.txt_lib.height())
        # self.ui.prb_lib.resize(self.width(), self.ui.prb_lib.height())
        self.ui.lbl_info.resize(self.width()-220, self.ui.lbl_info.height())
        self.ui.tree_lib.resize(self.ui.ln_sep.pos().x(), self.height()-115)
        self.ui.txt_info.move(self.ui.ln_sep.pos().x(), self.ui.txt_info.pos().y())
        self.ui.txt_info.resize(self.width()-self.ui.ln_sep.pos().x(), self.height()-115)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        x = a0.localPos().x()
        drag_point = [self.ui.ln_sep.pos().x(), self.ui.ln_sep.pos().x()+1, self.ui.ln_sep.pos().x()+2, self.ui.ln_sep.pos().x()+3]
        if a0.button() == QtCore.Qt.LeftButton and x in drag_point:
            self.drag_mode = True
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        x = a0.localPos().x()
        if self.drag_mode and x > 99 and x < (self.width()-50):
            self.resize_widgets(x)
        return super().mouseMoveEvent(a0)
    
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == QtCore.Qt.LeftButton:
            self.drag_mode = False
            self.scale = self.ui.ln_sep.pos().x()/self.width()
        return super().mouseReleaseEvent(a0)

    def load_setting(self):
        # Get last search text
        result = self.conn.get_setting_data("last_search", get_text=True)
        if type(result) == str:
            rslt = result.split("|")
            self.last_txt = []
            for i in rslt:
                self.last_txt.append(i)
            self.last_txt_idx = len(self.last_txt)
        # Setup window pos and size
        x = self.conn.get_setting_data("main_win_x")
        y = self.conn.get_setting_data("main_win_y")
        w = self.conn.get_setting_data("main_win_w")
        h = self.conn.get_setting_data("main_win_h")
        self.move(x, y)
        self.resize(w, h)
        self.setMinimumSize(200, 300)
        # Setup delimiter line pos
        delim = self.conn.get_setting_data("main_win_delimiter_line")
        if delim < 100:
            delim = 100
        self.ui.ln_sep.move(delim, self.ui.ln_sep.pos().y())
        # Define 'scale' - for calculating relative position of delimiter line in rezise event
        self.scale = delim / self.width()
        # Write ReadMe file in txt_info widget
        if os.path.exists("readme.txt"):
            self._show_readme_file()
            
    def _show_readme_file(self):
        self.ui.txt_info.setText("")
        read_me = open("readme.txt", "r", encoding="utf-8")
        read_me_data = read_me.readlines()
        char_formater = QtGui.QTextCharFormat()
        color = QtGui.QColor()
        font = QtGui.QFont()
        cursor = self.ui.txt_info.textCursor()
        for i in read_me_data:
            color.setNamedColor("#000000")
            font.setBold(False)
            font.setPointSize(8)
            char_formater.setFont(font)
            char_formater.setForeground(color)
            txt = i
            if len(txt) > 2:
                if txt[0:3] == "###":
                    txt = txt[3:]
                    font.setBold(True)
                    color.setNamedColor("#00007f")
                    font.setPointSize(34)
                    char_formater.setFont(font)
                    char_formater.setForeground(color)
                elif txt[0:3] == "## ":
                    txt = txt[3:]
                    color.setNamedColor("#0000ff")
                    font.setPointSize(20)
                    char_formater.setFont(font)
                    char_formater.setForeground(color)
                elif txt[0:3] == " # ":
                    txt = txt[3:]
                    color.setNamedColor("#0000ff")
                    font.setPointSize(16)
                    char_formater.setFont(font)
                    char_formater.setForeground(color)
                elif txt[0:3] == "#  ":
                    txt = txt[3:]
                    color.setNamedColor("#005500")
                    font.setPointSize(16)
                    char_formater.setFont(font)
                    char_formater.setForeground(color)
                elif txt[0:3] == "  #":
                    txt = txt[3:]
                    color.setNamedColor("#aa0000")
                    font.setPointSize(16)
                    char_formater.setFont(font)
                    char_formater.setForeground(color)
                else:
                    color.setNamedColor("#000000")
                    font.setPointSize(12)
                    color.setNamedColor("#000000")
                    char_formater.setFont(font)
                    char_formater.setForeground(color)


            cursor.insertText(txt, char_formater)
            self.ui.txt_info.moveCursor(QtGui.QTextCursor.Start)
        read_me.close()
    
    def save_setting(self, arg):
        # Save last search text
        lst_txt = ""
        for i in self.last_txt:
            lst_txt = lst_txt + i + "|"
        lst_txt = lst_txt[:-1]
        self.conn.set_setting_data("last_search", value_text=lst_txt)
        # Save window pos and size
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        self.conn.set_setting_data("main_win_x", x, "Main Window Geometry")
        self.conn.set_setting_data("main_win_y", y, "Main Window Geometry")
        self.conn.set_setting_data("main_win_w", w, "Main Window Geometry")
        self.conn.set_setting_data("main_win_h", h, "Main Window Geometry")
        # Save delimiter line position
        self.conn.set_setting_data("main_win_delimiter_line", self.ui.ln_sep.pos().x(), "Delimiter line position")


class CalculateAndSave(QThread):
    update_progress = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.obj_list = []  # List of IDs for recursion
        self.list_of_processed_objects = []  # Items to be saved in database
        self.parents_list = []  # List od parents to save
        # Load connection to database
        self.conn = Database()

    def calculate_and_save_all_data(self, recursion, command_text, parent=0):
        self.recursion = recursion
        txt = command_text.lower()
        result = ""
        if txt.find("from") >= 0:
            if txt.find(" import ") == 0:
                return "(C)", "Error. Misssing 'import' in 'from' statement.", "(C)"
            t1 = txt.find("from")
            t2 = txt.find(" import ")
            result = command_text[t1+4:t2].strip() + "." + command_text[t2+8:].strip()
        elif txt.find("import ") >= 0:
            t1 = txt.find("import")
            result = command_text[t1+6:].strip()
        else:
            result = command_text.strip()
        txt = result.split(".")
        if len(txt) > 1:
            from_txt = ""
            object_txt = txt[-1:][0]
            for x in txt[:-1]: from_txt = from_txt + "." + x
            from_txt = from_txt[1:]
            import_line = "        " + "from " + from_txt + " import " + object_txt
        else:
            if len(txt) == 0:
                return "(C)", "Error.", "(C)"
            import_line = "        " + "import " + txt[0]
            object_txt = txt[0]

        self.write_import_line_to_file(import_line)
        # Now we are prepared analyze.py import line and starting to add data to base
        # Add first object to data base
        self._update_progress([f"BEGIN: ", "color=#5500ff, size=8"])
        self.write_object_line_to_file(object_txt)
        result = self.execute_file()
        if result != "Ok":
            self._update_progress([result[0], "color=#ff0000"])
            return "(C)", result[0], result[1]
        # Save data to database
        json_data = self._load_json_file()
        data_to_append = self._make_data_to_append(json_data[0], 0)
        self._update_progress([f"{data_to_append[1]} ({data_to_append[4]})", "color=#00007f, size=8, bold=True, max=1, val=1"])
        if parent == 0:
            d_parent = self.conn.add_object([data_to_append])
        else:
            d_parent = parent
        self.parents_list.append([d_parent, 0, data_to_append[1], data_to_append[2], data_to_append[3], data_to_append[4], data_to_append[1]])
        self.save_data_for_items_in_parents_list()
        self._update_progress([f"END.", "color=#5500ff, size=8"])
        if parent != 0:
            return len(json_data), 0, 0
        else:
            return ["(C)", "(C)", "(C)"]

    def save_data_for_items_in_parents_list(self):
        if len(self.parents_list) == 0:
            return
        items = []
        current_obj = self.parents_list[0]
        self.parents_list.pop(0)
        self.write_object_line_to_file(current_obj[6])
        result = self.execute_file()
        if result != "Ok":
            self._update_progress([result[0], "color=#ff0000"])
            return
        obj_data = self._load_json_file()
        obj_data.pop(0)
        for i in obj_data:
            obj = current_obj[6] + "." + i[2]
            self._update_progress([i[2], "color=#000000, max_add=1"])
            obj_to_append = self._make_data_to_append(i, current_obj[0])
            items.append(obj_to_append)

        self.conn.add_object(items)
        self._update_progress(["", f"add={len(items)}"])
        return

    def save_data_for_items_in_parents_list_OLD_WITH_RECURSION(self):
        if len(self.parents_list) == 0:
            return
        items = []
        current_obj = self.parents_list[0]
        if current_obj[6] in self.obj_list or current_obj[6].count(".") > 10:
            return
        self.obj_list.append(current_obj[6])
        self.parents_list.pop(0)
        self.write_object_line_to_file(current_obj[6])
        result = self.execute_file()
        if result != "Ok":
            self._update_progress([result[0], "color=#ff0000"])
            return
        obj_data = self._load_json_file()
        obj_data.pop(0)
        for i in obj_data:
            obj = current_obj[6] + "." + i[2]
            self.write_object_line_to_file(obj)
            result = self.execute_file()
            if result != "Ok":
                self._update_progress([i[2], "color=#000000, max_add=1"])
                obj_to_append = self._make_data_to_append(i, current_obj[0])
                items.append(obj_to_append)
            else:
                obj_json = self._load_json_file()
                if len(obj_json) > 1:
                    obj_to_append = self._make_data_to_append(i, current_obj[0])
                    parent_id = self.conn.add_object([obj_to_append])
                    self.parents_list.append([parent_id, current_obj[0], obj_to_append[1], obj_to_append[2], obj_to_append[3], obj_to_append[4], obj])
                    self._update_progress([obj_to_append[1], "color=#0000ff, size=8, max_add=1, add=1"])
                else:
                    self._update_progress([i[2], "color=#000000, max_add=1"])
                    obj_to_append = self._make_data_to_append(i, current_obj[0])
                    items.append(obj_to_append)

        self.conn.add_object(items)
        self._update_progress(["", f"add={len(items)}"])
        if self.recursion:
            self.save_data_for_items_in_parents_list()
        else:
            return

    def _make_data_to_append(self, data_from_file, parent_id):
        d_parent = parent_id
        d_name = data_from_file[2]
        d_name_check = d_name.split(".")
        if len(d_name_check) > 1:
            d_name = d_name_check[-1:][0]
        d_value = data_from_file[1]
        d_arg = ""
        d_type = data_from_file[0]
        if d_type == 0:
            d_type_name = "Object"
            d_arg = d_value
            d_value = ""
        elif d_type == 1:
            d_type_name = "Class"
        elif d_type == 2:
            d_type_name = "Module"
        elif d_type == 3:
            d_type_name = "Method"
        elif d_type == 4:
            d_type_name = "Property"
        elif d_type == 5:
            d_type_name = "Function"
        elif d_type == 6:
            d_type_name = "Constant"
        elif d_type == 7:
            d_type_name = "Unclassified"

        data_to_append = [d_parent, d_name, d_value, d_arg, d_type_name]
        return data_to_append

    def _load_json_file(self):
        with open("result.txt", "r", encoding="utf-8") as a:
            data = json.load(a)
        return data

    def execute_file(self):
        try:
            import analyze
            importlib.reload(analyze)
            a = analyze.do_it()
        except Exception as e:
            txt = str(e) + "\n"
            txt = txt + str(type(e)) + "\n" + str(dir(e))
            return str(e), txt
        return "Ok"

    def write_import_line_to_file(self, import_line):
        # First load file to module var
        a = open("analyze.py", "r", encoding="utf-8")
        module = a.readlines()
        a.close()
        # Find last line index
        end_line = len(module)-1
        # Change module var
        module[end_line-1] = import_line + "\n"
        # Save changed file
        a = open("analyze.py", "w", encoding="utf-8")
        a.writelines(module)
        a.close()


    def write_object_line_to_file(self, object_to_exam):
        # First load file to module var
        a = open("analyze.py", "r", encoding="utf-8")
        module = a.readlines()
        a.close()
        # Find last line index
        end_line = len(module)-1
        # Change module var
        module[end_line] = f"        i = IspitajObjekat({object_to_exam})"
        # Save changed file
        a = open("analyze.py", "w", encoding="utf-8")
        a.writelines(module)
        a.close()
    
    def _update_progress(self, update_progress_list_of_strings):
        self.update_progress.emit(update_progress_list_of_strings)
        QCoreApplication.processEvents()

    



    
class Database():
    """ Connection to SQLite database 'lib_analyze.db'
    Provides data from database:
    - Table 'object' >> all analyzed objects
    - Table 'setting' >> application setting
    """
    def __init__(self):
        my_database = "lib_analize.db"
        # Check is database exists and make one if not
        if not os.path.exists(my_database):
            a = open(my_database, "w")
            a.close()
        self.conn = sqlite3.connect(my_database)
        self.cur = self.conn.cursor()
        self._check_is_tables_exists()
        self.some_list = []  # List for various purposes

    def complete_list_with_parents_until_root(self, objects_list):
        add_to = self._create_add_list_for_parents(objects_list)
        for i in add_to:
            objects_list.append(i)
        return objects_list

    def _create_add_list_for_parents(self, object_list):
        o = object_list.copy()
        add_to = []
        ids = []
        ids.append(0)
        for i in o:
            ids.append(i[0])
        counter = 0
        while counter != len(o):
            if o[counter][1] in ids:
                o.pop(counter)
            else:
                counter += 1
        ids = []
        for i in o:
            if i[1] not in ids:
                result = self._get_parent_object_until_root(i[0])
                for j in result:
                    if j[0] not in ids:
                        ids.append(j[0])
                        add_to.append(j)
        return add_to

    def _get_parent_object_until_root(self, object_id):
        cur_id = object_id
        go_loop = True
        parent_list = []
        parent_list.copy()
        while go_loop:
            result = self.get_object_all(object_id=cur_id)
            parent_list.append(result)
            if result[0][1] == 0:
                go_loop = False
            else:
                cur_id = result[0][1]
        parent_list.pop(0)
        parent_list.sort()
        return parent_list

    def populate_id_list_with_recur_names(self, ids):
        id_list_with_names = []
        for i in ids:
            result = self.get_full_name(i)
            id_list_with_names.append([i, result])
        return id_list_with_names

    def get_full_name(self, object_id):
        full_name = ""
        cur_id = object_id
        go_loop = True

        while go_loop:
            result = self.get_object_all(object_id=cur_id)
            full_name = full_name + result[0][2] + "."
            if result[0][1] == 0:
                go_loop = False
            else:
                cur_id = result[0][1]
        full_name = full_name[:-1]
        a = full_name.split(".")
        full_name = ""
        c = len(a) - 1
        while c >= 0:
            full_name = full_name + a[c]  + "."
            c -= 1
        full_name = full_name[:-1]
        return full_name

    def get_object_all(self, object_id=0, filter="", filter_exact_match=False):

        if object_id == 0 and filter == "":
            q = "SELECT * FROM object ;"
            self.cur.execute(q)
        elif object_id == 0 and filter != "" and filter_exact_match == False:
            q = f"SELECT * FROM object WHERE name LIKE '%{filter}%' COLLATE NOCASE ;"
            self.cur.execute(q)
        elif object_id == 0 and filter != "" and filter_exact_match == True:
            q = f"SELECT * FROM object WHERE name = '{filter}' ;"
            self.cur.execute(q)
        else:
            q = f"SELECT * FROM object WHERE object_id = {str(object_id)} ;"
            self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def get_setting_data(self, function_name, get_text=False):
        q = f"SELECT * FROM setting WHERE function = '{function_name}' ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) > 0:
            if get_text:
                return result[0][3]
            else:
                return result[0][2]
        else:
            if get_text:
                return ""
            else:
                return 0

    def set_setting_data(self, function_name, value_integer=0, value_text=""):
        if self._is_setting_exists(function_name):
            q = f"UPDATE setting SET val = {str(value_integer)}, val_txt = ? WHERE function = '{function_name}' ;"
        else:
            q = f"INSERT INTO setting(function, val, val_txt) VALUES ('{function_name}', {str(value_integer)}, ?) ;"
        self.cur.execute(q, (value_text,))
        self.conn.commit()

    def _check_is_tables_exists(self):
        q = "CREATE TABLE IF NOT EXISTS object (object_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, parent INTEGER, name TEXT, value TEXT, type TEXT (50));"
        self.cur.execute(q)
        self.conn.commit()
        q = "CREATE TABLE IF NOT EXISTS setting (setting_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, function TEXT (100) NOT NULL, val INTEGER, val_txt TEXT (255));"
        self.cur.execute(q)
        self.conn.commit()
    
    def _is_setting_exists(self, function_name):
        q = f"SELECT * FROM setting WHERE function = '{function_name}' ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) > 0:
            return True
        else:
            return False

    def add_object(self, data_list):
        for data in data_list:
            q = f"""INSERT INTO 
                        object(
                            parent,
                            name,
                            value,
                            arguments,
                            type, 
                            children)
                    VALUES  (
                            {str(data[0])},
                            '{data[1]}',
                            ?,
                            ?,
                            '{data[4]}',
                            0)
                            ;
            """
            self.cur.execute(q, (data[2], data[3]))
        self.conn.commit()
        if len(data_list) == 1:
            result = self.cur.lastrowid
            return result
        else:
            return 0

    def get_unique_parent_objects(self):
        q = "SELECT * FROM object WHERE object_id IN (SELECT parent FROM object GROUP BY parent) ORDER BY parent ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def get_objects_for_parent(self, parent_id):
        q = f"SELECT object_id, parent, name, value, arguments, type, children, name||' - '||type||'  '||value||arguments FROM object WHERE parent = {str(parent_id)} ORDER BY name COLLATE NOCASE;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def get_sum_childrens_children_for_parent(self, parent_id):
        q = f"SELECT SUM(children) FROM object WHERE parent = {str(parent_id)} ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result[0][0]

    def populate_children(self):
        q = """UPDATE object 
                SET children = COALESCE((SELECT child_num 
                FROM (SELECT parent AS afected_parent, COUNT(object_id) AS child_num 
                      FROM object 
                      GROUP BY parent) 
                WHERE afected_parent = object_id), 0) ;"""
        self.cur.execute(q)
        self.conn.commit()

    def find_text(self, text_to_find, object_id=0):
        if object_id == 0:
            result = self._find_text(text_to_find)
        else:
            self.some_list = []
            self._find_text_for_object_id(text_to_find.lower(), object_id)
            result = self.some_list
        return result

    def _find_text_for_object_id(self, txt, obj_id):
        res1 = self.get_object_all(obj_id)
        search_pool = f"{res1[0][2]} {res1[0][3]} {res1[0][4]}".lower()
        if search_pool.find(txt) >= 0:
            self.some_list.append(res1[0])
        res2 = self.get_objects_for_parent(res1[0][0])
        for i in res2:
            search_pool = f"{i[2]} {i[3]} {i[4]}".lower()
            if search_pool.find(txt) >= 0:
                self.some_list.append(i)
            if i[6] !=0:
                self._find_text_for_object_id(txt, i[0])

    def _find_text(self, txt):
        q = f"""SELECT 
                *
            FROM 
                object 
            WHERE 
                name LIKE '%{txt}%' OR
                value LIKE '%{txt}%' OR
                arguments LIKE '%{txt}%'
                COLLATE NOCASE
            ORDER BY
                parent, name
                ;
            """
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def delete_object_and_subobjects(self, object_id):
        self.some_list = []
        self._delete_object_and_subobjects(object_id)
        for i in self.some_list:
            q = f"DELETE FROM object WHERE object_id = {str(i)} ;"
            self.cur.execute(q)
        self.conn.commit()
        self.populate_children()
        return len(self.some_list)

    def _delete_object_and_subobjects(self, object_id):
        self.some_list.append(object_id)
        res = self.get_objects_for_parent(object_id)
        for i in res:
            if i[6] != 0:
                self._delete_object_and_subobjects(i[0])
            else:
                self.some_list.append(i[0])
        


app = QtWidgets.QApplication(sys.argv)
lib_anlyzer = Analyzer()
lib_anlyzer.start_me()

app.exec_()

