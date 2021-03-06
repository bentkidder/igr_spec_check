import matplotlib, sys
matplotlib.use('TkAgg')

from config_spec_check import *

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import pyfits as fits
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.cm as cm
from scipy import stats

import sys
import os, fnmatch
import tkMessageBox

if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

from tkFileDialog import askdirectory, askopenfilename, asksaveasfilename

# Create a new Matplotlib toolbar that does not display live x,y coordinates
# (this caused the toolbar to move around in its tk grid cell)
class my_toolbar(NavigationToolbar2TkAgg):
    toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if
               t[0] in ('Pan', 'Zoom', 'Save')]
    def set_message(self, msg):
        pass

#This class contains
class ViewSpec(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)


        #Window Title
        self.master.wm_title('View Window')

        self.grid(row=0, column=0)
        master.columnconfigure(0, weight=0)
        master.columnconfigure(4, weight=1)
        master.rowconfigure(5, weight=1)

        #Number in list
        self.list_counter = 0

        #Check if list has been successfully loaded
        self.list_loaded = False
        self.overplot_loaded = False


        # This overrides the command to exit a tkinter window using the red exit button on mac
        # and calls a custon quit command. Without this line, the embedded matplotlib canvas
        # would cause a fatal error in python
        self.master.protocol('WM_DELETE_WINDOW', self._quit)

        #Add a custom menu bar. (Just testing this right now)
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        self.filemenu = tk.Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.save_SNR_bool = tk.BooleanVar()
        self.filemenu.add_checkbutton(label='Save SNR Data', \
          onvalue=1, offvalue=0, variable=self.save_SNR_bool)

        self.filemenu.add_command(label = 'Save Session', command = self.save_session)
        self.filemenu.add_command(label = 'Load Session', command = self.load_session)


        #Bind to mouse release to check for 'pan' and 'zoom' activity on toolbar
        self.master.bind("<ButtonRelease-1>", self.on_click)

        #Bind enter key to update wavelength range and y-axis
        self.master.bind('<Return>', self.update_wvl)

        #Use escape key to remove focus from entry widgets
        self.master.bind('<Escape>', self.esc_entry)

        #Use 'F' key as a shortcut for flagging features
        self.master.bind('<Command-f>', self.f_press)

        #Bindings for using left and right arrows for cycling through spectra
        self.master.bind('<Left>', self.left_press)
        self.master.bind('<Right>', self.right_press)

        #Function for saving png images of matplotlib canvas 
        self.master.bind('<Command-s>', self.save_img_short)

        #Command for focusing on comment box
        self.master.bind('<Command-w>', self.write_comment)

        

       	#Cretae matplotlib canvas for viewing spectra
       	self.spec_fig, self.spec_ax = plt.subplots(1, figsize = (10,4))

        self.spec_canvas = FigureCanvasTkAgg(self.spec_fig, master=self.master)
        self.spec_canvas.get_tk_widget().grid(row=7,column=0, columnspan=20, rowspan=16, \
            sticky=tk.NSEW, pady=(0,50))

       	self.spec_fig.canvas.draw()

        #Create separate frame for matplotlib toolbar
        self.toolbar_frame = tk.Frame(self.master)
        self.toolbar_frame.grid(row=23,column=5, columnspan=7, rowspan=2, sticky='NE')
        self.beam_toolbar = my_toolbar(self.spec_canvas, self.toolbar_frame)
        self.beam_toolbar.update()

        self.pan_zoom_label = tk.Label(text = '', width=4, anchor='e')
        self.pan_zoom_label.grid(row=22, column=5,sticky='SE', padx=(25,0))

       	#Working directory input
       	self.wrk_dir = tk.StringVar()
       	self.wrk_dir_entry = tk.Entry(self.master, width=40, textvariable=self.wrk_dir)
       	self.wrk_dir_entry.grid(row= 0,column=4, sticky = 'NW', columnspan=9)
        self.wrk_dir_entry.insert(0, default_working_directory)
       	tk.Label(self.master, text='Working Directory').grid(row=0, column=3, \
       		sticky='NE', padx=(80,5))

       	#Browse button for working directory
       	self.browse_wrk_dir_button = tk.Button(self.master, text='Browse', \
       		command=self.browse_wrk_dir)
       	self.browse_wrk_dir_button.grid(row=0, column=13, sticky='NW', padx=(0,80))


       	#Entry for loading target list
       	self.target_list_loc = tk.StringVar()
       	self.target_list_loc_entry = tk.Entry(self.master, width=40, \
       		textvariable=self.target_list_loc)
       	self.target_list_loc_entry.grid(row=1, column=4, sticky='NW', columnspan=9)
        self.target_list_loc_entry.insert(0, default_target_list)
       	tk.Label(self.master, text='Target List').grid(row=1, column=3, \
       		sticky='NE', padx=(80,5))


        #Check button for overplotting 
        self.overplot_on = tk.IntVar()
        self.overplot_check = tk.Checkbutton(self.master, text = 'Overplotting', \
          variable = self.overplot_on, offvalue = 0, onvalue = 1)
        self.overplot_check.grid(row = 2, column = 12, sticky='NW')


       	#Browse button for target list
       	self.browse_target_list_button = tk.Button(self.master, text='Browse', \
       		command=self.browse_target_list)
       	self.browse_target_list_button.grid(row=1, column=13, sticky='NW')

        #Load button for target list
        self.load_list_button = tk.Button(self.master, text = 'Load List', \
          command = self.load_list)
        self.load_list_button.grid(row=2, column=13, sticky = 'NW')


        #Save output button
        self.save_button = tk.Button(self.master, text = 'Save Output', \
          command = self.save_output)
        self.save_button.grid(row = 4, column = 13, sticky = 'NW', pady=(10,0))

        #Button for saving images to gallery
        self.save_img_button = tk.Button(self.master, text = 'Save Image', \
          command = self.save_img)
        self.save_img_button.grid(row=5, column = 13, sticky = 'NW')

        #Display object info 
        tk.Label(self.master, text='Object ID: ').grid(row=0, column =0, sticky = 'NE')
        self.display_obsid = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_obsid.grid(row=0, column=1, columnspan = 2, sticky='NW')

        tk.Label(self.master, text='Obs. Date: ').grid(row=1, column = 0, sticky = 'NE')
        self.display_obsdate = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_obsdate.grid(row=1,column=1, columnspan = 2, sticky = 'NW')

        tk.Label(self.master, text='RA: ').grid(row=2, column=0, sticky = 'NE')
        self.display_RA = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_RA.grid(row=2, column=1, columnspan=2, sticky='NW')

        tk.Label(self.master, text='DEC: ').grid(row=3, column=0, sticky = 'NE')
        self.display_DEC = tk.Label(self.master, text = '', width = 15, anchor='w')
        self.display_DEC.grid(row=3, column=1, columnspan=2, sticky='NW')


        #Entry for feature name
        self.feature_name = tk.StringVar()
        self.feature_entry = tk.Entry(self.master, width = 10, \
          textvariable=self.feature_name)
        self.feature_entry.grid(row=4, column=0, sticky='NE', pady=(10,0))
        self.feature_entry.insert(0, 'Feature Name')

        #Entry for comments
        self.comment = tk.StringVar()
        self.comment_entry = tk.Entry(self.master, width=23, \
          textvariable = self.comment)
        self.comment_entry.grid(row=5, column=0, sticky='NE', columnspan=2)


        #Button for flagging features
        self.flag_button = tk.Button(self.master, text='Flag', width = 10, 
          command = self.flag_feature)
        self.flag_button.grid(row = 4, column=1, sticky = 'NW', pady=(10,0))

        #Flag display
        self.flag_display = tk.Label(self.master, text='')
        self.flag_display.grid(row=4, column = 2, sticky = 'NW', pady=(10,0))

       	#Wavelength entry
       	self.lower_wvl = tk.StringVar()
       	self.lower_wvl_entry = tk.Entry(self.master, width=6, \
       		textvariable=self.lower_wvl)
       	self.lower_wvl_entry.grid(row=23, column = 0, sticky = 'NW', padx=(80,5))
        self.lower_wvl_entry.insert(0, str(default_low_wvl))

       	self.upper_wvl = tk.StringVar()
       	self.upper_wvl_entry = tk.Entry(self.master, width = 6, \
       		textvariable= self.upper_wvl)
       	self.upper_wvl_entry.grid(row = 23, column = 1, sticky = 'NW', padx=(20,0))
        self.upper_wvl_entry.insert(0, str(default_high_wvl))
       	tk.Label(self.master, text = u'Wavelength Range (\u03bcm)').grid(row=22, column=0, \
       		columnspan=2, sticky = 'SW', padx=(80,0))
        tk.Label(self.master, text='-').grid(row=23, column=1, sticky='NW')

        #Plot range entry
        self.lower_y = tk.StringVar()
        self.lower_y_entry = tk.Entry(self.master, width=6, \
          textvariable=self.lower_y)
        self.lower_y_entry.name = 'Grumpus'
        self.lower_y_entry.grid(row=23, column=2, sticky='NW', padx=(20,0))
        self.lower_y_entry.insert(0, default_low_y)

        self.upper_y = tk.StringVar()
        self.upper_y_entry = tk.Entry(self.master, width=6, \
          textvariable = self.upper_y)
        self.upper_y_entry.grid(row=23, column=3, sticky = 'NW', padx=(20,0))
        self.upper_y_entry.insert(0, default_high_y)

        tk.Label(self.master, text='-').grid(row=23, column=3, sticky='NW', padx=(5,0))

        self.set_y_on = tk.IntVar()
        self.set_y_check = tk.Checkbutton(self.master, text = 'User Y-scale', \
          variable = self.set_y_on, offvalue = 0, onvalue = 1)
        self.set_y_check.grid(row = 22, column = 2, columnspan=2, sticky='SW', padx=(40,0))

        #Label for tracking place in list
        self.list_count_label = tk.Label(text = '/')
        self.list_count_label.grid(row=22, column = 12, columnspan=2, sticky = 'S', padx=(0,30))

       	#Next Spectrum Button 
       	self.next_button = tk.Button(self.master, text = 'Next', \
       		command = self.next_spec)
       	self.next_button.grid(row = 23, column = 13, sticky = 'NE', padx=(0,80))

        #Previous Spectrum Button
        self.back_button = tk.Button(self.master, text = 'Back', \
          command = self.prev_spec)
        self.back_button.grid(row=23, column = 12, sticky = 'NE')


    #Allows user to browse for igrins 'outdata' directory 
    def browse_wrk_dir(self):
    	select_wrk_dir = askdirectory()
    	self.wrk_dir_entry.delete(0, 'end')
    	self.wrk_dir_entry.insert(0, select_wrk_dir)

    #Allows user to locate target list in .csv format
    def browse_target_list(self):
    	select_target_list = askopenfilename()
    	self.target_list_loc_entry.delete(0, 'end')
    	self.target_list_loc_entry.insert(0, select_target_list)

    #Reads in target list
    def load_list(self):
      #Initialzie plot y-axis limits
      self.ymin = np.inf
      self.ymax = -np.inf

      #This variable determines where the user is in the list
      self.list_counter = 0

      #Attempt to load list. Contains separate warnings for problems 
      #loading working directory and list
      list_load_err = False
      wrk_dir_err = False
      try:
        self.get_columns()
        self.current_list_name = self.target_list_loc_entry.get()
        self.date, self.file_no, self.obsid, self.RA, self.DEC = \
          np.loadtxt(self.current_list_name , unpack=True, \
          delimiter=',', dtype=str, usecols=self.col_tuple)

        self.file_no = self.file_no.astype(int)
      except IOError:
        tkMessageBox.showwarning(\
          'Warning', 'Could not locate specified target list.')
        list_load_err = True
      except ValueError:
        tkMessageBox.showwarning(\
          'Warning', 'Encountered problem loading list.')
        list_load_err = True

      #Check that working directory exists
      if os.path.isdir(self.wrk_dir_entry.get())==False:
        tkMessageBox.showwarning(\
          'Warning', 'Could not locate specified working directory.')
        wrk_dir_err = True

      #Proceed with plotting if there are no loading errors.
      if list_load_err==False and wrk_dir_err==False:
        self.list_len = len(self.date)
        if self.overplot_on.get():
          self.flag_button.config(state='disabled')
          self.next_button.config(state='disabled')
          self.back_button.config(state='disabled')
          self.overplot_loaded=True
          self.overplot()
        else:
          self.flag_list = np.zeros(len(self.date))
          self.SNR_list = np.zeros((len(self.date), 6))
          self.comment_list = np.zeros(len(self.date)).astype(str)
          self.comment_list.fill('')
          self.next_spec()
          self.flag_button.config(state='normal')
          self.next_button.config(state='normal')
          self.back_button.config(state='normal')
          self.list_loaded=True
          self.overplot_loaded=False

    #Keyboard shortcut for 'Back' button
    def left_press(self, event):
      self.prev_spec()

    #Keyboard shortcut for 'Next' button
    def right_press(self, event):
      self.next_spec()

    #Command to move on to next item in list
    def next_spec(self):
      if (self.list_counter > 0) and (self.list_counter<(len(self.date)-1)):
        self.comment_list[self.list_counter] = self.comment.get()
        self.comment_entry.delete(0,'end')

      self.list_counter+=1

      if self.list_counter==len(self.date):
        tkMessageBox.showwarning(\
          'Warning', 'Reached end of list.')
        self.list_counter-=1
        self.comment_list[self.list_counter] = self.comment.get()
      else:
        self.spec_fig.canvas.draw()
        self.load_spec()
        self.display_info()
        self.check_flag()
        self.comment_entry.insert(0, self.comment_list[self.list_counter])

    #Command to move to previous item in the list
    def prev_spec(self):
      if self.list_counter>1:
        self.comment_list[self.list_counter] = self.comment.get()
        self.comment_entry.delete(0,'end')
        
      self.list_counter-=1

      if self.list_counter==0:
        tkMessageBox.showwarning(\
            'Warning', 'Reached start of list.')
        self.list_counter+=1
      else:
        self.spec_fig.canvas.draw()
        self.load_spec()
        self.display_info()
        self.check_flag()
        self.comment_entry.insert(0, self.comment_list[self.list_counter])
      
    #Function for loading one spectrum at a time
    def load_spec(self):
      H_spec_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCH_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.spec_a0v.fits'
      K_spec_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCK_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.spec_a0v.fits'

      H_sn_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCH_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.sn.fits'
      K_sn_path = self.wrk_dir_entry.get() + '/' + self.date[self.list_counter] \
        + '/' + 'SDCK_' + self.date[self.list_counter] + '_' + '%04d'%self.file_no[self.list_counter] \
        + '.sn.fits'

      #Attempt to load .spec_a0v.fits reduced spectrum
      load_err = False
      try: 
        H_hdu = fits.open(H_spec_path)
        K_hdu = fits.open(K_spec_path)

        H_spec = H_hdu[0].data
        K_spec = K_hdu[0].data

        H_wvl = H_hdu[1].data
        K_wvl = K_hdu[1].data

        self.flag_button.config(state='normal')

      except IOError:
        self.spec_ax.cla()
        self.spec_ax.set_title('Spectrum not found')
        self.spec_fig.canvas.draw()
        self.flag_list[self.list_counter] = np.nan
        self.flag_button.config(state = 'disabled')
        #print 'Load spec error'
        load_err = True

      #Attempt to load signal to noise files
      snr_load_err = False
      try:
        H_sn = fits.getdata(H_sn_path)
        K_sn = fits.getdata(K_sn_path)
      except IOError:
        #print 'Load SNR error'
        snr_load_err = True

      #Proceed if there are no errors loading file
      if load_err == False:
        self.spec_ax.set_title('')
        #Determine normilization and min/max values for specified wavelength regime
        ravel_spec = np.append(np.ravel(H_spec[:,250:1950]), np.ravel(K_spec[:,100:1950]))  
        ravel_wvl = np.append(np.ravel(H_wvl[:,250:1950]), np.ravel(K_wvl[:,100:1950])) 

        wvl_range_cut = ravel_spec[np.where((ravel_wvl>=float(self.lower_wvl_entry.get())) \
          & (ravel_wvl<=float(self.upper_wvl_entry.get())))]

        norm_factor = np.nanmedian(wvl_range_cut)

        ravel_spec/=np.nanmedian(wvl_range_cut)
        wvl_range_cut/=np.nanmedian(wvl_range_cut)

        self.ymin = np.nanmin(wvl_range_cut)
        self.ymax = np.nanmax(wvl_range_cut)

        #Plot spectrum
        self.spec_ax.cla()
        for i in range(0,K_wvl.shape[0]):
          self.spec_ax.plot(K_wvl[i,100:1950], K_spec[i,100:1950]/norm_factor, \
            color = default_plot_color)

        for i in range(0,H_wvl.shape[0]):
          self.spec_ax.plot(H_wvl[i,250:1950], H_spec[i,250:1950]/norm_factor, \
            color = default_plot_color)

        #Set plot limits
        self.spec_ax.set_xlim(float(self.lower_wvl_entry.get()), float(self.upper_wvl_entry.get()))

        if self.set_y_on.get()==1:
          self.spec_ax.set_ylim(float(self.lower_y.get()), float(self.upper_y.get()))
        else:
          self.spec_ax.set_ylim(self.ymin, self.ymax)

        #Update embedded plot
        self.spec_fig.canvas.draw()

        #Get SNR file values (mean, median, mode)
        if snr_load_err==False:
          #Averages for H band SNR
          H_sn = np.sort(H_sn, axis=None)

          H_sn = np.delete(H_sn, np.where(np.isnan(H_sn)==True))
          H_sn = np.delete(H_sn, np.where(H_sn<0))
          H_sn = np.around(H_sn[int(0.1*len(H_sn)):-1], decimals=0)

          H_mean = np.around(np.mean(H_sn), decimals=0)
          H_median = np.median(H_sn)
          H_mode = stats.mode(np.around(H_sn, decimals=-1), axis=None)
          #H_mode = stats.mode(H_sn, axis=None)

          #Averages for K band SNR
          K_sn = np.sort(K_sn, axis=None)

          K_sn = np.delete(K_sn, np.where(np.isnan(K_sn)==True))
          K_sn = np.delete(K_sn, np.where(K_sn<0))
          K_sn = np.around(K_sn[int(0.1*len(K_sn)):-1], decimals=0)

          K_mean = np.around(np.mean(K_sn), decimals=0)
          K_median = np.median(K_sn)
          K_mode = stats.mode(np.around(K_sn, decimals=-1), axis=None)
          #K_mode = stats.mode(K_sn, axis=None)


          #Store average data in array
          #print self.SNR_list.shape
          #print self.flag_list.shape
          self.SNR_list[self.list_counter, :] = \
            np.array([H_mean, K_mean, H_median, K_median, H_mode[0], K_mode[0]])


    #This function is similar to loadspec, but overplots all spectra in the list
    #rather than one at a time. 
    def overplot(self):
      self.clear_info()
      self.spec_ax.cla()

      cmap_inc = 0.9/(self.list_len-2)
      use_cmap = cm.get_cmap(default_overplot_cmap)

      self.ymin = np.inf
      self.ymax = -np.inf
      for i in range(1,self.list_len):

        #Get paths for H and K spectrum files
        H_spec_path = self.wrk_dir_entry.get() + '/' + self.date[i] \
          + '/' + 'SDCH_' + self.date[i] + '_' + '%04d'%self.file_no[i] \
          + '.spec_a0v.fits'
        K_spec_path = self.wrk_dir_entry.get() + '/' + self.date[i] \
          + '/' + 'SDCK_' + self.date[i] + '_' + '%04d'%self.file_no[i] \
          + '.spec_a0v.fits'

        #Attempt to load .spec_a0v.fits reduced spectrum
        load_err = False
        try: 
          H_hdu = fits.open(H_spec_path)
          K_hdu = fits.open(K_spec_path)

          H_spec = H_hdu[0].data
          K_spec = K_hdu[0].data

          H_wvl = H_hdu[1].data
          K_wvl = K_hdu[1].data

        except IOError:
          #print 'Load spec error'
          load_err = True

        #Proceed if there are no errors loading file
        if load_err == False:
          #Determine normilization and min/max values for specified wavelength regime
          ravel_spec = np.append(np.ravel(H_spec[:,250:1950]), np.ravel(K_spec[:,100:1950]))  
          ravel_wvl = np.append(np.ravel(H_wvl[:,250:1950]), np.ravel(K_wvl[:,100:1950])) 

          wvl_range_cut = ravel_spec[np.where((ravel_wvl>=float(self.lower_wvl_entry.get())) \
            & (ravel_wvl<=float(self.upper_wvl_entry.get())))]

          norm_factor = np.nanmedian(wvl_range_cut)

          ravel_spec/=np.nanmedian(wvl_range_cut)
          wvl_range_cut/=np.nanmedian(wvl_range_cut)


          if np.nanmax(wvl_range_cut)>self.ymax:
            self.ymax = np.nanmax(wvl_range_cut)
          if np.nanmin(wvl_range_cut)<self.ymin:
            self.ymin = np.nanmin(wvl_range_cut)


          current_color = use_cmap(cmap_inc*(i-1), 1.)

          #Determine label to use for plot legend
          if legend_id == 'date':
            current_label = self.date[i]
          elif legend_id == 'obsid':
            current_label = self.obsid[i]
          elif legend_id == 'nolegend':
            current_label = None

          #Plot spectrum
          for j in range(0,K_wvl.shape[0]):
            self.spec_ax.plot(K_wvl[j,100:1950], K_spec[j,100:1950]/norm_factor, \
              color = current_color, label = current_label)
            current_label = None

          for j in range(0,H_wvl.shape[0]):
            self.spec_ax.plot(H_wvl[j,250:1950], H_spec[j,250:1950]/norm_factor, \
              color = current_color)

          #Set plot limits
          self.spec_ax.set_xlim(float(self.lower_wvl_entry.get()), float(self.upper_wvl_entry.get()))
          self.spec_ax.set_ylim(self.ymin, self.ymax)

          #Update figure legend
          self.spec_ax.legend()

          #Update embedded plot
          self.spec_fig.canvas.draw()

    #Function used to alter object info labels for current object
    def display_info(self):
      self.display_obsid.configure(text=self.obsid[self.list_counter])
      self.display_obsdate.configure(text=self.date[self.list_counter])
      self.display_RA.configure(text=self.RA[self.list_counter])
      self.display_DEC.configure(text=self.DEC[self.list_counter])
      self.list_count_label.configure(text = \
        str(self.list_counter) + '/' + str(len(self.date)-1))

    #function to clear object info labels
    def clear_info(self):
      self.display_obsid.configure(text='')
      self.display_obsdate.configure(text='')
      self.display_RA.configure(text='')
      self.display_DEC.configure(text='')

    #Function that calls the 'flag_feature' function when the 'f'
    #key is pressed
    def f_press(self, event):
      if self.flag_button['state'] == 'normal':
        self.flag_feature()
      else:
        pass

    #Flags or unflags an object when the 'Flag/Unflag' button
    #is pressed
    def flag_feature(self):
      if self.list_loaded:
        if self.flag_list[self.list_counter]==0:
          self.flag_button.config(text='Unflag')
          self.flag_display.config(text=u'\u2691')
          self.flag_list[self.list_counter]=1
        else:
          self.flag_button.config(text='Flag')
          self.flag_display.config(text='')
          self.flag_list[self.list_counter]=0
      else:
        tkMessageBox.showwarning(\
          'Warning', 'No list loaded.')

    #Checks the flag status of an object when the 
    #'Back' and 'Next' buttons are pressed
    def check_flag(self):
      if self.flag_list[self.list_counter]==1:
          self.flag_button.config(text='Unflag')
          self.flag_display.config(text=u'\u2691')
      else:
          self.flag_button.config(text='Flag')
          self.flag_display.config(text='')


    #Locates columns based on column titles contained in the 
    #first row of an input list
    def get_columns(self):
      temp_list = np.loadtxt(self.target_list_loc_entry.get(), unpack=False, delimiter=',', dtype=str)
      col_names = temp_list[0,:]

      for i in range(0,len(col_names)):
        col = col_names[i].upper().strip()

        if col=='CIVIL':
          self.date_col = i
        elif col=='FILENUMBER':
          self.fileno_col = i
        elif col == 'OBJNAME':
          self.obsid_col = i
        elif col == 'RA':
          self.RA_col = i
        elif col == 'DEC':
          self.DEC_col = i

      self.col_tuple = (self.date_col, self.fileno_col, self.obsid_col, self.RA_col, self.DEC_col)

    #Function for saving the flag data for a given list
    def save_output(self):
      if self.overplot_loaded==True:
        tkMessageBox.showwarning('Warning', 'Flagging spectra disabled in overplotting mode.')
      elif not self.list_loaded:
        tkMessageBox.showwarning('Warning', 'No list loaded.')
      elif self.feature_name.get() == 'Feature Name' or self.feature_name.get() == '':
        tkMessageBox.showwarning('Warning', 'Enter valid feature name before saving.')
        self.feature_entry.focus_set()

      else:
        self.comment_list[self.list_counter]=self.comment.get()
        save_list = np.loadtxt(self.target_list_loc_entry.get(), unpack=False, delimiter=',', dtype=str)

        save_flag_list = np.copy(self.flag_list)
        save_flag_list = save_flag_list.astype(str)
        save_flag_list[0]=self.feature_name.get()

        #print save_list.shape, save_flag_list.shape
        save_list = np.column_stack((save_list,save_flag_list))

        if not all(self.comment_list==''):
          self.comment_list[0] = self.feature_name.get() + ' Comments'
          save_list = np.column_stack((save_list, self.comment_list))

        #Check if user wants to save the SNR data as well as the flag list
        if self.save_SNR_bool.get()==True:
          save_SNR_list = np.copy(self.SNR_list).astype(str)
          save_SNR_list[0, :] = \
            np.array(['H Mean', 'K Mean', 'H Median', 'K Median', 'H Mode', 'K Mode'])
          save_list = np.column_stack((save_list, save_SNR_list))


        save_name = self.target_list_loc_entry.get().replace('.csv', '_' + \
          self.feature_name.get() + '_flagged_ouput.csv')

        np.savetxt(save_name, save_list.astype(str), delimiter=',', fmt='%s')

        tkMessageBox.showinfo('Save Info', 'Output saved successfully.')

    #Call save_img from keyboard (command+s)
    def save_img_short(self, event):
      self.save_img()

    #Function for saving png versions of matplotlib plots
    def save_img(self):
      feature = self.feature_entry.get()
      if feature=='' or feature=='Feature Name':
        tkMessageBox.showwarning('Warning', \
          'Please enter a valid feature name before saving an image.')
        return
      elif not (self.list_loaded or self.overplot_loaded):
        tkMessageBox.showwarning('Warning', \
          'No list loaded.')
        return

      list_name = self.current_list_name.split('/')[-1]
      list_name = list_name.replace('.csv', '_')

      if self.overplot_loaded:
        save_folder = 'img_gallery'
        save_name = save_folder + '/' + list_name + feature + '_overplot.png'
        
        try: 
          self.spec_fig.savefig(save_name, dpi=120)
        except IOError:
          tkMessageBox.showwarning('Warning', 'Save path for images not found.')
          return

        tkMessageBox.showinfo('Save Info', 'Image saved successfully.')

      elif self.list_loaded:
        save_folder = 'img_gallery/' + list_name + feature 
        save_name = str(self.list_counter) + '_' + \
          self.obsid[self.list_counter] + '_' + self.date[self.list_counter]

        if not os.path.isdir(save_folder):
          os.makedirs(save_folder)

        self.spec_fig.savefig(save_folder + '/' + save_name )
        tkMessageBox.showinfo('Save Info', 'Image saved successfully.')




    #Update wavelength range and y-axis when Enter key is pressed
    def update_wvl(self, event):
      self.master.focus()
      self.spec_ax.set_xlim(float(self.lower_wvl.get()), float(self.upper_wvl.get()))
      #print event.widget, self.master.focus_get()

      if self.set_y_on.get()==1:
        try:
          self.spec_ax.set_ylim(float(self.lower_y.get()), float(self.upper_y.get()))
        except ValueError:
          tkMessageBox.showwarning(\
          'Sorry, Greg', 'Invalid y-axis limit entry.')
          
      self.spec_fig.canvas.draw()

    #Escape key removes focus from entry widgets
    def esc_entry(self, event):
      self.master.focus()

    #Save current session
    def save_session(self):
      if self.list_loaded==False:
        tkMessageBox.showwarning(\
          'Warning', 'Cannot save session with no target list loaded.')
        return
      elif self.overplot_on.get()==True:
        tkMessageBox.showwarning(\
          'Warning', 'Cannot save session in overplot mode.')
        return

      self.comment_list[self.list_counter]=self.comment.get()

      cwd = os.getcwd()
      save_file = asksaveasfilename(initialdir= (cwd + '/saved_sessions'))

      np.savez(save_file + '.npz', date = self.date, file_no = self.file_no, 
        obsid = self.obsid, RA = self.RA, DEC = self.DEC, flag_list = self.flag_list, \
        SNR_list = self.SNR_list, list_counter = self.list_counter, comments = self.comment_list)

    #Load a previously saved session
    def load_session(self):

      if self.overplot_on.get()==True:
        tkMessageBox.showwarning(\
          'Warning', 'Cannot load sessions in overplot mode.')
        return

      cwd = os.getcwd()
      open_session = askopenfilename(initialdir= (cwd + '/saved_sessions'))

      if not os.path.exists(self.wrk_dir.get()):
        tkMessageBox.showwarning('Warning', \
          'Working directory not found. Loading a previous session still requires the valid \
          working directory to be entered in the proper field. Please check that this field has \
          been correctly filled out.')
        return

      test_load = np.load(open_session)

      try:
        load_npz = np.load(open_session)

        self.date = load_npz['date']
        self.file_no = load_npz['file_no']
        self.obsid = load_npz['obsid']
        self.RA = load_npz['RA']
        self.DEC = load_npz['DEC']
        self.flag_list = load_npz['flag_list']
        self.SNR_list = load_npz['SNR_list']
        self.list_counter = load_npz['list_counter'] - 1
        self.comment_list = load_npz['comments']

      except IOError:
        tkMessageBox.showwarning(\
          'Warning', 'There was a problem loading this session. Please ensure that you selected \
          the correct directory and that none of the saved .npy files were deleted.')
        return

      self.next_spec()
      self.flag_button.config(state='normal')
      self.next_button.config(state='normal')
      self.back_button.config(state='normal')
      self.list_loaded=True
      self.overplot_loaded=False



    #Check if pan/zoom are on when mouse is released
    def on_click(self, event):
      if self.spec_fig.canvas.toolbar._active=='ZOOM':
        self.pan_zoom_label.config(text='Zoom')
      elif self.spec_fig.canvas.toolbar._active=='PAN':
        self.pan_zoom_label.config(text='Pan')
      else:
        self.pan_zoom_label.config(text='')

    #Focus on comment widget using keyboard (command+w)
    def write_comment(self, event):
      self.comment_entry.focus_set()

    #Kill program when exit button is pressed
    def _quit(self):
    	self.master.quit()
      #self.master.destroy()



if __name__ == '__main__':
  root = tk.Tk()
  root.lift()
  root.attributes('-topmost',True)
  root.after_idle(root.attributes,'-topmost',False)
  main = ViewSpec(root)
  root.mainloop()