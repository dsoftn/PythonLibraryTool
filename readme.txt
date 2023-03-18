### Python Library Analyzer

#  Unlock the power of Python libraries with Library Analyzer - your ultimate guide to efficient coding.

## Welcome to our Python library information tool!

The goal of this application is to help beginners as well as more experienced Python users navigate the vast number of available Python libraries. The "Library Analyzer" provides valuable information about all the methods contained within a specific library.

If you want to dive deeper into a library, the application can search for online documentation on your behalf. Alternatively, if you just need some basic functionality and a picture is worth a thousand words, with just a few clicks, you can access Python code examples that use the library or a specific method.

We hope that this application will be useful to you and help you improve your knowledge of Python and its libraries.

## How to begin:

 # (1.) Enter the name of the library you want to examine and hit Return.
Example:
#  	datetime
or
#  	sys
or
#  	matplotlib
You can also choose a certain part of the library.
Example:
#  	datetime.datetime
or
#  	matplotlib.pie
and you can also write:
#  	from datetime import datetime
or
#  	from PyQt5.QtCore import QThread

 # (2.) Press Enter and wait for data to be calculated.

 # (3.) Review the data.
The data is now recorded in the database and can be accessed quickly.

## Search:

 # To search for a specific object, simply type the object name in the search box and hit "Return"
It's important to note that our database only includes information on the direct sub-objects of the selected Python library, as well as any additional data that has been loaded as you navigate through the tree view. This means that if you haven't analyzed a particular component, it won't be included in the database. To ensure that all data is available for search, you can select "Analyze all sub-objects" in the tree view context menu.


 # The search results are displayed in the Info Box, click on one of the results to see it in the tree view
When you click on a search result, a 'Find' button will appear, which will take you directly to that object in the Tree View.

## Tree view context menu:

 # Delete object and all sub objects
Deletes the selected object and all its sub-objects.

 # Analyze all sub objects !
This option will analyze the selected object and all its sub-objects in depth. This is useful when you want to process and save all the information from the objects and a library to the database, that way every search of the database will give complete information. This is a one-time process and can be time-consuming for large libraries.

 # Search in this object
Searches only within the selected object and all its sub-objects. This is useful when you have a large number of analyzed libraries, so the search results of all libraries can sometimes be overwhelming.

## OnLine search:
Finds documentation and code examples for the selected object.
Depending on how much documentation and code examples are available online for the currently selected object, the search results can vary quite a bit in their accuracy.

 # Documentation:
Tries to find online documentation for the currently selected object.

 # Code Example:
Tries to find examples of Python code that use the currently selected object.


## Note:
Press CTRL+Return to view this document.
Press ESC to clear this box.
Press Up/Down Arrow in search box to loop through past queries.
Click on a search result to find it in the tree view.

 # ________________________
#  Author: DsoftN, March 2023.

