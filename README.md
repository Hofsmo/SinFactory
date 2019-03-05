# SinFactory
This is a collection of Python classes and methods for running PowerFactory using Python. It has been developed at SINTEF with inspiration from the book Advanced Smart Grid Functionality Based on PowerFactory.

## Include PowerFactory in pythonpath
To be able to use SinFactory one needs to tell Python where to find PowerFactory. On easy way of doing this is to create a file named pf.pth in the site-packages folder of the Python interpreter one is using. For instance I am using Python 3.7 and I put the file pf.pth in the following folder C:\Users\sigurdj\AppData\Local\Programs\Python\Python37\Lib\site-packages . The file contains the following line C:\Program Files\DIgSILENT\PowerFactory 2019\Python\3.7 .
It should be noted that both the Python installation location and the PowerFactory install location may vary.
