igr_spec_check Code
===================

Requirements
------------
This code has only been tested in python 2.7. All requirements come standard with Anaconda except for **pyfits**. Note that this code is meant to be used with spectra reduced with the igrins-plp package, and directories must contain the relevant .spec_aov.fits files in order for spectra to be loaded into the program. 

This code requires the following python packages:

-matplotlib
-numpy
-**pyfits**
-tkinter


Running spec_check
-------------------
This code is run out of the directory. Simply download the project and cd into the igr_spec_check directory. If all necessary python packages are installed you should be able to simply run 

.. code:: bash

    python spec_check.py

from this directory and the speck_check GUI should pop up. If the GUI does not appear at all, it likely means that a necessary package is not installed or up to date. 

The main purpose of this software is to provide an easy way to browse through spectra and flag objects that contain a specific spectral feature. I have included a sample target list that can be loaded into the program. To ensure that everything is working properly (for igrins team members) plug in your reduced data hard drive and use the browse button next to the 'Working Directory' entry bar to locate and select the 'outdata' directory on the hard drive. The sample_list.csv file should already be entered in the 'Target List' entry bar. 

Now click the **Load List** button. A spectra should appear on the embedded plot. You can use the **Next** and **Back** to cycle through the 4 spectra on the sample list. In order to flag the current spectrum, press the **Flag** button below the object info in the top left corner. In order to save the output, enter the name of your feature of interest in the box next to the **Flag/Unflag** button. Then press **Save Output**. This will save a .csv file identical to the input, but with an added column that contains the flags. 

This software is also capable of overplotting all spectra in a given list. To overplot the sample list check the **Overplot** check-box and press **Load List**. The embedded plot should now be populated with 4 spectra. 

The default plot colors, wavelengths, working directory, and target list can all be set by editing the 'config_spec_check.py' file. 

The software looks for the object id, observation date, and file number based on the column titles, so your list must contain the correct column titles, but the columns do not need to be in the same order as the sample list. 


