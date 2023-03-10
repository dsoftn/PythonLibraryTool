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
    """The main application class.
    Handles all events related to the graphical user interface.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_txt = []
        self.last_txt_idx = 0
        self.drag_mode = False  # If true then user resize widgets in progress
        self.find_list = []  # List helps to loacate searched item in tree
        self.pages = []  # Info box pages
        self.pages_current = 0  # Current page 
        self.pages_number = 20  # Number of pages to keep in memory
        self.info_char_format = QtGui.QTextCharFormat()
        self.info_color = QtGui.QColor()
        self.info_font = QtGui.QFont()
        # Setup GUI
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # Load connection to database
        self.conn = Database()
        # Hide progress bar !!! ABANDONED - now hide lbl_items_analyzed
        # self.ui.prb_lib.setVisible(False)
        self.ui.lbl_items_analyzed.setVisible(False)

    def start_me(self):
        """The main method of the class that is called after the instance is created.
        """
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
        self.ui.txt_info.selectionChanged.connect(self.txt_info_selection_changed)
        self.ui.btn_nav_left.clicked.connect(self.btn_nav_left_click)
        self.ui.btn_nav_right.clicked.connect(self.btn_nav_right_click)
        self.ui.btn_nav_end.clicked.connect(self.btn_nav_end_click)
        self.ui.btn_net_doc.clicked.connect(self.btn_net_doc_click)
        # Update tree
        self.update_tree()
        self.update_navigation_buttons()
        # Show window
        self.show()


    def btn_net_doc_click(self):
        """TEST"""
        box = TxtBoxPrinter(self.ui.txt_info)
        box.print_text(formating_flags="cls")
        box.print_text("Proba da vidimo kako radi sa default podesavanjima")
        box.print_text("Ovo je velicina 24, boja crvena, sve GLOBAL", "@size=24, @color=red")
        box.print_text("Boja je plava za ovu liniju", "color=blue")
        box.print_text("Boja je zelena i velicina 14 za ovu liniju", "color=green, size=14")
        box.print_text("Nema Flag, vraca se na GLOBAL", "")
        box.print_text("Na pocetak dokumenta", "move=start")
        box.print_text("Font Roboto Mono Boja tamno plava", "font=Roboto Mono, color= darkblue")
        box.print_text("Font Blackadder ITC Boja tamno plava", "font=Blackadder ITC, color= darkblue")
        box.print_text("Na kraj dokumenta sa Roboto Mono fontom", "move=end, @font=Courier, @size=12, @color=black")
        box.print_text("for i in result:")
        box.print_text("    ovo je sa tab-om")
        box.print_text("    ovo je sa razmakom")
        box.print_text("    iiiiiiiiii 10xi")
        box.print_text("    MMMMMMMMMM 10xM")
        box.print_text("Na kraj dokumenta sa Courier fontom", "move=end, @font=Courier, @size=12, @color=black")
        box.print_text("for i in result:")
        box.print_text("    ovo je sa tab-om")
        box.print_text("    ovo je sa razmakom")
        box.print_text("    iiiiiiiiii 10xi")
        box.print_text("    MMMMMMMMMM 10xM")
        box.print_text("Na kraj dokumenta sa System Fixed fontom", "move=end, @font=fixed, @size=12, @color=darkblue")
        box.print_text("for i in result:", "@bc=black, @fc=yellow")
        box.print_text("    ovo je sa tab-om","size=16")
        box.print_text("    ovo je sa razmakom","size = 8")
        box.print_text("    iiiiiiiiii 10xi","size=10")
        box.print_text("    MMMMMMMMMM 10xM")
        box.print_text("", "@background color=white")
        box.print_text("Crni deo ", "color=black, @size-20, @font=Verdana, n=0")
        box.print_text("pa onda crveni ", "c=red, n=false")
        box.print_text("BOLD ", "bold=yes, new line = NO")
        box.print_text("plavo na kraju", "color=darkblue, underline=true")
        box.print_text("HEADER", "size = 60, color=darkgreen, font = Elephant, move=top")

        if box.flags_has_errors():
            box.print_text("Errors:", "size=20, color=black")
        result = box.get_flag_error_list()
        for i in box.get_flag_error_list():
            box.print_text(f"Flag: {i[0]}   Error: {i[1]}", "size=16, color=Darkred")

    def add_info_box_page(self, page: str = ""):
        """Adds an Info box page.
        Args:
            page (str): The page in HTML format that is added, if it is omitted, the current page is taken from the Info box
        """
        if page != "":
            self.pages.append(page)
        else:
            self.pages.append(self.ui.txt_info.toHtml())
        if len(self.pages) > self.pages_number:
            self.pages.pop(0)
        self.pages_current = len(self.pages) - 1
        self.update_navigation_buttons()

    def btn_nav_left_click(self):
        """Moves the current page pointer by -1
        """
        if self.pages_current <= 0:
            return
        self.pages_current -= 1
        self.show_current_page()
        self.update_navigation_buttons()
    
    def btn_nav_right_click(self):
        """Moves the current page pointer by 1
        """
        if self.pages_current >= len(self.pages) - 1:
            return
        self.pages_current += 1
        self.show_current_page()
        self.update_navigation_buttons()

    def btn_nav_end_click(self):
        """Moves the current page pointer to end
        """
        self.pages_current = len(self.pages) - 1
        if self.pages_current < 0:
            self.pages_current = 0
        self.show_current_page()
        self.update_navigation_buttons()

    def show_current_page(self):
        """Displays the current page in the Info box
        """
        if len(self.pages) <= 0:
            return
        self.ui.txt_info.setText("")
        self.ui.txt_info.setHtml(self.pages[self.pages_current])

    def update_navigation_buttons(self):
        """Sets navigation buttons enabled/disabled depending on the position of the current page.
        """
        self.ui.btn_nav_left.setDisabled(False)
        self.ui.btn_nav_right.setDisabled(False)
        self.ui.btn_nav_end.setDisabled(False)
        if self.pages_current <= 0:
            self.ui.btn_nav_left.setDisabled(True)
        if self.pages_current >= len(self.pages) - 1:
            self.ui.btn_nav_right.setDisabled(True)
            self.ui.btn_nav_end.setDisabled(True)

    def txt_info_selection_changed(self):
        """Changed the selected text in the Info text box.
        Checking whether the name of an object exists in the current line of text, if so, it is checked whether that object exists in the database.
        If the object is found, the 'Find' box is displayed, which allows the user to find that object in the 'Tree view'.
        """
        cursor = self.ui.txt_info.textCursor()
        selection = cursor.selectedText()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        document = self.ui.txt_info.document()
        block = document.findBlock(start).text()
        block = block.strip()
        if block.find("  ") >= 0:
            block = block[:block.find("  ")]
        obj_comp = [x.strip() for x in block.split(".")]
        obj_list = []
        for i in obj_comp:
            obj_list.append(i)
            if i == selection:
                break
        result = self._find_if_exist(obj_list)
        if result is None:
            self.ui.frm_find.setVisible(False)
            self.find_list = []
            return
        self.ui.frm_find.setVisible(True)
        self.find_list = result
        self.update_find_frm()

    def update_find_frm(self):
        """Fills in the data in the 'Find' frame for the object currently selected in the Info box.
        """
        txt = ""
        for i in self.find_list:
            txt = txt + i[1] + "."
        txt = txt[:-1]
        self.ui.lbl_find_full_name.setText(txt)
        txt_main = self.find_list[len(self.find_list)-1][1]

        font = self.ui.lbl_find.font()
        size = font.pointSize()
        fm = QtGui.QFontMetrics(font)
        while fm.width(txt_main) > self.ui.lbl_find.width()-20:
            size -= 1
            font.setPointSize(size)
            fm = QtGui.QFontMetrics(font)
        self.ui.lbl_find.setFont(font)
        self.ui.lbl_find.setText(txt_main)
    
    def frm_find_click(self):
        """Finds the object in the 'Tree' view.
        """
        item = None
        parent = self.ui.tree_lib.invisibleRootItem()
        result = self._find_item(parent, 0)
        self.ui.frm_find.setVisible(False)
        self.ui.tree_lib.setCurrentItem(result)
        self.ui.tree_lib.setFocus()
        result.setSelected(True)

    def _find_item(self, parent: QtWidgets.QTreeWidgetItem, index: int) -> QtWidgets.QTreeWidgetItem:
        """It uses data from the 'self.find_list' list and finds an item in the Tree view by recursively calling itself.
        Args:
            parent (QTreeViewItem): The parent item from which the search starts, usually root
            index (int): This argument is used by the function itself in a recursive call, pass integer 0
        Returns:
            QTreeViewItem: Required item
        """
        parent.setExpanded(True)
        for i in range(parent.childCount()):
            item = parent.child(i)
            if item.data(0, QtCore.Qt.UserRole) == self.find_list[index][0]:
                if index == len(self.find_list)-1:
                    return item
                else:
                    return self._find_item(item, index + 1)

    def _find_if_exist(self, object_list: list) -> list:
        """Finds an object in the database.
        Args:
            object_list (list): List of parts of the full name of the object detected in the Info box
        Returns:
            list: If the object is found it returns a list, if not it returns None
        """
        if len(object_list) == 0:
            return None
        if len(object_list[0]) == 0:
            return None
        full_name = ".".join(object_list)
        all_objects = self.conn.get_objects_with_name(object_list[-1])
        for i in all_objects:
            f_name_list = self.conn.get_full_name(i[0], get_list_with_id_and_name=True)
            f_name = ""
            for j in f_name_list:
                f_name = f_name + j[1] + "."
            f_name = f_name[:-1]
            if f_name == full_name:
                return f_name_list
        return None

    def tree_custom_menu_request(self, pos):
        self.mnu_tree_menu.exec_(self.ui.tree_lib.mapToGlobal(pos))

    def create_custom_menu(self):
        """Creates a custom menu for the Tree view."""
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
        """Search within the selected item in the Tree view.
        It displays an InputBox and expects the input of the requested data.
        """
        if self.ui.tree_lib.currentItem == None:
            self.update_progress("No current object. Please select object before operation can be performed.", "color=red, size=10")
        msg_title = "Search"
        msg_text = f"Search in {self.ui.tree_lib.currentItem().text(0)} for string: "
        msg_def_text = self.ui.txt_find.text()
        result, ok = QtWidgets.QInputDialog.getText(self, msg_title, msg_text, text=msg_def_text)
        if ok and result != "":
            self.txt_find_return_pressed(search_text=result, object_id=self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole))

    def mnu_delete_triggered(self):
        """Deletes the selected Item and all its sub-items.
        """
        if self.ui.tree_lib.currentItem == None:
            self.update_progress("No current object. Please select object before operation can be performed.", "color=red, size=10")
        item = self.ui.tree_lib.currentItem()
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
            self._remove_children(item)
        else:
            return

    def mnu_analyze_all_triggered(self):
        """Analyzes all objects starting from the selected object in depth.
        """
        item = self.ui.tree_lib.currentItem()
        if self.ui.tree_lib.currentItem == None:
            self.update_progress("No current object. Please select object before operation can be performed.", "color=red, size=10")
        msg_title = "Warning"
        msg_text = "This operation may take a long time, are you sure you want to continue?"
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        self.update_progress("Started, please wait...", "bold=True, size=20, color=red")
        self.ui.lbl_items_analyzed.setVisible(True)
        obj_id = item.data(0,QtCore.Qt.UserRole)
        # First delete object and children
        affected =  self.conn.delete_object_and_subobjects(obj_id, delete_children_only=True)
        # Analyze object, add children, with recursion
        self._analize_object(obj_id, True)
        # Remove sub objects
        self._remove_children(item, protected_item=item)
        children_to_add = self.conn.get_objects_for_parent(obj_id)
        for i in children_to_add:
            item_to_add = QTreeWidgetItem()
            item_to_add.setText(0, i[2])
            item_to_add.setData(0, QtCore.Qt.UserRole, i[0])
            item.addChild(item_to_add)
        self.add_tree_items(item)
        # Calculate number of new object added
        total = self.conn.get_total_number_of_children_in_deep(obj_id) - affected
        self.update_progress(f"{total} new objects added.", "bold=True, size=12, color=blue")
        self.update_progress("Finished !!!", "bold=True, size=60, color=red")
        self.ui.lbl_items_analyzed.setVisible(False)

    def _remove_children(self, item: QtWidgets.QTreeWidgetItem, protected_item: QtWidgets.QTreeWidgetItem = None):
        """Deletes all sub-items in the Tree view in depth.
        Args:
            item (QTreeWidgetItem): Item from which the deletion starts
            protected_item (QTreeWidgetItem): An item that is protected from deletion
        """
        while item.childCount() > 0:
            child = item.child(0)
            self._remove_children(child)
        if item != protected_item:
            parent = item.parent()
            if parent == None:
                self.ui.tree_lib.takeTopLevelItem(self.ui.tree_lib.indexOfTopLevelItem(item))
            else:
                parent.removeChild(item)

    def _analize_object(self, obj_id: int, recursion: bool = False):
        """Analyzes all objects starting from obj_id.
        The function calls itself recursively until it has analyzed all objects in depth.
        Args:
            obj_id (int): The object from which the analysis starts
            recursion (bool): If it is true, the function will recursively call itself and analyze everything in depth
        """
        process = CalculateAndSave()
        process.update_progress.connect(self.update_progress)
        
        obj_full_name = self.conn.get_full_name(obj_id, add_virtual_name=True)
        result, r1, r2 = process.calculate_and_save_all_data(False, obj_full_name, obj_id)
        children = self.conn.get_objects_for_parent(obj_id)
        for i in children:
            child_full_name = self.conn.get_full_name(i[0], add_virtual_name=True)
            result, r1, r2 = process.calculate_and_save_all_data(False, child_full_name, parent=i[0])
            childs_children = self.conn.get_objects_for_parent(i[0])
            if recursion:
                for j in childs_children:
                    self._analize_object(j[0])
        self.conn.populate_children()

    def last_text_manager(self, text: str = "", txt_box_to_modify: QtWidgets.QLineEdit = None):
        """By pressing the up or down arrows, the user returns the previously entered text.
        """
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

    def txt_find_return_pressed(self, search_text: str = "", object_id: int = 0):
        """Searches for objects that contain the required string in the name, value or arguments.
        The search results are printed in the Info box.
        Args:
            search_text (str): The string to search for
            object_id (int): Optional, id of the object from which the search starts, 0 = all 
        """
        if self.ui.txt_find.text() != "":
            self.last_text_manager(self.ui.txt_find.text())
        if search_text == "":
            txt = self.ui.txt_find.text()
        else:
            txt = search_text
        self.update_progress("", "cls")
        self.update_progress("Search in ", "move=end, size=12, color=red, n=False")
        if object_id == 0:
            search_in = "ALL"
        else:
            search_in = self.conn.get_full_name(object_id)
        self.update_progress(search_in, "size=12, color=#005500, n=false")
        self.update_progress(" for ", "move=end, size=12, color=red, n=False")
        self.update_progress(txt, "size=12, color=#005500")
        self.update_progress("", "size=12")
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
                find_txt = i[3]
                if len(find_txt) > 50:
                    self.update_progress("", "size=12")
                    self.update_progress("Value: ", "size=12")
                    self.update_progress(find_txt, "size=6, color=#005500")
                else:
                    self.update_progress("Value: ", "size=12, n=false")
                    self.update_progress(find_txt, "size=12, color=#005500")
            if i[4] != "":
                find_txt = i[4]
                if len(find_txt) > 50:
                    self.update_progress("", "size=12")
                    self.update_progress("Arguments: ", "size=12")
                    self.update_progress(find_txt, "size=6, color=#005500")
                else:
                    self.update_progress("Arguments: ", "size=12, n=false")
                    self.update_progress(find_txt, "size=12, color=#005500")
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
        self.add_info_box_page()

    def tree_lib_item_expanded(self, item):
        self.add_tree_items(item)

    def tree_lib_current_changed(self, cur_index, prev_index):
        """Analyzes the currently selected object.
        """
        if self.ui.tree_lib.currentItem() == None:
            return
        self.ui.tree_lib.scrollToItem(self.ui.tree_lib.currentItem(), QTreeWidget.EnsureVisible)
        self.update_progress("", "cls, n=False")
        item_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        has_children = self.conn.get_objects_for_parent(item_id)
        # has_children, full_name = self.show_item()
        full_name = self.conn.get_full_name(item_id, add_virtual_name=True)
        process = CalculateAndSave()
        process.update_progress.connect(self.update_progress)
        if len(has_children) == 0:
            # Process the data
            self.update_progress("Analyze object:", "color=#00699a, size=8, cursor_freeze=True")
            self.ui.lbl_items_analyzed.setVisible(True)
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
        self.update_progress("Performing a deep analysis...", "color=darkblue, size=8, cursor_freeze=True")
        process.combine_names_and_analyze(item_id)
        self.show_item(no_clear_text=True, at_begining=True)
        self.add_info_box_page()
            
    def update_current_item(self, children: list = []):
        """Adds to the current item its sub-items from the database.
        Args:
            children (list): The list of sub-items to add, if empty, finds the list from the database
        """
        item_id = self.ui.tree_lib.currentItem().data(0, QtCore.Qt.UserRole)
        if len(children) == 0:
            children = self.conn.get_objects_for_parent(item_id)
        item = self.ui.tree_lib.currentItem()
        for i in children:
            child = QTreeWidgetItem()
            child.setText(0, i[2])
            child.setData(0, QtCore.Qt.UserRole, i[0])
            item.addChild(child)

    def show_item(self, item_id: int = 0, no_clear_text: bool = False, at_end: bool = True, at_begining: bool = False):
        """Displays the object in the Info box.
        Args:
            item_id (int): Object ID
            no_clear_text (bool): Clearing the contents of the Info box before printing data about the object
            at_end (bool): Start writing at the end of the text in the Info box
            at_begining (bool): Start writing at the beginning of the text in the Info box
        """
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
        size = 20
        max_width = self.ui.txt_info.contentsRect().width() - 120
        font = self.ui.txt_info.font()
        font.setPointSize(size)
        fm = QtGui.QFontMetrics(font)
        while fm.width(item[0][2]) < max_width and size < 74:
            size += 1
            font.setPointSize(size)
            fm = QtGui.QFontMetrics(font)
        size -= 1
        self.update_progress(item[0][2], f"color=#aa0000, size={size}, bold=True, cursor_freeze=True, new_line=False, font_name=Calibri")
        self.update_progress("", "cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Full name
        self.update_progress("Full object name: ", "cursor_freeze=True, n=false, size=10")
        full_name = self.conn.get_full_name(item_id)
        self.update_progress(full_name, "color=#00007f, size=12, cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Type
        self.update_progress("Type: ", "size=10, n=False, cursor_freeze=True")
        self.update_progress(item[0][5], "color=#0000ff, size=10, cursor_freeze=True, n=false")
        if item[0][13] != "" and item[0][13] != None:
            self.update_progress(".  ", "color=#0000ff, size=10, cursor_freeze=True, n=false")
            self.update_progress("Member of ", "size=10, cursor_freeze=True, n=false")
            self.update_progress(item[0][13], "color=#0000ff, size=10, cursor_freeze=True")
        else:
            self.update_progress("", "size=10, cursor_freeze=True")
        # Parent
        self.update_progress("Parent: ", "size=10, n=False, cursor_freeze=True")
        if item[0][1] == 0:
            parent_name = "None"
        else:
            parent_name = self.conn.get_object_all(item[0][1])[0][2]
        self.update_progress(parent_name, "color=red, size=10, cursor_freeze=True")
        # Python object
        if item[0][10] != "":
            self.update_progress("This is a built-in Python object: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][10], "color=Blue, size=10, cursor_freeze=True")
        # Docstrings
        if item[0][7] != "":
            self.update_progress("DocString: ", "size=10, n=False, cursor_freeze=True")
            if len(item[0][7]) > 100:
                self.update_progress("", "size=10, cursor_freeze=True")
            self.update_progress(item[0][7], "color=darkgreen, size=10, cursor_freeze=True")
        # Value
        if item[0][3] != "":
            self.update_progress("Value: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][3], "color=#329649, size=10, cursor_freeze=True")
        # Arguments
        if item[0][4] != "":
            self.update_progress("Arguments: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][4], "color=#329649, size=10, cursor_freeze=True")
        self.update_progress("", "cursor_freeze=True")
        # Filename
        if item[0][11] != "":
            self.update_progress("Filename: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][11], "color=#556878, size=10, cursor_freeze=True")
        # Module
        if item[0][12] != "":
            self.update_progress("Module: ", "size=10, n=False, cursor_freeze=True")
            self.update_progress(item[0][12], "color=#556878, size=10, cursor_freeze=True")
        # Mro
        if item[0][9] != "":
            self.update_progress("MRO - Information about inheritance hierarchy: ", "size=10, n=False, cursor_freeze=True")
            mro = item[0][9].split(",")
            if len(mro) == 1 and mro[0] == "object":
                self.update_progress("Not defined.", "color=blue, size=10, cursor_freeze=True")    
            else:                
                for i in mro:
                    self.update_progress(item[0][9], "color=blue, size=10, cursor_freeze=True")
        # Source Code
        if item[0][8] != "":
            self.update_progress("Source Code: ", "size=18, cursor_freeze=True")
            self.update_progress(item[0][8], "color=DarkGreen, size=10, cursor_freeze=True")
        # Children
        children = self.conn.get_objects_for_parent(item_id)
        if len(children) == 0:
            children_count = "no"
        else:
            children_count = str(len(children))
        self.update_progress(f"Object has {(children_count)} children.", "size=10, cursor_freeze=True")
        txt = ""
        for i in children:
            txt = txt + f"{i[2]}, "
        txt = txt[:-2]
        self.update_progress(txt, "cursor_freeze=True")
        self.update_progress("-"*80, "color=#00557f, size=10, cursor_freeze=True")
        self.update_progress("", "move=start, n=false")
        return children_count, full_name

    def update_tree(self):
        """Deletes the contents of the Tree view and reloads the data from the database.
        """
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
        
    def add_tree_items(self, tree_item: QtWidgets.QTreeWidgetItem = None):
        """Adds to the Tree view sub-items for a specified item.
        Args:
            tree_item (QTreeWidgetItem): Item for which sub-items are added
        """
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
                for j in range(tree_item.childCount()):
                    if i[0] == tree_item.child(j).data(0, QtCore.Qt.UserRole):
                        cur_idx = j
                        break
            if i[6] != 0:
                self._add_children(tree_item.child(cur_idx))
            count += 1

    def _add_children(self, tree_item: QtWidgets.QTreeWidgetItem):
        """Adds items from the database to the Tree view.
        Args:
            tree_item (QTreeWidgetItem): Item for which data is added
        """
        if tree_item.childCount() > 0:
            return
        parent_id = tree_item.data(0, QtCore.Qt.UserRole)
        objects = self.conn.get_objects_for_parent(parent_id)
        for i in objects:
            item = QTreeWidgetItem()
            item.setText(0, i[2])
            item.setData(0, QtCore.Qt.UserRole, i[0])
            tree_item.addChild(item)

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
            self.ui.frm_find.setVisible(False)
            self.ui.txt_info.setText("")
        elif a0.key() == QtCore.Qt.Key_Return and a0.modifiers() == QtCore.Qt.ControlModifier:
            self._show_readme_file()
        elif a0.key() == QtCore.Qt.Key_S and a0.modifiers() == QtCore.Qt.ControlModifier:
            self.add_info_box_page()
        return super().keyPressEvent(a0)

    def update_progress(self, event_data_list: list, t1: str = "", t2: str = ""):
        """Prints the text in the Info box.
        Args:
            event_data_list (list): event_data is list that contains following string elements:
                ["text for Info Box", "Flags", "Progress bar flags"]
            t1 (str) AND t2 (str): The function expects as an argument a list containing two or optionally three strings. These arguments allow the function to be passed two or three strings without passing a list.

        1. text for txt_info widget
            - this is a required element, it can be blank ("")
            - passed string will be added to text in txt_info
        
        2. string with flags for txt_info
              this is a required element, it can be blank ("")
              if the flag is preceded by the @ sign then it becomes global and valid until changed
              flags can be delimited with comma, and here is available flags:
            - 'cls' or 'clear' - clears txt_info text
            - (@)color=hex - text color, if omitted, black color is used (color=#000000)
            - (@)background_color=hex - text color, if omitted, black color is used (color=#000000)
            - (@)size=integer - font size, if omitted, point size 8 is used (size=8)
            - (@)font_name - font name
            - new_line - True/False, if True go to new line after inserting text (type 'new_line' or just 'n')
            - cursor_freeze - True/False if True do not move cursor after inserting text (type 'cursor_freeze' or 'freeze' or just 'f')
            - cursor - Start/End move cursor to start or end of document after inserting text (type 'cursor' or just 'c')
            - move - Start/End move cursor to start or end and move document view to ensure cursor visibile
            EXAMPLE: "clear, color=#aa0000, size=14" - clear text box, use red color with font size 14
            Note, color can be also in rgb: color=rgb(190,100,200), or by name (red, green, darkblue...)
        3. ABANDONED This part is no longer used!
            string with flags for progress bar (prb_lib)
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
        for i in range(1, len(commands)):
            if commands[i][0] == "!" or commands[i][0] == "!!" or commands[i][0] == "!!!":
                char_format = self.info_char_format
                color = self.info_color
                font = self.info_font
        no_new_line = False
        cursor_freeze = False
        cursor = self.ui.txt_info.textCursor()
        for i in range(1, len(commands)):
            if commands[i][0] == "color" or commands[i][0] == "foreground color" or commands[i][0] == "foreground_color" or commands[i][0] == "fore_color" or commands[i][0] == "fc":
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setForeground(color)
            elif commands[i][0] == "@color" or commands[i][0] == "@foreground color" or commands[i][0] == "@foreground_color" or commands[i][0] == "@fore_color" or commands[i][0] == "@fc":
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setForeground(color)
                self.info_color.setNamedColor(val)
                self.info_char_format.setForeground(self.info_color)
            elif commands[i][0] == "background color" or commands[i][0] == "background" or commands[i][0] == "background_color" or commands[i][0] == "back_color" or commands[i][0] == "bc":
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setBackground(color)
            elif commands[i][0] == "@background color" or commands[i][0] == "@background" or commands[i][0] == "@background_color" or commands[i][0] == "@back_color" or commands[i][0] == "@bc":
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setBackground(color)
                self.info_color.setNamedColor(val)
                self.info_char_format.setBackground(self.info_color)
            elif commands[i][0] == "size":
                val = int(commands[i][1])
                char_format.setFontPointSize(val)
            elif commands[i][0] == "@size":
                val = int(commands[i][1])
                char_format.setFontPointSize(val)
                self.info_char_format.setFontPointSize(val)
            elif commands[i][0] == "font_name":
                val = commands[i][1]
                char_format.setFontFamily(val)
            elif commands[i][0] == "@font_name":
                val = commands[i][1]
                char_format.setFontFamily(val)
                self.info_char_format.setFontFamily(val)
            elif commands[i][0] == "bold":
                val = commands[i][1]
                if val == "1" or val=="True":
                    font.setBold(True)
                    char_format.setFontWeight(QtGui.QFont.Bold)
            elif commands[i][0] == "@bold":
                val = commands[i][1]
                if val == "1" or val=="True":
                    font.setBold(True)
                    char_format.setFontWeight(QtGui.QFont.Bold)
                    self.info_font.setBold(True)
                    self.info_char_format.setFontWeight(QtGui.QFont.Bold)
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
    
    def _parse_flag_string(self, flag_string: str) -> list:
        """Handles the flags for the 'update_progress' function.
        Args:
            flag_string (str): String that contains flags
        Returns:
            list: List of commands and values
        """
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
        """Adds a new library to the database and Tree view.
        """
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

    def resize_widgets(self, x: int = 0):
        """Resizes widgets on window resize.
        Args:
            x (int): Position for delimiter line
        """
        # Resize widgets with window
        w = self.contentsRect().width()
        h = self.contentsRect().height()
        if self.drag_mode:
            self.ui.ln_sep.move(int(x), self.ui.ln_sep.pos().y())
            self.conn.set_setting_data("main_win_delimiter_line", value_integer=self.ui.ln_sep.pos().x())
        else:
            self.ui.ln_sep.move(int(self.width()*self.scale), self.ui.ln_sep.pos().y())
        self.ui.lbl_lib.resize(w, self.ui.lbl_lib.height())
        self.ui.txt_lib.resize(w, self.ui.txt_lib.height())
        # self.ui.prb_lib.resize(self.width(), self.ui.prb_lib.height())
        self.ui.tree_lib.resize(self.ui.ln_sep.pos().x(), h-110)
        self.ui.txt_info.move(self.ui.ln_sep.pos().x(), self.ui.txt_info.pos().y())
        self.ui.txt_info.resize(w-self.ui.ln_sep.pos().x(), h-110)
        # frm_find
        self.ui.frm_find.move(self.ui.txt_info.pos().x() + self.ui.txt_info.width() - 290, self.ui.txt_info.pos().y())
        # frm_navigation
        self.ui.frm_navigation.move(w - self.ui.frm_navigation.width(), self.ui.frm_navigation.pos().y())
        # frm_net
        self.ui.frm_net.move(self.ui.ln_sep.pos().x(), self.ui.frm_net.pos().y())

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.ui.frm_find.isVisible:
            x = a0.localPos().x()
            y = a0.localPos().y()
            fx = self.ui.frm_find.pos().x()
            fy = self.ui.frm_find.pos().y()
            fx1 = fx + self.ui.frm_find.width()
            fy1 = fy + self.ui.frm_find.height()
            if x > fx and x < fx1 and y > fy and y < fy1:
                self.frm_find_click()
        x = a0.localPos().x()
        drag_point = [self.ui.ln_sep.pos().x(), self.ui.ln_sep.pos().x()+1, self.ui.ln_sep.pos().x()+2, self.ui.ln_sep.pos().x()+3]
        if a0.button() == QtCore.Qt.LeftButton and x in drag_point:
            self.drag_mode = True
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        x = a0.localPos().x()
        y = a0.localPos().y()
        if self.drag_mode and x > 99 and x < (self.width()-50):
            self.resize_widgets(x)
        return super().mouseMoveEvent(a0)
    
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == QtCore.Qt.LeftButton:
            self.drag_mode = False
            self.scale = self.ui.ln_sep.pos().x()/self.width()
        return super().mouseReleaseEvent(a0)

    def load_setting(self):
        """Loading settings. It is called at the start of the application.
        """
        style = "QTreeWidget::item:selected { background-color: green; }"
        self.ui.tree_lib.setStyleSheet(style)
        # Hide Find Frame
        self.ui.frm_find.setVisible(False)
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
        if w < 200 or h < 300:
            self.resize(1200, 750)
        else:
            self.resize(w, h)
        self.setMinimumSize(200, 300)
        # Setup delimiter line pos
        delim = self.conn.get_setting_data("main_win_delimiter_line")
        if delim < 100:
            delim = 100
        self.ui.ln_sep.move(delim, self.ui.ln_sep.pos().y())
        self.ui.ln_sep.resize(self.ui.ln_sep.width(), self.height()-110)
        # Define 'scale' - for calculating relative position of delimiter line in rezise event
        self.scale = delim / self.width()
        # Write ReadMe file in txt_info widget
        if os.path.exists("readme.txt"):
            self._show_readme_file()
        # Load Info box pages
        result = self.conn.load_info_box_pages()
        self.pages = []
        for i in result:
            self.pages.append(i[3])
        self.pages_current = len(self.pages)
        if self.pages_current < 0:
            self.pages_current = 0
        while len(self.pages) > self.pages_number:
            self.pages.pop(0)

    def _show_readme_file(self):
        """Loads the readme.txt file and displays it in the Info box.
        """
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
        """Saves settings. Called at the end of the application.
        """
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
        # Save Info box pages
        self.conn.save_info_box_pages(self.pages)


class CalculateAndSave(QThread):
    """Contains methods for object analysis processing.
    """
    update_progress = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.obj_list = []  # List of IDs for recursion
        self.list_of_processed_objects = []  # Items to be saved in database
        self.parents_list = []  # List od parents to save
        # Load connection to database
        self.conn = Database()

    def combine_names_and_analyze(self, object_id: int):
        """Calls data analysis several times with slightly modified parameters if previous attempts failed.
        Args:
            object_id (int): Object ID
        """
        object_data = self.conn.get_object_all(object_id)
        # if object_data[0][6] != 0:
        #     return
        full_name = self.conn.get_full_name(object_id, add_virtual_name=True)
        bb = full_name.split(".")
        comb = []
        fr = ""
        im = ""
        ob = ""
        for f in range(len(bb)):
            for i in range(f+1, len(bb)+1):
                fr = ".".join(bb[:f])
                im = ".".join(bb[f:i])
                ob = ".".join(bb[f:])
                comb.append([fr, im , ob])
        self._update_progress([f"BEGIN: ", "color=#5500ff, size=8"])
        count = 0
        for i in comb:
            count += 1
            if i[0] != "":
                import_line = "        " + "from " + i[0] + " import " + i[1]
            else:
                import_line = "        " + "import " + i[1]
            self.write_import_line_to_file(import_line)
            self.write_object_line_to_file(i[2])
            result = self.execute_file()
            if result != "Ok":
                self._update_progress([f"Attempt {str(count)}: ", "n=False"])
                self._update_progress([f"{result[0]}", "color=red"])
                # self._update_progress([import_line, "color=darkblue"])
                # self._update_progress([i[2], "color=darkblue"])
            else:
                self._update_progress([f"Attempt {str(count)}: ", "n=False"])
                self._update_progress(["Success !!!", "color=darkgreen"])
                json_data = self._load_json_file()
                data_to_update = self._make_data_to_append(json_data[0], object_data[0][1])
                self.conn.update_object(object_id, data_to_update)
                break
        self._update_progress([f"END.", "color=#5500ff, size=8"])

    def calculate_and_save_all_data(self, recursion: bool, command_text: str, parent: int = 0):
        """Analyzes an object and its sub-objects.
        Args:
            recursion (bool): If true, analyzes all sub-objects in depth
            command_text (str): Text entered by the user
            parent (int): The ID of the object for which sub-objects are being analyzed
        """
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
        virtual_obj = ""
        if len(txt) > 1:
            from_txt = ""
            object_txt = txt[-1:][0]
            for x in txt[:-1]: from_txt = from_txt + "." + x
            from_txt = from_txt[1:]
            virtual_obj = from_txt
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
            if virtual_obj != "":
                data_to_append.append(virtual_obj)
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
        """Saves all sub-objects from the list of parent objects to the database.
        """
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
        if len(items) == 0:
            return
        self.conn.add_object(items)
        self._update_progress(["", f"add={len(items)}"])
        return

    def _make_data_to_append(self, data_from_file, parent_id):
        """Adjusts the data format so that a new object can be added to the database.
        Args:
            data_from_file (list): Data from JSON file
            parent_id (int): Parent object ID
        Returns:
            list: Adjusted data
        """
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
        
        doc_string = data_from_file[3]
        source = data_from_file[4]
        mro = data_from_file[5]
        py_obj = data_from_file[6]
        file_name = data_from_file[7]
        module = data_from_file[8]

        data_to_append = [d_parent, d_name, d_value, d_arg, d_type_name, doc_string, source, mro, py_obj, file_name, module]
        return data_to_append

    def _load_json_file(self):
        """Loads the generated JSON file.
        """
        with open("result.txt", "r", encoding="utf-8") as a:
            data = json.load(a)
        return data

    def execute_file(self):
        """'analyze.py' is executed which analyzes the object.
        """
        try:
            import analyze
            importlib.reload(analyze)
            a = analyze.do_it()
        except Exception as e:
            txt = str(e) + "\n"
            txt = txt + str(type(e)) + "\n" + str(dir(e))
            return str(e), txt
        return "Ok"

    def write_import_line_to_file(self, import_line: str):
        """Writes an Import line to 'analyze.py'
        Args:
            import_line (str): Import line to write
        """
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


    def write_object_line_to_file(self, object_to_exam: str):
        """Writes Object line to 'analyze.py'
        Args:
            object_to_exam (str): Object line
        """
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
        self.some_int = 0  # Integer for various purposes

    def get_full_name(self, object_id, get_list_with_id_and_name=False, add_virtual_name=False):
        """The full object name is the 'path' to the object starting from the library name itself.
        Args: 
            object_id (int): The ID of the object for which the full name is requested
            get_list_with_id_and_name (bool): If true, the function returns a list instead of a string
            add_virtual_name (bool): If true, it also takes virtual parents into account
            If the user added an object that is not a library but only part of a library, that object does not have a parent object but a virtual parent object.
        Returns:
            str, list: object full name
        """
        full_name = ""
        full_name_list = []
        cur_id = object_id
        go_loop = True

        while go_loop:
            result = self.get_object_all(object_id=cur_id)
            if result[0][13] != "" and result[0][13] != None and add_virtual_name == True:
                i = result[0][13] + "." + result[0][2]
                i1 = i.split(".")
                i1 = list(reversed(i1))
                i = ".".join(i1)
                full_name = full_name + i + "."
            else:
                full_name = full_name + result[0][2] + "."
            full_name_list.append([result[0][0], result[0][2]])
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
        full_name_list = list(reversed(full_name_list))
        if get_list_with_id_and_name:
            return full_name_list
        else:
            return full_name

    def get_object_all(self, object_id: int = 0, filter: str = "", filter_exact_match: bool = False) -> list:
        """Returns a list of objects from the database.
        Args:
            object_id (int): If specified, data is filtered by that ID
            filter (str): A string to use as a filter condition
            filter_exact_match (bool): An exact match for the filter is sought, not the filter string anywhere it appears
        Returns:
            list: List of objects
            """
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

    def get_setting_data(self, function_name: str, get_text: bool = False):
        """Loads data from the settings table.
        """
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

    def set_setting_data(self, function_name: str, value_integer: int = 0, value_text: str = ""):
        """Records data in the setting table.
        """
        if self._is_setting_exists(function_name):
            q = f"UPDATE setting SET val = {str(value_integer)}, val_txt = ? WHERE function = '{function_name}' ;"
        else:
            q = f"INSERT INTO setting(function, val, val_txt) VALUES ('{function_name}', {str(value_integer)}, ?) ;"
        self.cur.execute(q, (value_text,))
        self.conn.commit()

    def _check_is_tables_exists(self):
        """Checks if the tables exist in the database and creates them if they don't exist.
        """
        q = "CREATE TABLE IF NOT EXISTS object (object_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, parent INTEGER, name TEXT, value TEXT, arguments TEXT, type TEXT (50), children INTEGER, doc_string TEXT, source TEXT, mro TEXT, py_obj TEXT, file_name TEXT, module TEXT, member_of TEXT);"
        self.cur.execute(q)
        self.conn.commit()
        q = "CREATE TABLE IF NOT EXISTS setting (setting_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, function TEXT (100) NOT NULL, val INTEGER, val_txt TEXT);"
        self.cur.execute(q)
        self.conn.commit()
    
    def _is_setting_exists(self, function_name: str) -> bool:
        """Checks if the specified setting exists in the table.
        Args:
            function_name (str): Setting name
        """    
        q = f"SELECT * FROM setting WHERE function = '{function_name}' ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) > 0:
            return True
        else:
            return False

    def update_object(self, object_id: int, data: list):
        """Updates an object in the database.
        Args:
            object_id (int): Object ID
            data (list): Data
        """
        q = f"""UPDATE object
                SET
                    value = ?,
                    arguments = ?,
                    type = '{data[4]}', 
                    doc_string = ?,
                    source = ?,
                    mro = ?,
                    py_obj = '{data[8]}',
                    file_name = ?,
                    module = ?
                WHERE 
                    object_id = {str(object_id)}
                        ;
        """
        self.cur.execute(q, (data[2], data[3], data[5], data[6], data[7], data[9], data[10]))
        self.conn.commit()

    def add_object(self, data_list: list):
        """Adds a new object to the database.
        Args:
            data_list (list): Data
        """
        if len(data_list[0]) == 11:
            for i in range(len(data_list)):
                data_list[i].append("")
        for data in data_list:
            q = f"""INSERT INTO 
                        object(
                            parent,
                            name,
                            value,
                            arguments,
                            type, 
                            children,
                            doc_string,
                            source,
                            mro,
                            py_obj,
                            file_name,
                            module,
                            member_of)
                    VALUES  (
                            {str(data[0])},
                            '{data[1]}',
                            ?,
                            ?,
                            '{data[4]}',
                            0,
                            ?,
                            ?,
                            ?,
                            '{data[8]}',
                            ?,
                            ?,
                            '{data[11]}')
                            ;
            """
            self.cur.execute(q, (data[2], data[3], data[5], data[6], data[7], data[9], data[10]))
        self.conn.commit()
        if len(data_list) == 1:
            result = self.cur.lastrowid
            return result
        else:
            return 0

    def get_objects_for_parent(self, parent_id: int) -> list:
        """Returns a list of all sub objects.
        Args:
            parent_id (int): The ID of the object for which the data is requested
        Returns:
            list: List of objects
        """
        q = f"SELECT object_id, parent, name, value, arguments, type, children, name||' - '||type||'  '||value||arguments FROM object WHERE parent = {str(parent_id)} ORDER BY name COLLATE NOCASE;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def populate_children(self):
        """Fixes errors in the 'children' field when entering new objects.
        """
        q = """UPDATE object 
                SET children = COALESCE((SELECT child_num 
                FROM (SELECT parent AS afected_parent, COUNT(object_id) AS child_num 
                      FROM object 
                      GROUP BY parent) 
                WHERE afected_parent = object_id), 0) ;"""
        self.cur.execute(q)
        self.conn.commit()

    def find_text(self, text_to_find: str, object_id: int = 0) -> list:
        """Finds the given string in the object's name, value, and arguments.
        Args:
            text_to_finsd (str): search string
            object_id (int): start object, 0=search all
        Returns:
            list: List of objects
        """
        if object_id == 0:
            result = self._find_text(text_to_find)
        else:
            self.some_list = []
            self._find_text_for_object_id(text_to_find.lower(), object_id)
            result = self.some_list
        return result

    def _find_text_for_object_id(self, txt: str, obj_id: int):
        """Finds the required string by recursively calling itself.
        Args:
            txt (str): search string
            obj_id (int): start object
        """
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

    def _find_text(self, txt: str) -> list:
        """Finds the required string in the database
        """
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

    def delete_object_and_subobjects(self, object_id: int, delete_children_only: bool = False) -> int:
        """Deletes an object from the database.
        Args:
            object_id (int): Object ID
            delete_children_only (bool): IF true, object it self will not be deleted
        Returns:
            int: the number of objects that have been deleted
        """
        self.some_list = []
        if delete_children_only:
            protected_object = object_id
        else:
            protected_object = 0
        self._delete_object_and_subobjects(object_id, protected_object)
        for i in self.some_list:
            q = f"DELETE FROM object WHERE object_id = {str(i)} ;"
            self.cur.execute(q)
        self.conn.commit()
        self.populate_children()
        return len(self.some_list)

    def _delete_object_and_subobjects(self, object_id, protected_object):
        """The function deletes objects and all their sub-objects from the database by recursively calling itself.
        """
        if object_id != protected_object:
            self.some_list.append(object_id)
        res = self.get_objects_for_parent(object_id)
        for i in res:
            if i[6] != 0:
                self._delete_object_and_subobjects(i[0], protected_object)
            else:
                self.some_list.append(i[0])
        
    def get_total_number_of_children_in_deep(self, object_id: int) -> int:
        """The function returns the total number of sub objects in the depth for the given object ID.
        """
        self.some_int = 0
        self._total_children(object_id)
        self.some_int -= 1
        return self.some_int

    def _total_children(self, object_id):
        """The function calculates the total number of sub objects in depth for a given object ID by recursively calling itself.
        """
        children = self.get_objects_for_parent(object_id)
        self.some_int += 1
        for i in children:
            if i[6] != 0:
                self._total_children(i[0])
            else:
                self.some_int += 1

    def get_objects_with_name(self, object_name: str) -> list:
        """Returns all objects that have the requested name.
        Args:
            object_name (str): object name
        Returns:
            list: List of objects that meet the criteria
        """
        q = "SELECT * FROM object WHERE name = ? ;"
        self.cur.execute(q, (object_name,))
        result = self.cur.fetchall()
        return result

    def load_info_box_pages(self) -> list:
        """Loads all Info box pages from the database.
        """
        q = "SELECT * from setting WHERE function = 'Info_box_page' ORDER BY setting_id ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result
    
    def save_info_box_pages(self, pages: list):
        """Saves all Info box pages to the database.
        """
        q = "DELETE FROM setting WHERE function = 'Info_box_page' ;"
        self.cur.execute(q)
        self.conn.commit()
        for i in pages:
            q = f"""INSERT INTO
                        setting(function, val, val_txt)
                    VALUES
                        ('Info_box_page', 0, ?)
                        ;
                    """
            self.cur.execute(q, (i,))
        self.conn.commit()


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

    def print_text(self, text_to_print: str = "`None|Ignore`", formating_flags: str = ""):
        """Prints the text in the Text Box.
        Default behavior: Prints one line of text and moves to a new line, placing the cursor at the end of the printout.
        Args:
            QtWidgets_QTextEdit_object (QTextEdit): The object in which the text is printed
            text_to_print (str)(optional): Text to be printed
            formating_flags (str)(optional): Formating flags (font, color, etc.)
            use_txt_box_writer_formating (TxtBoxPrinter)(optional): TxtBoxPrinter object from which text formatting will be downloaded
        Flags (Commands):
            "cls": ["cls", "clear"]: Clear content of text box (No value needed)
            "color": ["color", "fc", "c", "foreground", "foreground_color", "fore_color"]: Sets the foreground text color (String)
            "background": ["background", "background_color", "back_color", "bc", "background color"]: Sets the background text color (String)
            "font_size": ["font_size", "size", "fs", "font size"]: Sets font size (Integer)
            "font_name": ["font_name", "fn", "font name", "font"]: Sets font name (String)
            "font_bold": ["font_bold", "fb", "font bold", "bold"]: Sets font to bold (True/False)
            "font_underline": ["font_underline", "fu", "font underline", "underline", "font_under", "font under", "under"]: Sets font to underline (True/False)
            "new_line": ["new_line", "nl", "new_l", "n", "new line"]: Default is 'True', if 'False' cursor will not go in new line
            "Move": ["move", "position", "@move", "@position"]: Move cursor in beginning or end of text (Beginning/End)
        """
        # Make variables for text and flags
        txt = text_to_print
        self.flags = formating_flags
        # Create a dictionary of synonyms for commands and values
        comm_syn = {
            "cls": ["cls", "clear"],
            "color": ["color", "fc", "c", "foreground", "foreground_color", "fore_color", "fore"],
            "@color": ["@color", "@fc", "@c", "@foreground", "@foreground_color", "@fore_color", "@fore"],
            "background": ["background", "background_color", "back_color", "bc", "background color", "back"],
            "@background": ["@background", "@background_color", "@back_color", "@bc", "@background color", "@back"],
            "font_size": ["font_size", "size", "fs", "font size"],
            "@font_size": ["@font_size", "@size", "@fs", "@font size"],
            "font_name": ["font_name", "fn", "font name", "font"],
            "@font_name": ["@font_name", "@fn", "@font name", "@font"],
            "font_bold": ["font_bold", "fb", "font bold", "bold"],
            "@font_bold": ["@font_bold", "@fb", "@font bold", "@bold"],
            "font_underline": ["font_underline", "fu", "font underline", "underline", "font_under", "font under", "under"],
            "@font_underline": ["@font_underline", "@fu", "@font underline", "@underline", "@font_under", "@font under", "@under"],
            "new_line": ["new_line", "nl", "new_l", "n", "new line"],
            "@new_line": ["@new_line", "@nl", "@new_l", "@n", "@new line"],
            "Move": ["move", "position", "@move", "@position"]
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
                color.setNamedColor(val)
                char_format.setForeground(color)
            elif commands[i][0] in comm_syn["@color"]:
                val = commands[i][1]
                color.setNamedColor(val)
                char_format.setForeground(color)
                self.global_color.setNamedColor(val)
                self.global_text_char_format.setForeground(self.global_color)
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
        
    def _parse_flag_string(self, flags_string: str, flag_names_dict: dict) -> list:
        """Handles the flags.
        Args:
            flags_string (str): String with user flags
            flag_names_dict (dict): Valid flag commands
        Returns:
            list: List of commands, values and Errors
        """
        result = []
        flag_list = flags_string.split(",")
        for i in flag_list:
            flag_and_value = i.split("=")
            if len(flag_and_value) == 1:
                result.append([flag_and_value[0].strip().lower(), "", ""])
            elif len(flag_and_value) == 2:
                result.append([flag_and_value[0].strip().lower(), flag_and_value[1].strip(), ""])
            elif len(flag_and_value) > 2:
                result.append(["", "", "The number of assigned values ??????has been exceeded"])
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    lib_anlyzer = Analyzer()
    lib_anlyzer.start_me()
    app.exec_()

